from math import radians, sin, cos, sqrt, atan2


# Universal system rule, not station data.
MAX_RADIUS_KM = 30


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula.
    Output is in kilometres.
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
    Given a coordinate, find the closest weather station / forecast point.

    Input:
        latitude, longitude:
            target coordinate, for example a telecom station

        weather_stations:
            list of weather station dictionaries

    Output:
        dictionary with:
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

    if nearest_distance > MAX_RADIUS_KM:
        status = "outside_max_radius"
    else:
        status = "within_radius"

    return {
        "station": nearest_station,
        "distance_km": nearest_distance,
        "max_radius_km": MAX_RADIUS_KM,
        "status": status
    }