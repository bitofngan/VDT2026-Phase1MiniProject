import csv
import unicodedata
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

TELECOM_CSV = ROOT / "data" / "telecom_stations_with_thresholds.csv"
WEATHER_CSV = ROOT / "data" / "weather_stations.csv"


def ascii_province_name(name):
    text = str(name or "Unknown").strip()
    text = text.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = "_".join(text.split())
    return text


def rename_csv(input_file, output_file, prefix, province_column):
    with open(input_file, mode="r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    counters = defaultdict(int)

    for row in rows:
        province = row.get(province_column) or row.get("province") or "Unknown"
        province_name = ascii_province_name(province)

        counters[province_name] += 1
        new_id = f"{prefix}-{province_name}-{counters[province_name]:05d}"

        row["id"] = new_id
        row["name"] = f"{prefix} {province_name} {counters[province_name]:05d}"

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Renamed {len(rows)} rows:", output_file)


def main():
    rename_csv(
        input_file=TELECOM_CSV,
        output_file=TELECOM_CSV,
        prefix="TS",
        province_column="new_province",
    )

    rename_csv(
        input_file=WEATHER_CSV,
        output_file=WEATHER_CSV,
        prefix="WS",
        province_column="province",
    )


if __name__ == "__main__":
    main()