from database.db_connection import get_connection


SCHEMA_FILE = "database/schema.sql"


def main():
    connection = get_connection()

    with open(SCHEMA_FILE, mode="r", encoding="utf-8") as file:
        schema_sql = file.read()

    connection.executescript(schema_sql)
    connection.commit()
    connection.close()

    print("Database initialized successfully.")
    print("Created database file: data/flood_warning.db")


if __name__ == "__main__":
    main()