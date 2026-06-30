from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

DATABASE_FILE = BACKEND_DIR / "database" / "flood_risk.db"

DATA_DIR = PROJECT_ROOT / "data"
WEATHER_FORECAST_DIR = PROJECT_ROOT / "weather_forecast_outputs"

WEATHER_STATION_CSV = DATA_DIR / "weather_stations.csv"
TELECOM_STATION_CSV = DATA_DIR / "telecom_stations_with_thresholds.csv"