#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import re

# Conectar ao banco de dados
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Consultar itens sem descrição ou com descrição inválida
cursor.execute("""
    SELECT codigo, descricao, id FROM item_estoque 
    WHERE descricao IS NULL 
    OR descricao = '' 
    OR descricao = '-' 
    OR descricao = '='
    ORDER BY codigo
""")

items_sem_descricao = cursor.fetchall()

print(f"Itens sem descrição válida: {len(items_sem_descricao)}")
print("-" * 80)

if items_sem_descricao:
    for codigo, descricao, item_id in items_sem_descricao:
        status = "vazio" if descricao == "" else (f"inválido: '{descricao}'" if descricao else "NULL")
        print(f"ID: {item_id} | Código: {codigo} | Status: {status}")
else:
    print("✓ Todos os itens têm descrição válida!")

print("-" * 80)

# Estatísticas
cursor.execute("SELECT COUNT(*) FROM item_estoque")
total = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM item_estoque 
    WHERE descricao IS NOT NULL 
    AND descricao != '' 
    AND descricao != '-' 
    AND descricao != '='
""")
com_descricao = cursor.fetchone()[0]

print(f"\nResumo:")
print(f"Total de itens: {total}")
print(f"Com descrição válida: {com_descricao}")
print(f"Sem descrição válida: {len(items_sem_descricao)}")
print(f"Cobertura: {(com_descricao/total*100):.1f}%")

conn.close()
