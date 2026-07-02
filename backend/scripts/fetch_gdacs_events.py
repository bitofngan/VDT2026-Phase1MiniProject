import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import feedparser

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "flood_risk.db"

GDACS_RSS_URL = "https://www.gdacs.org/xml/rss.xml"

VIETNAM_BOUNDS = {
    "min_lat": 5.0,
    "max_lat": 25.0,
    "min_lng": 95.0,
    "max_lng": 125.0,
}

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None

def is_near_vietnam(lat, lng):
    if lat is None or lng is None:
        return False

    return (
        VIETNAM_BOUNDS["min_lat"] <= lat <= VIETNAM_BOUNDS["max_lat"]
        and VIETNAM_BOUNDS["min_lng"] <= lng <= VIETNAM_BOUNDS["max_lng"]
    )

def classify_event(entry):
    title = (entry.get("title") or "").lower()
    summary = (entry.get("summary") or "").lower()

    text = f"{title} {summary}"

    if "tropical cyclone" in text or "cyclone" in text or "typhoon" in text:
        return "STORM"
    if "flood" in text:
        return "FLOOD"
    if "heavy rain" in text:
        return "HEAVY_RAIN"

    return "OTHER"

def parse_entry(entry):
    lat = safe_float(entry.get("geo_lat"))
    lng = safe_float(entry.get("geo_long"))

    event_id = entry.get("id") or entry.get("guid") or entry.get("link")
    title = entry.get("title") or "Unknown disaster event"
    summary = entry.get("summary") or ""
    link = entry.get("link") or ""

    event_type = classify_event(entry)

    severity = (
        entry.get("gdacs_alertlevel")
        or entry.get("gdacs_alertlevel_text")
        or "UNKNOWN"
    )

    published = entry.get("published") or entry.get("updated") or None

    return {
        "id": event_id,
        "name": title,
        "type": event_type,
        "status": "ACTIVE",
        "source": "GDACS",
        "severity": str(severity).upper(),
        "latitude": lat,
        "longitude": lng,
        "start_time_utc": published,
        "last_update_utc": now_utc(),
        "description": summary,
        "url": link,
    }

def upsert_event(conn, event):
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO disaster_event (
            id, name, type, status, source, severity,
            latitude, longitude, start_time_utc, last_update_utc,
            description, url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            type = excluded.type,
            status = excluded.status,
            source = excluded.source,
            severity = excluded.severity,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            last_update_utc = excluded.last_update_utc,
            description = excluded.description,
            url = excluded.url
        """,
        (
            event["id"],
            event["name"],
            event["type"],
            event["status"],
            event["source"],
            event["severity"],
            event["latitude"],
            event["longitude"],
            event["start_time_utc"],
            event["last_update_utc"],
            event["description"],
            event["url"],
        ),
    )

    cur.execute(
        """
        INSERT INTO disaster_event_history (
            event_id, fetched_at_utc, name, type, status, source, severity,
            latitude, longitude, description, url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["id"],
            now_utc(),
            event["name"],
            event["type"],
            event["status"],
            event["source"],
            event["severity"],
            event["latitude"],
            event["longitude"],
            event["description"],
            event["url"],
        ),
    )

def main():
    feed = feedparser.parse(GDACS_RSS_URL)

    conn = sqlite3.connect(DB_PATH)

    saved = 0

    for entry in feed.entries:
        event = parse_entry(entry)

        if event["type"] not in {"STORM", "FLOOD", "HEAVY_RAIN"}:
            continue

        if not is_near_vietnam(event["latitude"], event["longitude"]):
            continue

        upsert_event(conn, event)
        saved += 1

    conn.commit()
    conn.close()

    print(f"Saved {saved} active disaster event(s) near Vietnam.")

if __name__ == "__main__":
    main()