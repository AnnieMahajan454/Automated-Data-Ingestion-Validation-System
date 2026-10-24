import sqlite3

conn = sqlite3.connect('pipeline.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"\n📊 {len(tables)} tables found:\n")

for t in tables:
    try:
        count = cursor.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"  {t[0]:25} → {count} rows")
    except:
        print(f"  {t[0]:25} → error")

conn.close()
print("\n✅ Done!")