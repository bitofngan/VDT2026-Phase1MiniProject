import csv
import glob
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection


WEATHER_STATION_CSV = PROJECT_ROOT / "data" / "weather_stations.csv"
TELECOM_STATION_CSV = PROJECT_ROOT / "data" / "telecom_stations_with_thresholds.csv"
WEATHER_FORECAST_DIR = PROJECT_ROOT / "weather_forecast_outputs"


def safe_float(value, default=None):
    if value is None:
        return default

    if value == "":
        return default

    return float(value)


def get_required(row, possible_names):
    for name in possible_names:
        if name in row and row[name] != "":
            return row[name]

    raise KeyError(f"Missing required column. Expected one of: {possible_names}")


def import_weather_stations(connection):
    print("Importing weather stations...")
    print("Weather station CSV:", WEATHER_STATION_CSV)

    with open(WEATHER_STATION_CSV, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        print("Weather station CSV columns found:", reader.fieldnames)

        count = 0

        for row in reader:
            station_id = get_required(row, ["id", "station_id"])
            name = get_required(row, ["name", "station_name"])
            province = get_required(row, ["province"])
            latitude = float(get_required(row, ["latitude", "lat"]))
            longitude = float(get_required(row, ["longitude", "lon", "lng"]))

            connection.execute(
                """
                INSERT OR REPLACE INTO weather_station (
                    id,
                    name,
                    province,
                    latitude,
                    longitude
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    station_id,
                    name,
                    province,
                    latitude,
                    longitude,
                )
            )

            count += 1

    print("Weather stations imported:", count)


def import_telecom_stations(connection):
    print()
    print("Importing telecom stations...")
    print("Telecom station CSV:", TELECOM_STATION_CSV)

    with open(TELECOM_STATION_CSV, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        print("Telecom station CSV columns found:", reader.fieldnames)

        count = 0

        for row in reader:
            connection.execute(
                """
                INSERT OR REPLACE INTO telecom_station (
                    id,
                    name,
                    latitude,
                    longitude,
                    old_province,
                    new_province,
                    province_mapping_status,
                    elevation_m,
                    low_rain_threshold_24h_mm,
                    medium_rain_threshold_24h_mm,
                    high_rain_threshold_24h_mm
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["name"],
                    float(row["latitude"]),
                    float(row["longitude"]),
                    row.get("old_province", ""),
                    row.get("new_province", ""),
                    row.get("province_mapping_status", ""),
                    safe_float(row.get("elevation_m")),
                    safe_float(row.get("low_rain_threshold_mm"), 80),
                    safe_float(row.get("medium_rain_threshold_mm"), 150),
                    safe_float(row.get("high_rain_threshold_mm"), 200),
                )
            )

            count += 1

    print("Telecom stations imported:", count)


def import_weather_forecasts(connection):
    print()
    print("Importing weather forecasts...")
    print("Weather forecast folder:", WEATHER_FORECAST_DIR)

    forecast_files = glob.glob(
        str(WEATHER_FORECAST_DIR / "*_weather_forecast.csv")
    )

    if not forecast_files:
        print("WARNING: No weather forecast CSV files found.")
        print("Expected files like:")
        print(WEATHER_FORECAST_DIR / "WS_HN_01_weather_forecast.csv")
        return

    total_count = 0

    for filename in forecast_files:
        print("Reading:", filename)

        with open(filename, mode="r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                connection.execute(
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
                    (
                        row["weather_station_id"],
                        row["forecast_time_utc"],
                        row["forecast_time_vn"],
                        safe_float(row.get("temperature_c")),
                        safe_float(row.get("wind_speed_mps")),
                        safe_float(row.get("precip_3h_mm"), 0),
                    )
                )

                total_count += 1

    print("Weather forecast rows imported:", total_count)


def clear_imported_tables(connection):
    connection.execute("DELETE FROM telecom_flood_risk_forecast")
    connection.execute("DELETE FROM telecom_weather_station_mapping")
    connection.execute("DELETE FROM weather_forecast")
    connection.execute("DELETE FROM telecom_station")
    connection.execute("DELETE FROM weather_station")


def main():
    connection = get_connection()

    print("Clearing old imported data...")
    clear_imported_tables(connection)

    import_weather_stations(connection)
    import_telecom_stations(connection)
    import_weather_forecasts(connection)

    connection.commit()
    connection.close()

    print()
    print("CSV import completed.")


if __name__ == "__main__":
    main()