import time
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.services.update_pipeline_service import update_weather_pipeline, update_all_data
from backend.services.disaster_update_service import update_disaster_events


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "backend" / "database" / "flood_risk.db"

REFRESH_COOLDOWN_SECONDS = 600

LAST_WEATHER_REFRESH_TS = 0
LAST_DISASTER_REFRESH_TS = 0


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/forecast-times")
def get_forecast_times():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT DISTINCT forecast_time_vn
        FROM telecom_flood_risk_forecast
        WHERE forecast_time_vn IS NOT NULL
        ORDER BY forecast_time_vn
        """
    ).fetchall()

    connection.close()
    return [row["forecast_time_vn"] for row in rows]


@app.get("/api/provinces")
def get_provinces():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT DISTINCT new_province AS province
        FROM telecom_station
        WHERE new_province IS NOT NULL
        ORDER BY new_province
        """
    ).fetchall()

    connection.close()
    return [row["province"] for row in rows]


@app.get("/api/stations/current")
def get_current_stations():
    connection = get_connection()

    rows = connection.execute(
        """
        WITH latest_current_weather AS (
            SELECT *
            FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY weather_station_id
                        ORDER BY fetched_at DESC
                    ) AS rn
                FROM weather_current_observation
            )
            WHERE rn = 1
        )
        SELECT
            ts.id,
            ts.name,
            ts.new_province AS province,
            ts.latitude,
            ts.longitude,
            ts.elevation_m,

            cw.temp_c AS current_temp_c,
            cw.wind_mps AS current_wind_mps,
            cw.precip_mm AS current_precip_mm,
            cw.humidity AS current_humidity,
            cw.pressure_mb AS current_pressure_mb,
            cw.condition_text AS current_condition,
            cw.last_updated AS current_weather_time

        FROM telecom_station ts
        LEFT JOIN telecom_weather_station_mapping m
            ON ts.id = m.telecom_station_id
        LEFT JOIN latest_current_weather cw
            ON m.weather_station_id = cw.weather_station_id
        ORDER BY ts.id
        LIMIT 10000
        """
    ).fetchall()

    connection.close()
    return rows_to_dicts(rows)


@app.get("/api/stations/forecast")
def get_forecast_stations(forecast_time_vn: str | None = None):
    connection = get_connection()

    rows = connection.execute(
        """
        WITH ranked_risk AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY telecom_station_id
                    ORDER BY
                        CASE flood_risk
                            WHEN 'HIGH' THEN 4
                            WHEN 'MEDIUM' THEN 3
                            WHEN 'LOW' THEN 2
                            WHEN 'SAFE' THEN 1
                            ELSE 0
                        END DESC,
                        precip_24h_mm DESC
                ) AS rn
            FROM telecom_flood_risk_forecast
            WHERE (? IS NULL OR forecast_time_vn = ?)
        )
        SELECT
            ts.id,
            ts.name,
            ts.new_province AS province,
            ts.latitude,
            ts.longitude,
            ts.elevation_m,

            rr.weather_station_id,
            ws.name AS weather_station_name,

            rr.flood_risk,
            rr.flood_risk AS risk_level,
            rr.risk_reason,
            rr.precip_3h_mm,
            rr.precip_3h_mm AS rain_3h_mm,
            rr.precip_24h_mm,
            rr.forecast_time_vn

        FROM telecom_station ts
        LEFT JOIN ranked_risk rr
            ON ts.id = rr.telecom_station_id
            AND rr.rn = 1
        LEFT JOIN weather_station ws
            ON rr.weather_station_id = ws.id
        ORDER BY ts.id
        LIMIT 10000
        """,
        (forecast_time_vn, forecast_time_vn),
    ).fetchall()

    connection.close()
    return rows_to_dicts(rows)


@app.get("/api/risk-forecast-table")
def get_risk_forecast_table():
    connection = get_connection()

    rows = connection.execute(
        """
        WITH ranked AS (
            SELECT
                r.telecom_station_id AS id,
                t.name AS name,
                t.new_province AS province,
                t.latitude,
                t.longitude,

                r.flood_risk,
                r.flood_risk AS risk_level,
                r.forecast_time_vn,

                r.precip_3h_mm,
                r.precip_3h_mm AS rain_3h_mm,
                r.precip_24h_mm,

                r.weather_station_id,
                COALESCE(w.name, r.weather_station_id) AS weather_station_name,
                r.risk_reason,

                ROW_NUMBER() OVER (
                    PARTITION BY r.telecom_station_id
                    ORDER BY
                        CASE r.flood_risk
                            WHEN 'HIGH' THEN 1
                            WHEN 'MEDIUM' THEN 2
                            WHEN 'LOW' THEN 3
                            WHEN 'SAFE' THEN 4
                            ELSE 5
                        END,
                        r.precip_24h_mm DESC,
                        r.forecast_time_vn
                ) AS rn

            FROM telecom_flood_risk_forecast r
            JOIN telecom_station t
                ON r.telecom_station_id = t.id
            LEFT JOIN weather_station w
                ON r.weather_station_id = w.id
            WHERE r.flood_risk != 'SAFE'
        )
        SELECT *
        FROM ranked
        WHERE rn = 1
        ORDER BY
            CASE flood_risk
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            province,
            id
        """
    ).fetchall()

    connection.close()
    return rows_to_dicts(rows)


@app.get("/api/disaster-events/active")
def get_active_disaster_events():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM disaster_event
        WHERE status = 'ACTIVE'
        ORDER BY last_update_utc DESC
        """
    ).fetchall()

    connection.close()
    return rows_to_dicts(rows)


@app.get("/api/disaster-events/history")
def get_disaster_event_history():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM disaster_event_history
        ORDER BY fetched_at_utc DESC
        LIMIT 500
        """
    ).fetchall()

    connection.close()
    return rows_to_dicts(rows)


@app.post("/api/admin/refresh-weather")
def refresh_weather():
    global LAST_WEATHER_REFRESH_TS

    now = time.time()

    if now - LAST_WEATHER_REFRESH_TS < REFRESH_COOLDOWN_SECONDS:
        remaining = int(REFRESH_COOLDOWN_SECONDS - (now - LAST_WEATHER_REFRESH_TS))
        raise HTTPException(
            status_code=429,
            detail=f"Refresh cooldown active. Try again in {remaining} seconds.",
        )

    LAST_WEATHER_REFRESH_TS = now

    try:
        return update_weather_pipeline()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/admin/refresh-disasters")
def refresh_disasters():
    global LAST_DISASTER_REFRESH_TS

    now = time.time()

    if now - LAST_DISASTER_REFRESH_TS < REFRESH_COOLDOWN_SECONDS:
        remaining = int(REFRESH_COOLDOWN_SECONDS - (now - LAST_DISASTER_REFRESH_TS))
        raise HTTPException(
            status_code=429,
            detail=f"Refresh cooldown active. Try again in {remaining} seconds.",
        )

    LAST_DISASTER_REFRESH_TS = now

    try:
        return update_disaster_events()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/admin/refresh-all")
def refresh_all():
    try:
        return update_all_data()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))