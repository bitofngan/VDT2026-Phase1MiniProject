import os
import sqlite3
from database.db_connection import DATABASE_FILE


REQUIRED_TABLES = [
    "weather_station",
    "telecom_station",
    "weather_forecast",
    "telecom_weather_station_mapping",
    "telecom_flood_risk_forecast",
]


VALID_FLOOD_RISKS = {
    "SAFE",
    "LOW",
    "MEDIUM",
    "HIGH",
    "UNKNOWN",
}


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    # Enable foreign key checking in SQLite
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def print_section(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def check_database_file():
    print_section("1. Checking database file")

    if not os.path.exists(DATABASE_FILE):
        print("FAILED: Database file does not exist.")
        print("Expected:", DATABASE_FILE)
        return False

    file_size_mb = os.path.getsize(DATABASE_FILE) / (1024 * 1024)

    print("PASSED: Database file exists.")
    print("Path:", DATABASE_FILE)
    print("Size:", round(file_size_mb, 2), "MB")

    return True


def check_required_tables(connection):
    print_section("2. Checking required tables")

    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    existing_tables = set(row["name"] for row in rows)

    all_ok = True

    for table in REQUIRED_TABLES:
        if table in existing_tables:
            print("PASSED:", table)
        else:
            print("FAILED:", table, "is missing")
            all_ok = False

    return all_ok


def check_table_counts(connection):
    print_section("3. Checking table row counts")

    all_ok = True

    for table in REQUIRED_TABLES:
        row = connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            """
        ).fetchone()

        count = row["count"]

        print(table + ":", count, "rows")

        if count == 0:
            print("WARNING:", table, "has 0 rows")
            all_ok = False

    return all_ok


def check_foreign_key_integrity(connection):
    print_section("4. Checking foreign key integrity")

    rows = connection.execute("PRAGMA foreign_key_check").fetchall()

    if not rows:
        print("PASSED: No foreign key problems found.")
        return True

    print("FAILED: Foreign key problems found.")

    for row in rows:
        print(dict(row))

    return False


def check_mapping_join(connection):
    print_section("5. Checking telecom station to weather station mapping join")

    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM telecom_weather_station_mapping m
        JOIN telecom_station t
        ON m.telecom_station_id = t.id
        LEFT JOIN weather_station w
        ON m.weather_station_id = w.id
        """
    ).fetchone()

    count = row["count"]

    print("Mapping rows that can join to telecom_station:", count)

    sample_rows = connection.execute(
        """
        SELECT
            t.id AS telecom_station_id,
            t.name AS telecom_station_name,
            t.new_province,
            w.id AS weather_station_id,
            w.name AS weather_station_name,
            m.distance_km,
            m.max_radius_km,
            m.radius_status
        FROM telecom_weather_station_mapping m
        JOIN telecom_station t
        ON m.telecom_station_id = t.id
        LEFT JOIN weather_station w
        ON m.weather_station_id = w.id
        ORDER BY t.id
        LIMIT 10
        """
    ).fetchall()

    print()
    print("Sample mapping rows:")

    for row in sample_rows:
        print(dict(row))

    return count > 0


def check_flood_risk_join(connection):
    print_section("6. Checking flood risk join")

    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM telecom_flood_risk_forecast r
        JOIN telecom_station t
        ON r.telecom_station_id = t.id
        LEFT JOIN weather_station w
        ON r.weather_station_id = w.id
        """
    ).fetchone()

    count = row["count"]

    print("Flood risk rows that can join to telecom_station:", count)

    sample_rows = connection.execute(
        """
        SELECT
            r.telecom_station_id,
            t.name AS telecom_station_name,
            t.new_province,
            r.weather_station_id,
            w.name AS weather_station_name,
            r.forecast_time_vn,
            r.precip_3h_mm,
            r.precip_24h_mm,
            r.flood_risk,
            r.risk_reason
        FROM telecom_flood_risk_forecast r
        JOIN telecom_station t
        ON r.telecom_station_id = t.id
        LEFT JOIN weather_station w
        ON r.weather_station_id = w.id
        ORDER BY r.telecom_station_id, r.forecast_time_utc
        LIMIT 10
        """
    ).fetchall()

    print()
    print("Sample flood risk rows:")

    for row in sample_rows:
        print(dict(row))

    return count > 0


def check_flood_risk_values(connection):
    print_section("7. Checking flood risk values")

    rows = connection.execute(
        """
        SELECT flood_risk, COUNT(*) AS count
        FROM telecom_flood_risk_forecast
        GROUP BY flood_risk
        ORDER BY count DESC
        """
    ).fetchall()

    all_ok = True

    print("Flood risk distribution:")

    for row in rows:
        flood_risk = row["flood_risk"]
        count = row["count"]

        print(flood_risk, ":", count)

        if flood_risk not in VALID_FLOOD_RISKS:
            print("FAILED: Invalid flood risk value:", flood_risk)
            all_ok = False

    if all_ok:
        print("PASSED: All flood risk values are valid.")

    return all_ok


def check_radius_status_distribution(connection):
    print_section("8. Checking nearest weather station radius status")

    rows = connection.execute(
        """
        SELECT radius_status, COUNT(*) AS count
        FROM telecom_weather_station_mapping
        GROUP BY radius_status
        ORDER BY count DESC
        """
    ).fetchall()

    print("Radius status distribution:")

    for row in rows:
        print(row["radius_status"], ":", row["count"])

    return True


def show_medium_high_risk_samples(connection):
    print_section("9. Showing MEDIUM / HIGH risk samples")

    rows = connection.execute(
        """
        SELECT
            r.telecom_station_id,
            t.name AS telecom_station_name,
            t.new_province,
            t.elevation_m,
            r.weather_station_id,
            w.name AS weather_station_name,
            r.forecast_time_vn,
            r.precip_3h_mm,
            r.avg_precip_1h_mm,
            r.precip_24h_mm,
            t.low_rain_threshold_24h_mm,
            t.medium_rain_threshold_24h_mm,
            t.high_rain_threshold_24h_mm,
            r.flood_risk,
            r.risk_reason
        FROM telecom_flood_risk_forecast r
        JOIN telecom_station t
        ON r.telecom_station_id = t.id
        LEFT JOIN weather_station w
        ON r.weather_station_id = w.id
        WHERE r.flood_risk IN ('MEDIUM', 'HIGH')
        ORDER BY
            CASE r.flood_risk
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                ELSE 3
            END,
            r.precip_24h_mm DESC
        LIMIT 20
        """
    ).fetchall()

    if not rows:
        print("No MEDIUM or HIGH risk rows found.")
        print("This can be okay if current forecast rainfall is low.")
        return True

    for row in rows:
        print(dict(row))

    return True


def show_database_summary(connection):
    print_section("10. Database summary")

    summary = connection.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM weather_station) AS weather_station_count,
            (SELECT COUNT(*) FROM telecom_station) AS telecom_station_count,
            (SELECT COUNT(*) FROM weather_forecast) AS weather_forecast_count,
            (SELECT COUNT(*) FROM telecom_weather_station_mapping) AS mapping_count,
            (SELECT COUNT(*) FROM telecom_flood_risk_forecast) AS flood_risk_count
        """
    ).fetchone()

    print(dict(summary))


def main():
    print("Testing SQLite database functionality...")

    if not check_database_file():
        return

    connection = get_connection()

    test_results = []

    test_results.append(check_required_tables(connection))
    test_results.append(check_table_counts(connection))
    test_results.append(check_foreign_key_integrity(connection))
    test_results.append(check_mapping_join(connection))
    test_results.append(check_flood_risk_join(connection))
    test_results.append(check_flood_risk_values(connection))
    test_results.append(check_radius_status_distribution(connection))
    test_results.append(show_medium_high_risk_samples(connection))

    show_database_summary(connection)

    connection.close()

    print_section("Final result")

    if all(test_results):
        print("DATABASE TEST PASSED")
    else:
        print("DATABASE TEST FINISHED WITH WARNINGS OR FAILURES")
        print("Check the sections above for details.")


if __name__ == "__main__":
    main()