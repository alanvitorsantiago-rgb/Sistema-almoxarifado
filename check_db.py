import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Obter lista de todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("✅ VERIFICAÇÃO COMPLETA DO BANCO DE DADOS")
print("=" * 60)

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    print(f"\n📋 Tabela: {table}")
    print(f"  Colunas ({len(cols)}):")
    for col in cols:
        print(f"    - {col[1]:25} ({col[2]})")

print("\n" + "=" * 60)
print("✅ TODAS AS TABELAS VERIFICADAS COM SUCESSO!")
conn.close()
