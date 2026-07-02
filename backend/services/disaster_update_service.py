import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from scripts.fetch_gdacs_events import main as fetch_gdacs_events_main


def update_disaster_events():
    fetch_gdacs_events_main()

    return {
        "success": True,
        "message": "Disaster events updated successfully.",
    }