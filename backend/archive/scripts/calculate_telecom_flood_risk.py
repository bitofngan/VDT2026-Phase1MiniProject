import csv
import os

from backend.archive.scripts.weather_station_loader import load_weather_stations_from_csv
from backend.archive.scripts.nearest_weather_station import find_nearest_weather_station


# ============================================================
# File paths
# ============================================================

TELECOM_STATION_CSV = "data/telecom_stations_with_thresholds.csv"
WEATHER_STATION_CSV = "data/weather_stations.csv"
WEATHER_FORECAST_DIR = "weather_forecast_outputs"

MAPPING_OUTPUT_FILE = "data/telecom_weather_station_mapping.csv"
FLOOD_RISK_OUTPUT_FILE = "flood_risk_outputs/telecom_flood_risk_forecast.csv"


# ============================================================
# Config
# ============================================================

# Use None to process all telecom stations.
# Use a small number like 20 for testing.
PROCESS_LIMIT = None

# For POC, calculate risk even if nearest weather station is outside max radius.
# The output still includes weather_station_radius_status.
# Later, you can set this to False if you want outside-radius stations to be UNKNOWN.
CALCULATE_RISK_OUTSIDE_RADIUS = True


# ============================================================
# Flood risk constants
# ============================================================

FLOOD_RISK_SAFE = "SAFE"
FLOOD_RISK_LOW = "LOW"
FLOOD_RISK_MEDIUM = "MEDIUM"
FLOOD_RISK_HIGH = "HIGH"
FLOOD_RISK_UNKNOWN = "UNKNOWN"


# ============================================================
# Helpers
# ============================================================

def safe_float(value, default=None):
    if value is None:
        return default

    if value == "":
        return default

    return float(value)


def export_rows_to_csv(rows, filename):
    if not rows:
        print("No rows to export:", filename)
        return

    output_folder = os.path.dirname(filename)

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)

    fieldnames = rows[0].keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Saved:", filename)


# ============================================================
# Load telecom stations
# ============================================================

def load_telecom_stations_from_csv(filename):
    """
    Load telecom stations with elevation and 24-hour rainfall thresholds.

    Expected input:
        data/telecom_stations_with_thresholds.csv
    """

    telecom_stations = []

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            station = {
                "id": row["id"],
                "name": row["name"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),

                "old_province": row.get("old_province", ""),
                "new_province": row.get("new_province", ""),
                "province_mapping_status": row.get("province_mapping_status", ""),

                "elevation_m": safe_float(row.get("elevation_m")),

                # These thresholds are interpreted as 24-hour accumulated rainfall thresholds.
                "low_rain_threshold_24h_mm": safe_float(
                    row.get("low_rain_threshold_mm"),
                    80
                ),
                "medium_rain_threshold_24h_mm": safe_float(
                    row.get("medium_rain_threshold_mm"),
                    150
                ),
                "high_rain_threshold_24h_mm": safe_float(
                    row.get("high_rain_threshold_mm"),
                    200
                ),
            }

            telecom_stations.append(station)

    return telecom_stations


# ============================================================
# Load weather forecast
# ============================================================

def load_weather_forecast_csv(weather_station_id):
    """
    Load forecast CSV for one weather station.

    Expected file:
        weather_forecast_outputs/<weather_station_id>_weather_forecast.csv
    """

    filename = os.path.join(
        WEATHER_FORECAST_DIR,
        f"{weather_station_id}_weather_forecast.csv"
    )

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Missing weather forecast file: {filename}")

    rows = []

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            clean_row = {
                "weather_station_id": row["weather_station_id"],
                "weather_station_name": row["weather_station_name"],
                "weather_station_province": row["province"],
                "weather_station_latitude": float(row["latitude"]),
                "weather_station_longitude": float(row["longitude"]),

                "forecast_time_utc": row["forecast_time_utc"],
                "forecast_time_vn": row["forecast_time_vn"],

                "temperature_c": safe_float(row.get("temperature_c")),
                "wind_speed_mps": safe_float(row.get("wind_speed_mps")),
                "precip_3h_mm": safe_float(row.get("precip_3h_mm"), 0),
            }

            rows.append(clean_row)

    return rows


# ============================================================
# Nearest weather station mapping
# ============================================================

def create_mapping_row(telecom_station, nearest_result):
    nearest_weather_station = nearest_result["station"]

    if nearest_weather_station is None:
        return {
            "telecom_station_id": telecom_station["id"],
            "telecom_station_name": telecom_station["name"],
            "telecom_latitude": telecom_station["latitude"],
            "telecom_longitude": telecom_station["longitude"],
            "new_province": telecom_station["new_province"],
            "elevation_m": telecom_station["elevation_m"],
            "low_rain_threshold_24h_mm": telecom_station["low_rain_threshold_24h_mm"],
            "medium_rain_threshold_24h_mm": telecom_station["medium_rain_threshold_24h_mm"],
            "high_rain_threshold_24h_mm": telecom_station["high_rain_threshold_24h_mm"],

            "nearest_weather_station_id": "",
            "nearest_weather_station_name": "",
            "nearest_weather_station_province": "",
            "nearest_weather_station_latitude": "",
            "nearest_weather_station_longitude": "",
            "nearest_weather_station_distance_km": "",
            "max_radius_km": nearest_result["max_radius_km"],
            "weather_station_radius_status": nearest_result["status"],
        }

    return {
        "telecom_station_id": telecom_station["id"],
        "telecom_station_name": telecom_station["name"],
        "telecom_latitude": telecom_station["latitude"],
        "telecom_longitude": telecom_station["longitude"],
        "new_province": telecom_station["new_province"],
        "elevation_m": telecom_station["elevation_m"],
        "low_rain_threshold_24h_mm": telecom_station["low_rain_threshold_24h_mm"],
        "medium_rain_threshold_24h_mm": telecom_station["medium_rain_threshold_24h_mm"],
        "high_rain_threshold_24h_mm": telecom_station["high_rain_threshold_24h_mm"],

        "nearest_weather_station_id": nearest_weather_station["id"],
        "nearest_weather_station_name": nearest_weather_station["name"],
        "nearest_weather_station_province": nearest_weather_station["province"],
        "nearest_weather_station_latitude": nearest_weather_station["latitude"],
        "nearest_weather_station_longitude": nearest_weather_station["longitude"],
        "nearest_weather_station_distance_km": round(nearest_result["distance_km"], 2),
        "max_radius_km": nearest_result["max_radius_km"],
        "weather_station_radius_status": nearest_result["status"],
    }


# ============================================================
# Flood risk formula
# ============================================================

def calculate_flood_risk_for_station(telecom_station, weather_rows):
    """
    Calculate flood risk for one telecom station over all forecast times.

    Rainfall meaning:
        precip_3h_mm:
            rain accumulated over the previous 3 hours

        avg_precip_1h_mm:
            estimated average hourly rain intensity
            precip_3h_mm / 3

        precip_24h_mm:
            rolling 24-hour accumulated rain
            current 3h value + previous 7 values

    Threshold meaning:
        low_rain_threshold_24h_mm:
            24-hour accumulated rainfall threshold for LOW risk

        medium_rain_threshold_24h_mm:
            24-hour accumulated rainfall threshold for MEDIUM risk

        high_rain_threshold_24h_mm:
            24-hour accumulated rainfall threshold for HIGH risk

    Extra 1h warning:
        Because intense short rain can still be dangerous, estimate a 1h high threshold:

            estimated_1h_high_threshold_mm = high_rain_threshold_24h_mm / 3

        This is a simple proof-of-concept approximation.
    """

    result_rows = []

    low_threshold_24h = telecom_station["low_rain_threshold_24h_mm"]
    medium_threshold_24h = telecom_station["medium_rain_threshold_24h_mm"]
    high_threshold_24h = telecom_station["high_rain_threshold_24h_mm"]

    estimated_1h_high_threshold = high_threshold_24h / 3

    for i in range(len(weather_rows)):
        weather_row = weather_rows[i]

        precip_3h_mm = weather_row["precip_3h_mm"]
        avg_precip_1h_mm = precip_3h_mm / 3

        # Rolling 24h window:
        # current row + previous 7 rows = 8 rows
        # 8 rows x 3h = 24h
        start_index = max(0, i - 7)
        previous_24h_rows = weather_rows[start_index:i + 1]

        precip_24h_mm = 0

        for row in previous_24h_rows:
            precip_24h_mm += row["precip_3h_mm"]

        exceed_1h_threshold = avg_precip_1h_mm > estimated_1h_high_threshold
        exceed_24h_threshold = precip_24h_mm >= high_threshold_24h

        if exceed_1h_threshold:
            flood_risk = FLOOD_RISK_HIGH
            risk_reason = "avg_1h_precip_exceeds_estimated_1h_high_threshold"

        elif exceed_24h_threshold:
            flood_risk = FLOOD_RISK_HIGH
            risk_reason = "rolling_24h_precip_exceeds_high_threshold"

        elif precip_24h_mm >= medium_threshold_24h:
            flood_risk = FLOOD_RISK_MEDIUM
            risk_reason = "rolling_24h_precip_exceeds_medium_threshold"

        elif precip_24h_mm >= low_threshold_24h:
            flood_risk = FLOOD_RISK_LOW
            risk_reason = "rolling_24h_precip_exceeds_low_threshold"

        else:
            flood_risk = FLOOD_RISK_SAFE
            risk_reason = "rainfall_below_thresholds"

        result_row = {
            "forecast_time_utc": weather_row["forecast_time_utc"],
            "forecast_time_vn": weather_row["forecast_time_vn"],

            "temperature_c": weather_row["temperature_c"],
            "wind_speed_mps": weather_row["wind_speed_mps"],

            "precip_3h_mm": round(precip_3h_mm, 2),
            "avg_precip_1h_mm": round(avg_precip_1h_mm, 2),
            "precip_24h_mm": round(precip_24h_mm, 2),

            "low_rain_threshold_24h_mm": low_threshold_24h,
            "medium_rain_threshold_24h_mm": medium_threshold_24h,
            "high_rain_threshold_24h_mm": high_threshold_24h,
            "estimated_1h_high_threshold_mm": round(estimated_1h_high_threshold, 2),

            "exceed_1h_threshold": exceed_1h_threshold,
            "exceed_24h_threshold": exceed_24h_threshold,

            "flood_risk": flood_risk,
            "risk_reason": risk_reason,
        }

        result_rows.append(result_row)

    return result_rows


def create_unknown_risk_row(telecom_station, nearest_result, reason):
    """
    Used when we cannot calculate reliable flood risk.
    """

    nearest_weather_station = nearest_result["station"]

    if nearest_weather_station is None:
        weather_station_id = ""
        weather_station_name = ""
    else:
        weather_station_id = nearest_weather_station["id"]
        weather_station_name = nearest_weather_station["name"]

    return {
        "telecom_station_id": telecom_station["id"],
        "telecom_station_name": telecom_station["name"],
        "telecom_latitude": telecom_station["latitude"],
        "telecom_longitude": telecom_station["longitude"],
        "new_province": telecom_station["new_province"],
        "elevation_m": telecom_station["elevation_m"],

        "nearest_weather_station_id": weather_station_id,
        "nearest_weather_station_name": weather_station_name,
        "nearest_weather_station_distance_km": (
            round(nearest_result["distance_km"], 2)
            if nearest_result["distance_km"] is not None
            else ""
        ),
        "max_radius_km": nearest_result["max_radius_km"],
        "weather_station_radius_status": nearest_result["status"],

        "forecast_time_utc": "",
        "forecast_time_vn": "",
        "temperature_c": "",
        "wind_speed_mps": "",
        "precip_3h_mm": "",
        "avg_precip_1h_mm": "",
        "precip_24h_mm": "",

        "low_rain_threshold_24h_mm": telecom_station["low_rain_threshold_24h_mm"],
        "medium_rain_threshold_24h_mm": telecom_station["medium_rain_threshold_24h_mm"],
        "high_rain_threshold_24h_mm": telecom_station["high_rain_threshold_24h_mm"],
        "estimated_1h_high_threshold_mm": "",

        "exceed_1h_threshold": "",
        "exceed_24h_threshold": "",

        "flood_risk": FLOOD_RISK_UNKNOWN,
        "risk_reason": reason,
    }


# ============================================================
# Main
# ============================================================

def main():
    print("Loading telecom stations...")
    telecom_stations = load_telecom_stations_from_csv(TELECOM_STATION_CSV)

    print("Loading weather stations...")
    weather_stations = load_weather_stations_from_csv(WEATHER_STATION_CSV)

    print("Telecom stations:", len(telecom_stations))
    print("Weather stations:", len(weather_stations))

    if PROCESS_LIMIT is not None:
        telecom_stations = telecom_stations[:PROCESS_LIMIT]
        print("Processing limit:", PROCESS_LIMIT)

    print()

    mapping_rows = []
    flood_risk_rows = []

    weather_forecast_cache = {}

    for index, telecom_station in enumerate(telecom_stations, start=1):
        nearest_result = find_nearest_weather_station(
            telecom_station["latitude"],
            telecom_station["longitude"],
            weather_stations
        )

        nearest_weather_station = nearest_result["station"]

        mapping_row = create_mapping_row(telecom_station, nearest_result)
        mapping_rows.append(mapping_row)

        if nearest_weather_station is None:
            unknown_row = create_unknown_risk_row(
                telecom_station,
                nearest_result,
                "no_nearest_weather_station"
            )
            flood_risk_rows.append(unknown_row)
            continue

        if (
            nearest_result["status"] == "outside_max_radius"
            and not CALCULATE_RISK_OUTSIDE_RADIUS
        ):
            unknown_row = create_unknown_risk_row(
                telecom_station,
                nearest_result,
                "nearest_weather_station_outside_max_radius"
            )
            flood_risk_rows.append(unknown_row)
            continue

        weather_station_id = nearest_weather_station["id"]

        if weather_station_id not in weather_forecast_cache:
            weather_forecast_cache[weather_station_id] = load_weather_forecast_csv(
                weather_station_id
            )

        weather_rows = weather_forecast_cache[weather_station_id]

        station_flood_rows = calculate_flood_risk_for_station(
            telecom_station,
            weather_rows
        )

        for row in station_flood_rows:
            output_row = {
                "telecom_station_id": telecom_station["id"],
                "telecom_station_name": telecom_station["name"],
                "telecom_latitude": telecom_station["latitude"],
                "telecom_longitude": telecom_station["longitude"],
                "old_province": telecom_station["old_province"],
                "new_province": telecom_station["new_province"],
                "province_mapping_status": telecom_station["province_mapping_status"],
                "elevation_m": telecom_station["elevation_m"],

                "nearest_weather_station_id": nearest_weather_station["id"],
                "nearest_weather_station_name": nearest_weather_station["name"],
                "nearest_weather_station_province": nearest_weather_station["province"],
                "nearest_weather_station_latitude": nearest_weather_station["latitude"],
                "nearest_weather_station_longitude": nearest_weather_station["longitude"],
                "nearest_weather_station_distance_km": round(nearest_result["distance_km"], 2),
                "max_radius_km": nearest_result["max_radius_km"],
                "weather_station_radius_status": nearest_result["status"],
            }

            output_row.update(row)
            flood_risk_rows.append(output_row)

        print(
            f"Processed {index}/{len(telecom_stations)}:",
            telecom_station["id"],
            "->",
            nearest_weather_station["id"],
            "|",
            round(nearest_result["distance_km"], 2),
            "km",
            "|",
            nearest_result["status"]
        )

    print()
    export_rows_to_csv(mapping_rows, MAPPING_OUTPUT_FILE)
    export_rows_to_csv(flood_risk_rows, FLOOD_RISK_OUTPUT_FILE)

    print()
    print("Done.")
    print("Mapping output:", MAPPING_OUTPUT_FILE)
    print("Flood risk output:", FLOOD_RISK_OUTPUT_FILE)


if __name__ == "__main__":
    main()