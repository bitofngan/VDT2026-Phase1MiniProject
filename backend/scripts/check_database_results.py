import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection, DATABASE_FILE


def print_count(connection, table_name):
    row = connection.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM {table_name}
        """
    ).fetchone()

    print(table_name + ":", row["count"])


def main():
    connection = get_connection()

    print("Database file:", DATABASE_FILE)
    print()

    print("Table counts:")
    print_count(connection, "weather_station")
    print_count(connection, "telecom_station")
    print_count(connection, "weather_forecast")
    print_count(connection, "telecom_weather_station_mapping")
    print_count(connection, "telecom_flood_risk_forecast")

    print()
    print("Flood risk distribution:")

    rows = connection.execute(
        """
        SELECT flood_risk, COUNT(*) AS count
        FROM telecom_flood_risk_forecast
        GROUP BY flood_risk
        ORDER BY count DESC
        """
    ).fetchall()

    for row in rows:
        print(row["flood_risk"], ":", row["count"])

    print()
    print("Radius status distribution:")

    rows = connection.execute(
        """
        SELECT radius_status, COUNT(*) AS count
        FROM telecom_weather_station_mapping
        GROUP BY radius_status
        ORDER BY count DESC
        """
    ).fetchall()

    for row in rows:
        print(row["radius_status"], ":", row["count"])

    print()
    print("Sample flood risk rows:")

    rows = connection.execute(
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

    for row in rows:
        print(dict(row))

    connection.close()


if __name__ == "__main__":
    main()