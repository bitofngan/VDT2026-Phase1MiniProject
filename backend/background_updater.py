import logging
import threading
import time

from backend.services.update_pipeline_service import update_weather_pipeline

UPDATE_INTERVAL_SECONDS = 180 * 60


def updater_loop():
    logging.info("Background weather updater started.")

    while True:
        try:
            logging.info("Running scheduled weather update...")
            update_weather_pipeline()
            logging.info("Scheduled weather update completed.")
        except Exception:
            logging.exception("Scheduled weather update failed.")

        time.sleep(UPDATE_INTERVAL_SECONDS)


def start_background_updater():
    thread = threading.Thread(
        target=updater_loop,
        daemon=True,
        name="WeatherUpdater",
    )
    thread.start()