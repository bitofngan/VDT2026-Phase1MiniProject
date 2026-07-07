import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    print("\nRunning:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["real", "simulate"],
        default="real",
        help="real = fetch Windy data, simulate = generate storm demo data",
    )

    args = parser.parse_args()

    if args.mode == "real":
        run([sys.executable, "backend/scripts/fetch_weather_forecasts.py"])

    if args.mode == "simulate":
        run([sys.executable, "backend/scripts/simulate_weather_forecasts.py"])

    run([sys.executable, "backend/scripts/import_csv_to_database.py"])
    run([sys.executable, "backend/scripts/calculate_telecom_flood_risk_db.py"])
    run([sys.executable, "backend/scripts/check_database_results.py"])

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()