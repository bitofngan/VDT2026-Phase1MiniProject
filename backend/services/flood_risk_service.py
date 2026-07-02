import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from scripts.calculate_telecom_flood_risk_db import main as calculate_flood_risk_main


def update_flood_risk():
    calculate_flood_risk_main()

    return {
        "success": True,
        "message": "Flood risk recalculated successfully.",
    }