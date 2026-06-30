import csv
import glob
import os

from database.db_connection import get_connection


WEATHER_STATION_CSV = "data/weather_stations.csv"
TELECOM_STATION_CSV = "data/telecom_stations_with_thresholds.csv"
WEATHER_FORECAST_DIR = "weather_forecast_outputs"


def safe_float(value, default=None):
    if value is None:
        return default

    if value == "":
        return default

    return float(value)


def import_weather_stations(connection):
    print("Importing weather stations...")

    with open(WEATHER_STATION_CSV, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
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
                    row["id"],
                    row["name"],
                    row["province"],
                    float(row["latitude"]),
                    float(row["longitude"]),
                )
            )

            count += 1

    print("Weather stations imported:", count)


def import_telecom_stations(connection):
    print("Importing telecom stations...")

    with open(TELECOM_STATION_CSV, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

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
    print("Importing weather forecasts...")

    forecast_files = glob.glob(
        os.path.join(WEATHER_FORECAST_DIR, "*_weather_forecast.csv")
    )

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


def main():
    connection = get_connection()

    import_weather_stations(connection)
    import_telecom_stations(connection)
    import_weather_forecasts(connection)

    connection.commit()
    connection.close()

    print()
    print("CSV import completed.")


if __name__ == "__main__":
    main()