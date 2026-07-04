import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import re
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
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()

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

    return {
        "id": event_id,
        "name": entry.get("title") or "Unknown disaster event",
        "type": classify_event(entry),
        "status": "ACTIVE",
        "source": "GDACS",
        "severity": str(
            entry.get("gdacs_alertlevel")
            or entry.get("gdacs_alertlevel_text")
            or "UNKNOWN"
        ).upper(),
        "latitude": lat,
        "longitude": lng,
        "start_time_utc": entry.get("published") or entry.get("updated"),
        "last_update_utc": now_utc(),
        "description": entry.get("summary") or "",
        "url": entry.get("link") or "",
    }


def upsert_event(conn, event):
    conn.execute(
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
            status = 'ACTIVE',
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

    conn.execute(
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


def mark_missing_events_inactive(conn, active_ids):
    if not active_ids:
        conn.execute(
            """
            UPDATE disaster_event
            SET status = 'INACTIVE',
                last_update_utc = ?
            WHERE source = 'GDACS'
            """,
            (now_utc(),),
        )
        return

    placeholders = ",".join("?" for _ in active_ids)

    conn.execute(
        f"""
        UPDATE disaster_event
        SET status = 'INACTIVE',
            last_update_utc = ?
        WHERE source = 'GDACS'
        AND id NOT IN ({placeholders})
        """,
        [now_utc(), *active_ids],
    )

def parse_gdacs_end_date(description):
    match = re.search(r"lasting until (\d{2})/(\d{2})/(\d{4})", description or "")
    if not match:
        return None

    day, month, year = match.groups()
    return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)


def is_event_still_active(description):
    end_date = parse_gdacs_end_date(description)

    if end_date is None:
        return True

    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return end_date >= today


def main():
    feed = feedparser.parse(GDACS_RSS_URL)

    if getattr(feed, "bozo", False):
        raise RuntimeError(f"GDACS RSS parse error: {feed.bozo_exception}")

    conn = sqlite3.connect(DB_PATH)

    active_ids = []
    saved = 0

    for entry in feed.entries:
        event = parse_entry(entry)
        if not is_event_still_active(event["description"]):
            continue

        if not event["id"]:
            continue

        if event["type"] not in {"STORM", "FLOOD", "HEAVY_RAIN"}:
            continue

        if not is_near_vietnam(event["latitude"], event["longitude"]):
            continue

        upsert_event(conn, event)
        active_ids.append(event["id"])
        saved += 1

    mark_missing_events_inactive(conn, active_ids)

    conn.commit()
    conn.close()

    print(f"Saved {saved} active GDACS event(s) near Vietnam.")
    print(f"Marked missing GDACS events as INACTIVE.")


if __name__ == "__main__":
    main()