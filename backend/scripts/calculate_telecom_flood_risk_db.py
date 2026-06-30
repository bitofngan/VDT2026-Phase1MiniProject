from math import radians, sin, cos, sqrt, atan2

from database.db_connection import get_connection


MAX_RADIUS_KM = 100

FLOOD_RISK_SAFE = "SAFE"
FLOOD_RISK_LOW = "LOW"
FLOOD_RISK_MEDIUM = "MEDIUM"
FLOOD_RISK_HIGH = "HIGH"
FLOOD_RISK_UNKNOWN = "UNKNOWN"

# Set to None to process all.
# Use 20 first to test quickly.
PROCESS_LIMIT = 20

CALCULATE_RISK_OUTSIDE_RADIUS = True


def haversine_distance_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def get_all_weather_stations(connection):
    rows = connection.execute(
        """
        SELECT *
        FROM weather_station
        """
    ).fetchall()

    return rows


def get_telecom_stations(connection):
    query = """
        SELECT *
        FROM telecom_station
        ORDER BY id
    """

    if PROCESS_LIMIT is not None:
        query += f" LIMIT {PROCESS_LIMIT}"

    rows = connection.execute(query).fetchall()

    return rows


def find_nearest_weather_station(telecom_station, weather_stations):
    if not weather_stations:
        return None, None, "no_weather_stations_available"

    nearest_station = None
    nearest_distance = float("inf")

    for weather_station in weather_stations:
        distance = haversine_distance_km(
            telecom_station["latitude"],
            telecom_station["longitude"],
            weather_station["latitude"],
            weather_station["longitude"]
        )

        if distance < nearest_distance:
            nearest_station = weather_station
            nearest_distance = distance

    if nearest_distance <= MAX_RADIUS_KM:
        status = "within_radius"
    else:
        status = "outside_max_radius"

    return nearest_station, nearest_distance, status


def save_mapping(connection, telecom_station, weather_station, distance_km, status):
    if weather_station is None:
        weather_station_id = None
    else:
        weather_station_id = weather_station["id"]

    connection.execute(
        """
        INSERT OR REPLACE INTO telecom_weather_station_mapping (
            telecom_station_id,
            weather_station_id,
            distance_km,
            max_radius_km,
            radius_status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            telecom_station["id"],
            weather_station_id,
            distance_km,
            MAX_RADIUS_KM,
            status,
        )
    )


def get_weather_forecasts(connection, weather_station_id):
    rows = connection.execute(
        """
        SELECT *
        FROM weather_forecast
        WHERE weather_station_id = ?
        ORDER BY forecast_time_utc
        """,
        (weather_station_id,)
    ).fetchall()

    return rows


def clear_previous_results(connection):
    connection.execute("DELETE FROM telecom_weather_station_mapping")
    connection.execute("DELETE FROM telecom_flood_risk_forecast")


def bool_to_int(value):
    if value:
        return 1

    return 0


def insert_unknown_risk(connection, telecom_station, weather_station, reason):
    if weather_station is None:
        weather_station_id = None
    else:
        weather_station_id = weather_station["id"]

    connection.execute(
        """
        INSERT INTO telecom_flood_risk_forecast (
            telecom_station_id,
            weather_station_id,
            forecast_time_utc,
            forecast_time_vn,
            temperature_c,
            wind_speed_mps,
            precip_3h_mm,
            avg_precip_1h_mm,
            precip_24h_mm,
            estimated_1h_high_threshold_mm,
            exceed_1h_threshold,
            exceed_24h_threshold,
            flood_risk,
            risk_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            telecom_station["id"],
            weather_station_id,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            FLOOD_RISK_UNKNOWN,
            reason,
        )
    )


def calculate_and_save_flood_risk(connection, telecom_station, weather_station, weather_rows):
    low_threshold_24h = telecom_station["low_rain_threshold_24h_mm"]
    medium_threshold_24h = telecom_station["medium_rain_threshold_24h_mm"]
    high_threshold_24h = telecom_station["high_rain_threshold_24h_mm"]

    estimated_1h_high_threshold = high_threshold_24h / 3

    for i in range(len(weather_rows)):
        weather_row = weather_rows[i]

        precip_3h_mm = weather_row["precip_3h_mm"]
        avg_precip_1h_mm = precip_3h_mm / 3

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

        connection.execute(
            """
            INSERT INTO telecom_flood_risk_forecast (
                telecom_station_id,
                weather_station_id,
                forecast_time_utc,
                forecast_time_vn,
                temperature_c,
                wind_speed_mps,
                precip_3h_mm,
                avg_precip_1h_mm,
                precip_24h_mm,
                estimated_1h_high_threshold_mm,
                exceed_1h_threshold,
                exceed_24h_threshold,
                flood_risk,
                risk_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telecom_station["id"],
                weather_station["id"],
                weather_row["forecast_time_utc"],
                weather_row["forecast_time_vn"],
                weather_row["temperature_c"],
                weather_row["wind_speed_mps"],
                round(precip_3h_mm, 2),
                round(avg_precip_1h_mm, 2),
                round(precip_24h_mm, 2),
                round(estimated_1h_high_threshold, 2),
                bool_to_int(exceed_1h_threshold),
                bool_to_int(exceed_24h_threshold),
                flood_risk,
                risk_reason,
            )
        )


def main():
    connection = get_connection()

    print("Clearing previous mapping and flood-risk results...")
    clear_previous_results(connection)

    weather_stations = get_all_weather_stations(connection)
    telecom_stations = get_telecom_stations(connection)

    print("Weather stations:", len(weather_stations))
    print("Telecom stations to process:", len(telecom_stations))
    print()

    for index, telecom_station in enumerate(telecom_stations, start=1):
        nearest_weather_station, distance_km, status = find_nearest_weather_station(
            telecom_station,
            weather_stations
        )

        save_mapping(
            connection,
            telecom_station,
            nearest_weather_station,
            distance_km,
            status
        )

        if nearest_weather_station is None:
            insert_unknown_risk(
                connection,
                telecom_station,
                None,
                "no_nearest_weather_station"
            )
            continue

        if status == "outside_max_radius" and not CALCULATE_RISK_OUTSIDE_RADIUS:
            insert_unknown_risk(
                connection,
                telecom_station,
                nearest_weather_station,
                "nearest_weather_station_outside_max_radius"
            )
            continue

        weather_rows = get_weather_forecasts(
            connection,
            nearest_weather_station["id"]
        )

        if not weather_rows:
            insert_unknown_risk(
                connection,
                telecom_station,
                nearest_weather_station,
                "no_weather_forecast_rows"
            )
            continue

        calculate_and_save_flood_risk(
            connection,
            telecom_station,
            nearest_weather_station,
            weather_rows
        )

        print(
            f"Processed {index}/{len(telecom_stations)}:",
            telecom_station["id"],
            "->",
            nearest_weather_station["id"],
            "|",
            round(distance_km, 2),
            "km",
            "|",
            status
        )

    connection.commit()
    connection.close()

    print()
    print("Done.")
    print("Results saved into data/flood_warning.db")


if __name__ == "__main__":
    main()