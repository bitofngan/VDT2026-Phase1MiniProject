from math import radians, sin, cos, sqrt, atan2


# For proof-of-concept, 100 km is reasonable because these are forecast points,
# not dense physical weather stations.
MAX_RADIUS_KM = 100


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two latitude/longitude coordinates.

    Returns:
        distance in kilometres
    """

    earth_radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def find_nearest_weather_station(latitude, longitude, weather_stations):
    """
    Find the nearest weather station / forecast point for one coordinate.

    Input:
        latitude, longitude:
            telecom station coordinate

        weather_stations:
            list loaded from data/weather_stations.csv

    Output:
        dictionary containing:
            station
            distance_km
            max_radius_km
            status
    """

    if not weather_stations:
        return {
            "station": None,
            "distance_km": None,
            "max_radius_km": MAX_RADIUS_KM,
            "status": "no_weather_stations_available"
        }

    nearest_station = None
    nearest_distance = float("inf")

    for station in weather_stations:
        distance = haversine_distance_km(
            latitude,
            longitude,
            station["latitude"],
            station["longitude"]
        )

        if distance < nearest_distance:
            nearest_station = station
            nearest_distance = distance

    if nearest_distance <= MAX_RADIUS_KM:
        status = "within_radius"
    else:
        status = "outside_max_radius"

    return {
        "station": nearest_station,
        "distance_km": nearest_distance,
        "max_radius_km": MAX_RADIUS_KM,
        "status": status
    }