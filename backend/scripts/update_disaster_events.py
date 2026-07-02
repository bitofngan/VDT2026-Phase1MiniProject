import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from services.disaster_update_service import update_disaster_events


def main():
    result = update_disaster_events()
    print(result)


if __name__ == "__main__":
    main()