import sqlite3
import os


DATABASE_FILE = "data/flood_warning.db"


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    return connection