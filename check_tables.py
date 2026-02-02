import sqlite3

# Verificar as tabelas no banco atual
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("Tabelas no banco atual:")
for table in tables:
    print(f"  - {table}")

conn.close()
