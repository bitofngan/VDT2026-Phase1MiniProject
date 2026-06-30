import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.append(str(BACKEND_DIR))

from database.db_connection import get_connection, DATABASE_FILE


SCHEMA_FILE = BACKEND_DIR / "database" / "schema.sql"


def main():
    connection = get_connection()

    with open(SCHEMA_FILE, mode="r", encoding="utf-8") as file:
        schema_sql = file.read()

    connection.executescript(schema_sql)
    connection.commit()
    connection.close()

    print("Database initialized successfully.")
    print("Created database file:", DATABASE_FILE)


if __name__ == "__main__":
    main()