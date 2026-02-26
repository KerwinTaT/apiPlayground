import sqlite3
from src.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables:")
for t in tables:
    print(t[0])

for t in tables:
    print(f"\nSchema for table: {t[0]}")
    cursor.execute(f"PRAGMA table_info({t[0]});")
    for col in cursor.fetchall():
        print(col)

conn.close()