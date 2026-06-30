from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "backend" / "database" / "flood_risk.db"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/forecast-times")
def get_forecast_times():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT forecast_time_vn
        FROM telecom_flood_risk_forecast
        WHERE forecast_time_vn IS NOT NULL
        ORDER BY forecast_time_vn
    """)

    rows = cursor.fetchall()
    conn.close()
    return [row["forecast_time_vn"] for row in rows]


@app.get("/api/stations/current")
def get_current_stations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
    """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/stations/forecast")
def get_forecast_stations(forecast_time_vn: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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

            rr.flood_risk,
            rr.risk_reason,
            rr.precip_3h_mm,
            rr.precip_24h_mm,
            rr.forecast_time_vn

        FROM telecom_station ts

        LEFT JOIN ranked_risk rr
            ON ts.id = rr.telecom_station_id
            AND rr.rn = 1

        ORDER BY ts.id
        LIMIT 10000
    """, (forecast_time_vn, forecast_time_vn))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/provinces")
def get_provinces():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT new_province AS province
        FROM telecom_station
        WHERE new_province IS NOT NULL
        ORDER BY new_province
    """)

    rows = cursor.fetchall()
    conn.close()
    return [row["province"] for row in rows]