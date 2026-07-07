import os
import sys
import math
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from backend.database.db_connection import get_connection

load_dotenv()

WINDY_API_KEY = os.getenv("WINDY_POINT_FORECAST_KEY")

WINDY_URL = "https://api.windy.com/api/point-forecast/v2"

REQUEST_DELAY_SECONDS = 0.5
MAX_CONSECUTIVE_FAILURES = 5
REQUEST_TIMEOUT_SECONDS = 30


class PermanentWeatherApiError(RuntimeError):
    pass


class TemporaryWeatherApiError(RuntimeError):
    pass


def fetch_weather_from_windy(latitude, longitude):
    if not WINDY_API_KEY:
        raise PermanentWeatherApiError("Missing WINDY_POINT_FORECAST_KEY in .env file.")

    payload = {
        "lat": latitude,
        "lon": longitude,
        "model": "gfs",
        "parameters": ["precip", "temp", "wind"],
        "levels": ["surface"],
        "key": WINDY_API_KEY,
    }

    try:
        response = requests.post(
            WINDY_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise TemporaryWeatherApiError(f"Windy request timed out: {error}") from error
    except requests.ConnectionError as error:
        raise TemporaryWeatherApiError(f"Windy connection error: {error}") from error
    except requests.RequestException as error:
        raise TemporaryWeatherApiError(f"Windy request failed: {error}") from error

    if response.status_code in (401, 403):
        raise PermanentWeatherApiError(
            f"Invalid or unauthorized Windy API key. HTTP {response.status_code}: {response.text}"
        )

    if response.status_code == 400:
        raise PermanentWeatherApiError(
            f"Invalid Windy API request. HTTP 400: {response.text}"
        )

    if response.status_code == 429:
        raise TemporaryWeatherApiError(
            f"Windy API rate limit reached. HTTP 429: {response.text}"
        )

    if response.status_code >= 500:
        raise TemporaryWeatherApiError(
            f"Windy server error. HTTP {response.status_code}: {response.text}"
        )

    if response.status_code != 200:
        raise TemporaryWeatherApiError(
            f"Unexpected Windy API error. HTTP {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except ValueError as error:
        raise TemporaryWeatherApiError("Windy returned invalid JSON.") from error

    if data.get("error") is True:
        message = data.get("message") or data.get("reason") or str(data)

        if "key" in message.lower() or "unauthorized" in message.lower():
            raise PermanentWeatherApiError(f"Windy API authentication error: {message}")

        raise TemporaryWeatherApiError(f"Windy API returned error: {message}")

    if "ts" not in data:
        raise TemporaryWeatherApiError("Windy response missing forecast timestamps.")

    return data


def safe_get(data, key, index):
    values = data.get(key)

    if values is None:
        return None

    if index >= len(values):
        return None

    return values[index]


def kelvin_to_celsius(value):
    if value is None:
        return None

    return value - 273.15


def calculate_wind_speed_mps(wind_u, wind_v):
    if wind_u is None or wind_v is None:
        return None

    return math.sqrt(wind_u ** 2 + wind_v ** 2)


def parse_weather_rows(raw_data, station):
    timestamps = raw_data.get("ts", [])

    if not timestamps:
        raise TemporaryWeatherApiError("Windy response contains no forecast timestamps.")

    vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    rows = []

    for i, ts in enumerate(timestamps):
        forecast_time_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        forecast_time_vn = forecast_time_utc.astimezone(vietnam_tz)

        precip_raw = safe_get(raw_data, "past3hprecip-surface", i)
        temp_raw = safe_get(raw_data, "temp-surface", i)
        wind_u = safe_get(raw_data, "wind_u-surface", i)
        wind_v = safe_get(raw_data, "wind_v-surface", i)

        precip_3h_mm = None
        if precip_raw is not None:
            precip_3h_mm = precip_raw * 1000

        temperature_c = kelvin_to_celsius(temp_raw)
        wind_speed = calculate_wind_speed_mps(wind_u, wind_v)

        rows.append(
            (
                station["id"],
                forecast_time_utc.isoformat(),
                forecast_time_vn.isoformat(),
                round(temperature_c, 2) if temperature_c is not None else None,
                round(wind_speed, 2) if wind_speed is not None else None,
                round(precip_3h_mm, 2) if precip_3h_mm is not None else None,
            )
        )

    return rows


def clear_old_forecast_data(connection):
    connection.execute("DELETE FROM telecom_flood_risk_forecast")
    connection.execute("DELETE FROM telecom_weather_station_mapping")
    connection.execute("DELETE FROM weather_forecast")
    connection.commit()


def insert_weather_rows(connection, rows):
    connection.executemany(
        """
        INSERT INTO weather_forecast (
            weather_station_id,
            forecast_time_utc,
            forecast_time_vn,
            temperature_c,
            wind_speed_mps,
            precip_3h_mm
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def get_weather_stations(connection):
    return connection.execute(
        """
        SELECT id, name, province, latitude, longitude
        FROM weather_station
        ORDER BY id
        """
    ).fetchall()


def update_weather_forecasts():
    connection = get_connection()

    print("Clearing old forecast, mapping, and flood-risk data...")
    clear_old_forecast_data(connection)

    weather_stations = get_weather_stations(connection)

    if not weather_stations:
        connection.close()
        raise PermanentWeatherApiError("No weather stations found in database.")

    total_rows = 0
    failed = []
    consecutive_failures = 0

    print("Weather stations:", len(weather_stations))

    for index, station in enumerate(weather_stations, start=1):
        station_id = station["id"]
        station_name = station["name"]

        try:
            print(f"[{index}/{len(weather_stations)}] Fetching {station_id} {station_name}")

            raw_data = fetch_weather_from_windy(
                station["latitude"],
                station["longitude"],
            )

            rows = parse_weather_rows(raw_data, station)
            insert_weather_rows(connection, rows)
            connection.commit()

            total_rows += len(rows)
            consecutive_failures = 0

            print(f"[{index}/{len(weather_stations)}] OK {station_id}: inserted {len(rows)} rows")

        except PermanentWeatherApiError:
            connection.rollback()
            connection.close()
            raise

        except TemporaryWeatherApiError as error:
            connection.rollback()
            consecutive_failures += 1

            failed.append(
                {
                    "station_id": station_id,
                    "station_name": station_name,
                    "error": str(error),
                }
            )

            print(
                f"[{index}/{len(weather_stations)}] FAILED {station_id}: {error}"
            )
            print(
                f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}"
            )

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                connection.close()
                raise TemporaryWeatherApiError(
                    f"Windy API failed {MAX_CONSECUTIVE_FAILURES} consecutive times. "
                    "Aborting update to avoid unnecessary API calls."
                )

        except Exception as error:
            connection.rollback()
            consecutive_failures += 1

            failed.append(
                {
                    "station_id": station_id,
                    "station_name": station_name,
                    "error": str(error),
                }
            )

            print(
                f"[{index}/{len(weather_stations)}] UNEXPECTED FAILURE {station_id}: {error}"
            )
            print(
                f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}"
            )

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                connection.close()
                raise RuntimeError(
                    f"Unexpected errors occurred {MAX_CONSECUTIVE_FAILURES} consecutive times. "
                    "Aborting update."
                )

        time.sleep(REQUEST_DELAY_SECONDS)

    connection.close()

    return {
        "success": True,
        "weather_stations": len(weather_stations),
        "forecast_rows_inserted": total_rows,
        "failed_count": len(failed),
        "failed": failed,
    }