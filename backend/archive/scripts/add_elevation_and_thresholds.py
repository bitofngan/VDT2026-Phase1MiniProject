import csv
import os
import sys
import time
import requests


# Open-Meteo allows maximum 100 coordinate pairs per request.
ELEVATION_BATCH_SIZE = 100

# Wait between successful requests to reduce rate-limit risk.
ELEVATION_DELAY_SECONDS = 15

MAX_ELEVATION_RETRIES = 5


def read_csv(filename):
    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def generate_thresholds_from_elevation(elevation_m):
    """
    Basic placeholder rainfall thresholds based on elevation.

    Lower elevation = more flood-prone.
    Higher elevation = less flood-prone.

    Returns:
        low_rain_threshold_mm,
        medium_rain_threshold_mm,
        high_rain_threshold_mm
    """

    if elevation_m is None:
        return 80, 150, 200

    if elevation_m < 10:
        return 40, 80, 120

    if elevation_m < 50:
        return 60, 120, 180

    if elevation_m < 200:
        return 80, 150, 220

    if elevation_m < 700:
        return 100, 180, 260

    return 120, 220, 320


def add_thresholds_to_row(row):
    elevation_text = row.get("elevation_m", "")

    if elevation_text == "" or elevation_text is None:
        elevation_m = None
    else:
        elevation_m = float(elevation_text)

    low, medium, high = generate_thresholds_from_elevation(elevation_m)

    row["low_rain_threshold_mm"] = low
    row["medium_rain_threshold_mm"] = medium
    row["high_rain_threshold_mm"] = high

    return row


def write_csv(rows, filename):
    if not rows:
        print("No rows to write:", filename)
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


def fetch_elevation_for_batch(batch):
    latitudes = ",".join(str(row["latitude"]) for row in batch)
    longitudes = ",".join(str(row["longitude"]) for row in batch)

    url = "https://api.open-meteo.com/v1/elevation"

    params = {
        "latitude": latitudes,
        "longitude": longitudes
    }

    for attempt in range(1, MAX_ELEVATION_RETRIES + 1):
        response = requests.get(url, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()

            if data.get("error") is True:
                reason = data.get("reason", "Unknown API error")
                print(f"Elevation API error on attempt {attempt}: {reason}")

                if "daily api request limit exceeded" in reason.lower():
                    raise RuntimeError("Daily elevation API limit exceeded")

                if "limit" in reason.lower():
                    print("Rate limit hit. Waiting 70 seconds before retrying...")
                    time.sleep(70)
                    continue

                raise RuntimeError(f"Elevation API error: {reason}")

            elevations = data.get("elevation", [])

            if len(elevations) != len(batch):
                raise RuntimeError("Elevation API returned unexpected number of results")

            return elevations

        print(f"Elevation API HTTP error {response.status_code} on attempt {attempt}")
        print(response.text)

        try:
            data = response.json()
            reason = data.get("reason", "")
        except Exception:
            reason = ""

        if "daily api request limit exceeded" in reason.lower():
            raise RuntimeError("Daily elevation API limit exceeded")

        if response.status_code == 429:
            print("Rate limit hit. Waiting 70 seconds before retrying...")
            time.sleep(70)
        else:
            time.sleep(10)

    raise RuntimeError("Failed to fetch elevation after retries")


def fetch_elevations(rows):
    """
    Fetch elevation in batches.

    If the daily limit is reached, the script saves progress so far.
    Rows without elevation will receive default thresholds.
    """

    for start in range(0, len(rows), ELEVATION_BATCH_SIZE):
        batch = rows[start:start + ELEVATION_BATCH_SIZE]

        print(f"Fetching elevation for rows {start + 1} to {start + len(batch)}...")

        try:
            elevations = fetch_elevation_for_batch(batch)

            for row, elevation in zip(batch, elevations):
                if elevation is None:
                    row["elevation_m"] = ""
                else:
                    row["elevation_m"] = round(float(elevation), 2)

            print(f"Fetched elevation for rows {start + 1} to {start + len(batch)}")

        except RuntimeError as error:
            print()
            print("Stopped fetching elevation:")
            print(error)
            print()
            print("The script will still export the CSV.")
            print("Rows without elevation will use default thresholds.")
            print()
            break

        time.sleep(ELEVATION_DELAY_SECONDS)

    for row in rows:
        add_thresholds_to_row(row)

    return rows


def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("python add_elevation_and_threshold.py <input_csv> <output_csv>")
        print()
        print("Example:")
        print(
            "python .\\add_elevation_and_thresholds.py "
            "data\\telecom_stations_part_1.csv "
            "data\\telecom_stations_part_1_with_thresholds.csv"
        )
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print("Input CSV:", os.path.abspath(input_file))
    print("Output CSV:", os.path.abspath(output_file))

    rows = read_csv(input_file)

    print("Loaded rows:", len(rows))

    rows = fetch_elevations(rows)

    write_csv(rows, output_file)

    print("Done.")


if __name__ == "__main__":
    main()