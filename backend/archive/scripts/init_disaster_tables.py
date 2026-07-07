import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "flood_risk.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS disaster_event (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        source TEXT,
        severity TEXT,
        latitude REAL,
        longitude REAL,
        start_time_utc TEXT,
        last_update_utc TEXT,
        description TEXT,
        url TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS disaster_event_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        fetched_at_utc TEXT NOT NULL,
        name TEXT,
        type TEXT,
        status TEXT,
        source TEXT,
        severity TEXT,
        latitude REAL,
        longitude REAL,
        description TEXT,
        url TEXT,
        FOREIGN KEY (event_id) REFERENCES disaster_event(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Disaster tables initialized:", DB_PATH)

if __name__ == "__main__":
    main()