from database.db_connection import get_connection


def print_count(connection, table_name):
    row = connection.execute(
        f"SELECT COUNT(*) AS count FROM {table_name}"
    ).fetchone()

    print(table_name + ":", row["count"])


def main():
    connection = get_connection()

    print("Table counts:")
    print_count(connection, "weather_station")
    print_count(connection, "telecom_station")
    print_count(connection, "weather_forecast")
    print_count(connection, "telecom_weather_station_mapping")
    print_count(connection, "telecom_flood_risk_forecast")

    print()
    print("Sample HIGH risk rows:")

    rows = connection.execute(
        """
        SELECT
            r.telecom_station_id,
            t.name AS telecom_station_name,
            t.new_province,
            r.forecast_time_vn,
            r.precip_24h_mm,
            r.flood_risk,
            r.risk_reason
        FROM telecom_flood_risk_forecast r
        JOIN telecom_station t
        ON r.telecom_station_id = t.id
        WHERE r.flood_risk = 'HIGH'
        LIMIT 10
        """
    ).fetchall()

    for row in rows:
        print(dict(row))

    connection.close()


if __name__ == "__main__":
    main()