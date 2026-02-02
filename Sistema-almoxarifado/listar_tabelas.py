#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("Tabelas disponíveis:")
for table in tables:
    print(f"  - {table}")

conn.close()
