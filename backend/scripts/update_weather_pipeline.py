import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from services.update_pipeline_service import update_weather_pipeline


def main():
    result = update_weather_pipeline()
    print(result)


if __name__ == "__main__":
    main()