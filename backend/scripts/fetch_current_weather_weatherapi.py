import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection


load_dotenv()

WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")

if not WEATHERAPI_KEY:
    raise ValueError("Missing WEATHERAPI_KEY in .env file")


API_URL = "https://api.weatherapi.com/v1/current.json"
REQUEST_DELAY_SECONDS = 0.5


def get_weather_stations(connection):
    return connection.execute("""
        SELECT id, name, province, latitude, longitude
        FROM weather_station
        ORDER BY id
    """).fetchall()


def fetch_current_weather(latitude, longitude):
    params = {
        "key": WEATHERAPI_KEY,
        "q": f"{latitude},{longitude}",
        "aqi": "no",
    }

    response = requests.get(API_URL, params=params, timeout=20)

    if response.status_code != 200:
        print("WeatherAPI error:", response.status_code)
        print(response.text)
        raise RuntimeError("WeatherAPI request failed")

    return response.json()


def save_current_weather(connection, weather_station_id, data):
    current = data["current"]

    wind_kph = current.get("wind_kph")
    wind_mps = wind_kph / 3.6 if wind_kph is not None else None

    condition = current.get("condition") or {}
    fetched_at = datetime.now(timezone.utc).isoformat()

    connection.execute("""
        INSERT INTO weather_current_observation (
            weather_station_id,
            observation_time,
            last_updated,
            fetched_at,
            temp_c,
            wind_kph,
            wind_mps,
            precip_mm,
            humidity,
            pressure_mb,
            condition_text,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        weather_station_id,
        current.get("last_updated"),
        current.get("last_updated"),
        fetched_at,
        current.get("temp_c"),
        wind_kph,
        wind_mps,
        current.get("precip_mm"),
        current.get("humidity"),
        current.get("pressure_mb"),
        condition.get("text"),
        "WeatherAPI",
    ))


def main():
    connection = get_connection()

    weather_stations = get_weather_stations(connection)
    print("Weather stations:", len(weather_stations))

    for index, station in enumerate(weather_stations, start=1):
        print(
            f"[{index}/{len(weather_stations)}]",
            station["id"],
            station["name"],
        )

        try:
            data = fetch_current_weather(
                station["latitude"],
                station["longitude"],
            )

            save_current_weather(connection, station["id"], data)
            connection.commit()

        except Exception as error:
            print("Failed:", station["id"], error)

        time.sleep(REQUEST_DELAY_SECONDS)

    connection.close()
    print("Current weather history updated.")


if __name__ == "__main__":
    main()