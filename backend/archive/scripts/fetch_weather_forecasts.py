"""
Fetch weather forecast data from Windy Point Forecast API.

This script:
1. Loads weather stations / forecast points from data/weather_stations.csv.
2. Fetches precipitation, temperature, and wind from Windy.
3. Saves one CSV file per weather station.

Important:
- This file does NOT calculate flood risk.
- Flood risk is calculated later for telecom stations because each telecom station
  has its own elevation and rainfall thresholds.
"""

import os
import csv
import math
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from backend.archive.scripts.weather_station_loader import load_weather_stations_from_csv


# ============================================================
# File paths
# ============================================================

WEATHER_STATION_CSV = "data/weather_stations.csv"
OUTPUT_DIR = "weather_forecast_outputs"


# ============================================================
# Load Windy API key
# ============================================================

load_dotenv()

WINDY_API_KEY = os.getenv("WINDY_POINT_FORECAST_KEY")

if not WINDY_API_KEY:
    raise ValueError("Missing WINDY_POINT_FORECAST_KEY in .env file")


# ============================================================
# Fetch weather data from Windy
# ============================================================

def fetch_weather_from_windy(latitude, longitude):
    """
    Calls Windy Point Forecast API.

    Requested parameters:
        precip
        temp
        wind

    Windy response keys:
        past3hprecip-surface
        temp-surface
        wind_u-surface
        wind_v-surface
    """

    url = "https://api.windy.com/api/point-forecast/v2"

    payload = {
        "lat": latitude,
        "lon": longitude,
        "model": "gfs",
        "parameters": ["precip", "temp", "wind"],
        "levels": ["surface"],
        "key": WINDY_API_KEY
    }

    response = requests.post(url, json=payload, timeout=20)

    print("Status code:", response.status_code)

    if response.status_code != 200:
        print("Windy error response:")
        print(response.text)
        raise Exception("Windy API request failed")

    return response.json()


# ============================================================
# Helpers
# ============================================================

def safe_get(data, key, index):
    values = data.get(key)

    if values is None:
        return None

    if index >= len(values):
        return None

    return values[index]


def kelvin_to_celsius(kelvin):
    if kelvin is None:
        return None

    return kelvin - 273.15


def calculate_wind_speed_mps(wind_u, wind_v):
    if wind_u is None or wind_v is None:
        return None

    return math.sqrt(wind_u ** 2 + wind_v ** 2)


# ============================================================
# Parse Windy response
# ============================================================

def parse_weather_response(raw_data, station):
    """
    Converts raw Windy response into clean rows.

    precip_3h_mm means:
        precipitation accumulated during the 3 hours BEFORE forecast_time.
    """

    timestamps = raw_data.get("ts", [])
    rows = []

    vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")

    for i, ts in enumerate(timestamps):
        forecast_time_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        forecast_time_vn = forecast_time_utc.astimezone(vietnam_tz)

        precip_raw = safe_get(raw_data, "past3hprecip-surface", i)
        temp_raw = safe_get(raw_data, "temp-surface", i)
        wind_u = safe_get(raw_data, "wind_u-surface", i)
        wind_v = safe_get(raw_data, "wind_v-surface", i)

        precip_3h_mm = None
        if precip_raw is not None:
            # Windy commonly returns precipitation in metres.
            precip_3h_mm = precip_raw * 1000

        temperature_c = kelvin_to_celsius(temp_raw)
        wind_speed_mps = calculate_wind_speed_mps(wind_u, wind_v)

        row = {
            "weather_station_id": station["id"],
            "weather_station_name": station["name"],
            "province": station["province"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],

            "forecast_time_utc": forecast_time_utc.isoformat(),
            "forecast_time_vn": forecast_time_vn.isoformat(),

            "temperature_c": round(temperature_c, 2) if temperature_c is not None else None,
            "wind_speed_mps": round(wind_speed_mps, 2) if wind_speed_mps is not None else None,
            "precip_3h_mm": round(precip_3h_mm, 2) if precip_3h_mm is not None else None,
        }

        rows.append(row)

    return rows


# ============================================================
# Export
# ============================================================

def export_rows_to_csv(rows, filename):
    if not rows:
        print("No rows to export")
        return

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    fieldnames = rows[0].keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    print("Saved:", filename)


# ============================================================
# Main
# ============================================================

def main():
    weather_stations = load_weather_stations_from_csv(WEATHER_STATION_CSV)

    print(f"Loaded {len(weather_stations)} weather station(s).")

    for station in weather_stations:
        print()
        print("Fetching weather data for:", station["name"])
        print("Coordinate:", station["latitude"], station["longitude"])

        raw_data = fetch_weather_from_windy(
            station["latitude"],
            station["longitude"]
        )

        print("Windy response keys:")
        print(raw_data.keys())

        print("Windy units:")
        print(raw_data.get("units", {}))

        rows = parse_weather_response(raw_data, station)

        filename = os.path.join(
            OUTPUT_DIR,
            f"{station['id']}_weather_forecast.csv"
        )

        export_rows_to_csv(rows, filename)

        print("First 5 rows:")
        for row in rows[:5]:
            print(row)


if __name__ == "__main__":
    main()