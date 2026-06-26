"""
Fetch precipitation forecasts from Windy Point Forecast API.

What this script does:
1. Loads weather stations / forecast points from data/weather_stations.csv.
2. Sends each station's latitude/longitude to Windy Point Forecast API.
3. Requests precipitation data only.
4. Converts Windy's raw response into readable rows.
5. Calculates simple flood risk using fixed thresholds.
6. Saves one CSV file per weather station.

Before running:
1. Install required packages:
   python -m pip install requests python-dotenv

2. Create a file named .env in the same folder:
   WINDY_POINT_FORECAST_KEY=your_real_windy_point_forecast_key_here

3. Create:
   data/weather_stations.csv

4. Run:
   python fetch_precipitation_forecasts.py
"""

import os
import csv
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from weather_station_loader import load_weather_stations_from_csv


# ============================================================
# 1. File paths
# ============================================================

WEATHER_STATION_CSV = "data/weather_stations.csv"
OUTPUT_DIR = "weather_forecast_outputs"


# ============================================================
# 2. Load Windy API key from .env
# ============================================================

load_dotenv()

WINDY_API_KEY = os.getenv("WINDY_POINT_FORECAST_KEY")

if not WINDY_API_KEY:
    raise ValueError("Missing WINDY_POINT_FORECAST_KEY in .env file")


# ============================================================
# 3. Fetch only precipitation data from Windy
# ============================================================

def fetch_precipitation_from_windy(latitude, longitude):
    """
    Calls Windy Point Forecast API for precipitation only.

    We request:
        "parameters": ["precip"]

    Windy returns:
        "past3hprecip-surface"

    Meaning:
        precipitation accumulated during the 3 hours BEFORE the forecast timestamp.
    """

    url = "https://api.windy.com/api/point-forecast/v2"

    payload = {
        "lat": latitude,
        "lon": longitude,
        "model": "gfs",
        "parameters": ["precip"],
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
# 4. Helper function to safely read Windy array values
# ============================================================

def safe_get(data, key, index):
    values = data.get(key)

    if values is None:
        return None

    if index >= len(values):
        return None

    return values[index]


# ============================================================
# 5. Parse Windy precipitation response into clean rows
# ============================================================

def parse_precipitation_response(raw_data, station):
    """
    Converts raw Windy response into clean rows.

    Windy response key:
        past3hprecip-surface

    Our cleaned column:
        precip_3h_mm

    Meaning:
        precip_3h_mm = precipitation in the 3 hours BEFORE forecast_time.
    """

    timestamps = raw_data.get("ts", [])
    rows = []

    vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")

    for i, ts in enumerate(timestamps):
        forecast_time_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        forecast_time_vn = forecast_time_utc.astimezone(vietnam_tz)

        precip_raw = safe_get(raw_data, "past3hprecip-surface", i)

        # Windy commonly returns precipitation in metres.
        # Convert metres to millimetres.
        precip_3h_mm = None
        if precip_raw is not None:
            precip_3h_mm = precip_raw * 1000

        # Approximate average hourly precipitation over the previous 3-hour window.
        avg_precip_1h_mm = None
        if precip_3h_mm is not None:
            avg_precip_1h_mm = precip_3h_mm / 3

        row = {
            "weather_station_id": station["id"],
            "weather_station_name": station["name"],
            "province": station["province"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],

            "forecast_time_utc": forecast_time_utc.isoformat(),
            "forecast_time_vn": forecast_time_vn.isoformat(),

            "precip_3h_mm": precip_3h_mm,
            "avg_precip_1h_mm": avg_precip_1h_mm,
        }

        rows.append(row)

    return rows


# ============================================================
# 6. Calculate flood risk based on precipitation
# ============================================================

def add_flood_risk_to_rows(rows):
    """
    Adds flood risk to each forecast timestamp.

    Fixed thresholds for now:
        - avg_precip_1h_mm > 100
        - precip_24h_mm > 200

    Because Windy gives previous 3-hour precipitation:
        precip_24h_mm = current row + previous 7 rows
        8 rows * 3 hours = 24 hours
    """

    for i in range(len(rows)):
        current_row = rows[i]

        avg_precip_1h_mm = current_row["avg_precip_1h_mm"] or 0

        # Previous 24h window:
        # current row and previous 7 rows
        start_index = max(0, i - 7)
        previous_24h_rows = rows[start_index:i + 1]

        precip_24h_mm = 0

        for row in previous_24h_rows:
            precip_24h_mm += row["precip_3h_mm"] or 0

        exceed_1h = avg_precip_1h_mm > 100
        exceed_24h = precip_24h_mm > 200

        if exceed_1h or exceed_24h:
            flood_risk = "HIGH"
        else:
            flood_risk = "SAFE"

        current_row["precip_24h_mm"] = precip_24h_mm
        current_row["exceed_1h_threshold"] = exceed_1h
        current_row["exceed_24h_threshold"] = exceed_24h
        current_row["flood_risk"] = flood_risk

    return rows


# ============================================================
# 7. Export one CSV file per weather station
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
# 8. Main program
# ============================================================

def main():
    weather_stations = load_weather_stations_from_csv(WEATHER_STATION_CSV)

    print(f"Loaded {len(weather_stations)} weather station(s).")

    for station in weather_stations:
        print()
        print("Fetching precipitation data for:", station["name"])
        print("Coordinate:", station["latitude"], station["longitude"])

        raw_data = fetch_precipitation_from_windy(
            station["latitude"],
            station["longitude"]
        )

        print("Windy response keys:")
        print(raw_data.keys())

        print("Windy units:")
        print(raw_data.get("units", {}))

        rows = parse_precipitation_response(raw_data, station)
        rows = add_flood_risk_to_rows(rows)

        filename = os.path.join(
            OUTPUT_DIR,
            f"{station['id']}_precipitation_forecast.csv"
        )

        export_rows_to_csv(rows, filename)

        print("First 5 rows:")
        for row in rows[:5]:
            print(row)


if __name__ == "__main__":
    main()