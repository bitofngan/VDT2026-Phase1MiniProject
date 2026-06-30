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


@app.get("/api/stations")
def get_stations(provinces: list[str] = Query(default=[])):
    conn = get_connection()
    cursor = conn.cursor()

    if provinces:
        placeholders = ",".join(["?"] * len(provinces))
        query = f"""
            SELECT
                id,
                name,
                province,
                latitude,
                longitude,
                elevation,
                flood_risk
            FROM telecom_stations
            WHERE province IN ({placeholders})
            LIMIT 10000
        """
        cursor.execute(query, provinces)
    else:
        cursor.execute("""
            SELECT
                id,
                name,
                province,
                latitude,
                longitude,
                elevation,
                flood_risk
            FROM telecom_stations
            LIMIT 10000
        """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/provinces")
def get_provinces():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT province
        FROM telecom_stations
        WHERE province IS NOT NULL
        ORDER BY province
    """)

    rows = cursor.fetchall()
    conn.close()
    return [row["province"] for row in rows]