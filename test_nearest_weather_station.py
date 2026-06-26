from weather_station_loader import load_weather_stations_from_csv
from nearest_weather_station import find_nearest_weather_station


weather_stations = load_weather_stations_from_csv("data/weather_stations.csv")

target_point = {
    "name": "Example Telecom Station",
    "latitude": 21.0300,
    "longitude": 105.8500
}

result = find_nearest_weather_station(
    target_point["latitude"],
    target_point["longitude"],
    weather_stations
)

print("Target point:", target_point["name"])

if result["station"] is None:
    print("No weather station found")
else:
    print("Nearest weather station:", result["station"]["name"])
    print("Distance km:", result["distance_km"])
    print("Max radius km:", result["max_radius_km"])
    print("Status:", result["status"])