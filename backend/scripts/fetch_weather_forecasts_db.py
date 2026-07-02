import os
import sys
import math
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection

load_dotenv()

WINDY_API_KEY = os.getenv("WINDY_POINT_FORECAST_KEY")

if not WINDY_API_KEY:
    raise ValueError("Missing WINDY_POINT_FORECAST_KEY in .env file")

WINDY_URL = "https://api.windy.com/api/point-forecast/v2"
REQUEST_DELAY_SECONDS = 0.5


def get_weather_stations(connection):
    return connection.execute("""
        SELECT id, name, province, latitude, longitude
        FROM weather_station
        ORDER BY id
    """).fetchall()


def fetch_weather_from_windy(latitude, longitude):
    payload = {
        "lat": latitude,
        "lon": longitude,
        "model": "gfs",
        "parameters": ["precip", "temp", "wind"],
        "levels": ["surface"],
        "key": WINDY_API_KEY,
    }

    response = requests.post(WINDY_URL, json=payload, timeout=30)

    if response.status_code != 200:
        print("Windy API error:", response.status_code)
        print(response.text)
        raise RuntimeError("Windy API request failed")

    return response.json()


def safe_get(data, key, index):
    values = data.get(key)
    if values is None or index >= len(values):
        return None
    return values[index]


def kelvin_to_celsius(value):
    if value is None:
        return None
    return value - 273.15


def wind_speed_mps(wind_u, wind_v):
    if wind_u is None or wind_v is None:
        return None
    return math.sqrt(wind_u ** 2 + wind_v ** 2)


def parse_weather_rows(raw_data, station):
    timestamps = raw_data.get("ts", [])
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
        wind = wind_speed_mps(wind_u, wind_v)

        rows.append({
            "weather_station_id": station["id"],
            "forecast_time_utc": forecast_time_utc.isoformat(),
            "forecast_time_vn": forecast_time_vn.isoformat(),
            "temperature_c": round(temperature_c, 2) if temperature_c is not None else None,
            "wind_speed_mps": round(wind, 2) if wind is not None else None,
            "precip_3h_mm": round(precip_3h_mm, 2) if precip_3h_mm is not None else None,
        })

    return rows


def clear_old_forecasts(connection):
    connection.execute("DELETE FROM telecom_flood_risk_forecast")
    connection.execute("DELETE FROM telecom_weather_station_mapping")
    connection.execute("DELETE FROM weather_forecast")


def insert_weather_rows(connection, rows):
    connection.executemany("""
        INSERT INTO weather_forecast (
            weather_station_id,
            forecast_time_utc,
            forecast_time_vn,
            temperature_c,
            wind_speed_mps,
            precip_3h_mm
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (
            row["weather_station_id"],
            row["forecast_time_utc"],
            row["forecast_time_vn"],
            row["temperature_c"],
            row["wind_speed_mps"],
            row["precip_3h_mm"],
        )
        for row in rows
    ])


def main():
    connection = get_connection()

    print("Clearing old forecast and flood-risk data...")
    clear_old_forecasts(connection)
    connection.commit()

    weather_stations = get_weather_stations(connection)

    print("Weather stations:", len(weather_stations))

    total_rows = 0

    for index, station in enumerate(weather_stations, start=1):
        print(f"[{index}/{len(weather_stations)}] Fetching:", station["id"], station["name"])

        try:
            raw_data = fetch_weather_from_windy(
                station["latitude"],
                station["longitude"],
            )

            rows = parse_weather_rows(raw_data, station)
            insert_weather_rows(connection, rows)
            connection.commit()

            total_rows += len(rows)
            print("Inserted forecast rows:", len(rows))

        except Exception as error:
            print("Failed:", station["id"], error)

        time.sleep(REQUEST_DELAY_SECONDS)

    connection.close()

    print()
    print("Done.")
    print("Total forecast rows inserted:", total_rows)


if __name__ == "__main__":
    main()