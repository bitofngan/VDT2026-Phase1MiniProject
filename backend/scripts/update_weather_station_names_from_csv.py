import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection

FORECAST_DIR = PROJECT_ROOT / "outputs" / "weather_forecast_outputs"


def normalize_id(value):
    text = str(value or "").strip().lower()

    text = text.replace("-", "_")
    text = re.sub(r"[^a-z0-9_]", "", text)

    parts = text.split("_")

    if len(parts) >= 3 and parts[0] == "ws":
        province = "".join(parts[1:-1])
        number = str(int(parts[-1]))
        return f"ws_{province}_{number}"

    return re.sub(r"[^a-z0-9]", "", text)

def read_station_info(csv_file):
    with open(csv_file, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        first_row = next(reader, None)

    if not first_row or len(first_row) < 2:
        return None

    station_id = first_row[0]
    station_name = first_row[1]

    return {
        "id": station_id.strip(),
        "name": station_name.strip(),
    }

def main():
    connection = get_connection()

    db_stations = connection.execute(
        """
        SELECT id, name
        FROM weather_station
        """
    ).fetchall()

    db_id_by_normalized = {
        normalize_id(row["id"]): row["id"]
        for row in db_stations
    }

    updated = 0
    skipped = 0
    not_matched = []

    csv_files = []

    if FORECAST_DIR.exists():
        csv_files.extend(FORECAST_DIR.glob("*_weather_forecast.csv"))

    print("CSV files found:", len(csv_files))

    for csv_file in csv_files:
        info = read_station_info(csv_file)

        if not info:
            skipped += 1
            continue

        csv_station_id = info["id"]
        csv_station_name = info["name"]

        db_station_id = db_id_by_normalized.get(normalize_id(csv_station_id))

        if not db_station_id:
            not_matched.append(csv_station_id)
            continue

        connection.execute(
            """
            UPDATE weather_station
            SET name = ?
            WHERE id = ?
            """,
            (csv_station_name, db_station_id),
        )

        updated += 1

    connection.commit()

    print("Updated weather station names:", updated)
    print("Skipped CSV files:", skipped)
    print("Unmatched station IDs:", len(not_matched))

    if not_matched:
        print("First unmatched IDs:")
        for station_id in not_matched[:20]:
            print("-", station_id)

    print()
    print("Sample database names:")
    rows = connection.execute(
        """
        SELECT id, name, province
        FROM weather_station
        ORDER BY id
        LIMIT 10
        """
    ).fetchall()

    for row in rows:
        print(dict(row))

    connection.close()


if __name__ == "__main__":
    main()