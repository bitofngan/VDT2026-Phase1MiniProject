import csv
import os
import random
import unicodedata
import geopandas as gpd
from shapely.geometry import Point


# ============================================================
# Config
# ============================================================

ADM1_FILE = "data/vietnam_adm1.geojson"
OUTPUT_FILE = "data/telecom_stations.csv"

NUMBER_OF_TELECOM_STATIONS = 10000

# Use a number for repeatable fake data.
# Use None for different random data every run.
RANDOM_SEED = 42


# ============================================================
# Possible province-name columns in ADM1 GeoJSON
# ============================================================

POSSIBLE_PROVINCE_COLUMNS = [
    "shapeName",
    "NAME_1",
    "name",
    "Name",
    "ADM1_EN",
    "ADM1_VI",
    "province",
    "Province",
]


# ============================================================
# Old province to new 2025 province mapping
# ============================================================

OLD_TO_NEW_PROVINCE = {
    # Unchanged / current 2025 units
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",

    "hue": "Huế",
    "thua thien hue": "Huế",

    "lai chau": "Lai Châu",
    "dien bien": "Điện Biên",
    "son la": "Sơn La",
    "lang son": "Lạng Sơn",
    "cao bang": "Cao Bằng",
    "quang ninh": "Quảng Ninh",
    "thanh hoa": "Thanh Hóa",
    "nghe an": "Nghệ An",
    "ha tinh": "Hà Tĩnh",

    # Merged units
    "tuyen quang": "Tuyên Quang",
    "ha giang": "Tuyên Quang",

    "lao cai": "Lào Cai",
    "yen bai": "Lào Cai",

    "thai nguyen": "Thái Nguyên",
    "bac kan": "Thái Nguyên",
    "backan": "Thái Nguyên",

    "phu tho": "Phú Thọ",
    "vinh phuc": "Phú Thọ",
    "hoa binh": "Phú Thọ",

    "bac ninh": "Bắc Ninh",
    "bac giang": "Bắc Ninh",

    "hung yen": "Hưng Yên",
    "thai binh": "Hưng Yên",

    "hai phong": "Hải Phòng",
    "haiphong": "Hải Phòng",
    "hai duong": "Hải Phòng",

    "ninh binh": "Ninh Bình",
    "nam dinh": "Ninh Bình",
    "ha nam": "Ninh Bình",

    "quang tri": "Quảng Trị",
    "quang binh": "Quảng Trị",

    "da nang": "Đà Nẵng",
    "danang": "Đà Nẵng",
    "quang nam": "Đà Nẵng",

    "quang ngai": "Quảng Ngãi",
    "kon tum": "Quảng Ngãi",
    "kontum": "Quảng Ngãi",

    "gia lai": "Gia Lai",
    "binh dinh": "Gia Lai",

    "khanh hoa": "Khánh Hòa",
    "ninh thuan": "Khánh Hòa",

    "lam dong": "Lâm Đồng",
    "dak nong": "Lâm Đồng",
    "dac nong": "Lâm Đồng",
    "binh thuan": "Lâm Đồng",

    "dak lak": "Đắk Lắk",
    "dac lak": "Đắk Lắk",
    "daklak": "Đắk Lắk",
    "phu yen": "Đắk Lắk",

    "ho chi minh city": "TPHCM",
    "ho chi minh": "TPHCM",
    "hcmc": "TPHCM",
    "tp ho chi minh": "TPHCM",
    "thanh pho ho chi minh": "TPHCM",
    "binh duong": "TPHCM",
    "ba ria vung tau": "TPHCM",
    "baria vungtau": "TPHCM",

    "dong nai": "Đồng Nai",
    "binh phuoc": "Đồng Nai",

    "tay ninh": "Tây Ninh",
    "long an": "Tây Ninh",

    "can tho": "Cần Thơ",
    "cantho": "Cần Thơ",
    "soc trang": "Cần Thơ",
    "hau giang": "Cần Thơ",

    "vinh long": "Vĩnh Long",
    "ben tre": "Vĩnh Long",
    "tra vinh": "Vĩnh Long",

    "dong thap": "Đồng Tháp",
    "tien giang": "Đồng Tháp",

    "ca mau": "Cà Mau",
    "bac lieu": "Cà Mau",

    "an giang": "An Giang",
    "kien giang": "An Giang",

    # Special case from your ADM1 file
    "con dao": "Thành phố Hồ Chí Minh",
}


# ============================================================
# Province helpers
# ============================================================

def normalize_name(name):
    """
    Normalize province names for easier matching.

    Examples:
        "Bình Dương" -> "binh duong"
        "Bà Rịa–Vũng Tàu" -> "ba ria vung tau"
        "Hà Tĩnh" -> "ha tinh"
    """

    if name is None:
        return ""

    text = str(name).strip().lower()

    text = text.replace("đ", "d").replace("Đ", "d")

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace("—", " ")
    text = text.replace("_", " ")
    text = text.replace(".", " ")
    text = text.replace(",", " ")

    text = text.replace("province", "")
    text = text.replace("city", "")

    text = " ".join(text.split())

    return text


def map_old_to_new_province(old_province):
    key = normalize_name(old_province)

    if key in OLD_TO_NEW_PROVINCE:
        return OLD_TO_NEW_PROVINCE[key], "mapped"

    return str(old_province), "unmapped"


# ============================================================
# Load ADM1 polygons
# ============================================================

def find_province_column(gdf):
    for column in POSSIBLE_PROVINCE_COLUMNS:
        if column in gdf.columns:
            return column

    print("Available columns in your ADM1 file:")
    print(list(gdf.columns))

    raise ValueError(
        "Could not find province-name column. "
        "Add the correct column name to POSSIBLE_PROVINCE_COLUMNS."
    )


def load_adm1_polygons(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Cannot find ADM1 file: {filename}")

    gdf = gpd.read_file(filename)

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    province_column = find_province_column(gdf)

    cleaned = gdf[[province_column, "geometry"]].copy()
    cleaned = cleaned.rename(columns={province_column: "old_province"})

    cleaned["old_province"] = cleaned["old_province"].astype(str)

    mapped_results = cleaned["old_province"].apply(map_old_to_new_province)
    cleaned["new_province"] = mapped_results.apply(lambda x: x[0])
    cleaned["province_mapping_status"] = mapped_results.apply(lambda x: x[1])

    cleaned = cleaned[cleaned.geometry.notnull()]
    cleaned = cleaned[~cleaned.geometry.is_empty]

    print("Using province column:", province_column)
    print("Loaded ADM1 polygons:", len(cleaned))

    unmapped = sorted(
        set(
            cleaned.loc[
                cleaned["province_mapping_status"] == "unmapped",
                "old_province"
            ]
        )
    )

    if unmapped:
        print()
        print("Warning: these old province names were NOT mapped:")
        for name in unmapped:
            print("-", name)
        print()

    return cleaned


# ============================================================
# Generate fake telecom stations
# ============================================================

def random_point_in_polygon(polygon):
    minx, miny, maxx, maxy = polygon.bounds

    while True:
        longitude = random.uniform(minx, maxx)
        latitude = random.uniform(miny, maxy)

        point = Point(longitude, latitude)

        if polygon.covers(point):
            return point


def generate_fake_coordinates_from_adm1(adm1_gdf, count):
    stations = []

    try:
        projected = adm1_gdf.to_crs("EPSG:3405")
        weights = projected.geometry.area.tolist()
    except Exception:
        weights = None

    records = adm1_gdf.to_dict("records")

    for i in range(1, count + 1):
        province_record = random.choices(records, weights=weights, k=1)[0]
        point = random_point_in_polygon(province_record["geometry"])

        station = {
            "id": f"BTS_{i:05d}",
            "name": f"Fake Telecom Station {i:05d}",
            "latitude": round(point.y, 6),
            "longitude": round(point.x, 6),
            "old_province": province_record["old_province"],
            "new_province": province_record["new_province"],
            "province_mapping_status": province_record["province_mapping_status"],
        }

        stations.append(station)

        if i % 1000 == 0:
            print(f"Generated {i} telecom station coordinates...")

    return stations


# ============================================================
# Export
# ============================================================

def export_to_csv(stations, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    fieldnames = [
        "id",
        "name",
        "latitude",
        "longitude",
        "old_province",
        "new_province",
        "province_mapping_status",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stations)

    print(f"Saved {len(stations)} fake telecom stations to {filename}")


# ============================================================
# Main
# ============================================================

def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    print("ADM1 file:", os.path.abspath(ADM1_FILE))
    print("Output CSV:", os.path.abspath(OUTPUT_FILE))

    print("Loading ADM1 province polygons...")
    adm1_gdf = load_adm1_polygons(ADM1_FILE)

    print("Generating fake telecom station coordinates...")
    stations = generate_fake_coordinates_from_adm1(
        adm1_gdf,
        NUMBER_OF_TELECOM_STATIONS
    )

    export_to_csv(stations, OUTPUT_FILE)

    print("First 5 stations:")
    for station in stations[:5]:
        print(station)


if __name__ == "__main__":
    main()