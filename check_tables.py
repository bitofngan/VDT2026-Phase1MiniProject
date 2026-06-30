import sqlite3
from pathlib import Path

for db_path in Path(".").rglob("*.db"):
    print("\nDB:", db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """).fetchall()

    if not tables:
        print("  No tables")
    else:
        for table in tables:
            print(" ", table[0])

    conn.close()