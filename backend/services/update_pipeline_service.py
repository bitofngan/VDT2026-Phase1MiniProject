from backend.services.weather_update_service import update_weather_forecasts
from backend.services.flood_risk_service import update_flood_risk
from backend.services.disaster_update_service import update_disaster_events


def update_weather_pipeline():
    weather_result = update_weather_forecasts()
    flood_result = update_flood_risk()

    return {
        "success": True,
        "message": "Weather forecast and flood risk updated successfully.",
        "weather": weather_result,
        "flood_risk": flood_result,
    }


def update_all_data():
    weather_result = update_weather_pipeline()
    disaster_result = update_disaster_events()

    return {
        "success": True,
        "message": "All data updated successfully.",
        "weather_pipeline": weather_result,
        "disasters": disaster_result,
    }