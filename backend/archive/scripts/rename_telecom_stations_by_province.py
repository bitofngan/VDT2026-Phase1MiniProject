import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = PROJECT_ROOT / "data" / "telecom_stations_with_thresholds.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "telecom_stations_with_thresholds.csv"


SPECIAL_CODES = {
    "Hà Nội": "HN",
    "TPHCM": "TPHCM",
    "Đà Nẵng": "DN",
    "Huế": "HUE",
}


def normalize_text(text):
    text = str(text).strip()
    text = text.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    return " ".join(text.upper().split())


def province_code(province):
    if province in SPECIAL_CODES:
        return SPECIAL_CODES[province]

    words = normalize_text(province).split()

    if len(words) == 1:
        return words[0][:3]

    return "".join(word[0] for word in words)


def main():
    with open(INPUT_CSV, mode="r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    counters = defaultdict(int)

    for row in rows:
        province = row.get("new_province") or row.get("old_province") or "UNKNOWN"
        code = province_code(province)

        counters[code] += 1

        new_id = f"{code}-{counters[code]:05d}"
        row["id"] = new_id
        row["name"] = f"Telecom Station {new_id}"

    fieldnames = rows[0].keys()

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Renamed telecom stations:", len(rows))
    print("Saved:", OUTPUT_CSV)


if __name__ == "__main__":
    main()