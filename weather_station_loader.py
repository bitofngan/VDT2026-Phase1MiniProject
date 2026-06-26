import csv


def load_weather_stations_from_csv(filename):
    """
    Load weather stations / forecast points from a CSV file.

    Expected CSV columns:
    id,name,province,latitude,longitude

    encoding="utf-8-sig" handles CSV files saved by Excel with BOM.
    """

    weather_stations = []

    with open(filename, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        print("CSV columns found:", reader.fieldnames)

        required_columns = ["id", "name", "province", "latitude", "longitude"]

        for column in required_columns:
            if column not in reader.fieldnames:
                raise ValueError(
                    f"Missing required column '{column}'. "
                    f"Found columns: {reader.fieldnames}"
                )

        for row in reader:
            station = {
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                "province": row["province"].strip(),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"])
            }

            weather_stations.append(station)

    return weather_stations