import csv
import os


PART_1_FILE = "data/telecom_stations_part_1_with_thresholds.csv"
PART_2_FILE = "data/telecom_stations_part_2_with_thresholds.csv"

OUTPUT_FILE = "data/telecom_stations_with_thresholds.csv"


def read_csv(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Missing file: {filename}")

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(rows, filename):
    if not rows:
        print("No rows to write.")
        return

    output_folder = os.path.dirname(filename)

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)

    fieldnames = [
        "id",
        "name",
        "latitude",
        "longitude",
        "old_province",
        "new_province",
        "province_mapping_status",
        "elevation_m",
        "low_rain_threshold_mm",
        "medium_rain_threshold_mm",
        "high_rain_threshold_mm",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            cleaned_row = {}

            for field in fieldnames:
                cleaned_row[field] = row.get(field, "")

            writer.writerow(cleaned_row)

    print("Saved:", filename)


def main():
    print("Reading part 1:", PART_1_FILE)
    part_1 = read_csv(PART_1_FILE)

    print("Reading part 2:", PART_2_FILE)
    part_2 = read_csv(PART_2_FILE)

    rows = part_1 + part_2

    # Keep BTS_00001, BTS_00002, ... order.
    rows.sort(key=lambda row: row["id"])

    write_csv(rows, OUTPUT_FILE)

    print()
    print("Part 1 rows:", len(part_1))
    print("Part 2 rows:", len(part_2))
    print("Total rows:", len(rows))
    print("Final merged file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()