DROP TABLE IF EXISTS telecom_flood_risk_forecast;
DROP TABLE IF EXISTS telecom_weather_station_mapping;
DROP TABLE IF EXISTS weather_forecast;
DROP TABLE IF EXISTS telecom_station;
DROP TABLE IF EXISTS weather_station;

CREATE TABLE weather_station (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    province TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE telecom_station (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    old_province TEXT,
    new_province TEXT,
    province_mapping_status TEXT,
    elevation_m REAL,
    low_rain_threshold_24h_mm REAL,
    medium_rain_threshold_24h_mm REAL,
    high_rain_threshold_24h_mm REAL
);

CREATE TABLE weather_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weather_station_id TEXT NOT NULL,
    forecast_time_utc TEXT NOT NULL,
    forecast_time_vn TEXT NOT NULL,
    temperature_c REAL,
    wind_speed_mps REAL,
    precip_3h_mm REAL NOT NULL,
    FOREIGN KEY (weather_station_id) REFERENCES weather_station(id)
);

CREATE TABLE telecom_weather_station_mapping (
    telecom_station_id TEXT PRIMARY KEY,
    weather_station_id TEXT NOT NULL,
    distance_km REAL NOT NULL,
    max_radius_km REAL NOT NULL,
    radius_status TEXT NOT NULL CHECK (
        radius_status IN ('within_radius', 'outside_max_radius')
    ),
    FOREIGN KEY (telecom_station_id) REFERENCES telecom_station(id),
    FOREIGN KEY (weather_station_id) REFERENCES weather_station(id)
);

CREATE TABLE telecom_flood_risk_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telecom_station_id TEXT NOT NULL,
    weather_station_id TEXT NOT NULL,
    forecast_time_utc TEXT NOT NULL,
    forecast_time_vn TEXT NOT NULL,
    temperature_c REAL,
    wind_speed_mps REAL,
    precip_3h_mm REAL NOT NULL,
    avg_precip_1h_mm REAL NOT NULL,
    precip_24h_mm REAL NOT NULL,
    estimated_1h_high_threshold_mm REAL NOT NULL,
    exceed_1h_threshold INTEGER NOT NULL CHECK (
        exceed_1h_threshold IN (0, 1)
    ),
    exceed_24h_threshold INTEGER NOT NULL CHECK (
        exceed_24h_threshold IN (0, 1)
    ),
    flood_risk TEXT NOT NULL CHECK (
        flood_risk IN ('SAFE', 'LOW', 'MEDIUM', 'HIGH')
    ),
    risk_reason TEXT NOT NULL,
    FOREIGN KEY (telecom_station_id) REFERENCES telecom_station(id),
    FOREIGN KEY (weather_station_id) REFERENCES weather_station(id)
);

CREATE TABLE IF NOT EXISTS weather_current_observation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weather_station_id TEXT NOT NULL,
    observation_time TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    temp_c REAL,
    wind_kph REAL,
    wind_mps REAL,
    precip_mm REAL,
    humidity INTEGER,
    pressure_mb REAL,
    condition_text TEXT,
    source TEXT NOT NULL DEFAULT 'WeatherAPI',
    fetched_at TEXT NOT NULL,
    FOREIGN KEY (weather_station_id) REFERENCES weather_station(id)
);