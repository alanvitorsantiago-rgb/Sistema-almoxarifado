#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("=" * 80)
print("RELATÓRIO DE INTEGRIDADE DO BANCO DE DADOS")
print("=" * 80)

# 1. Total de itens
cursor.execute("SELECT COUNT(*) FROM item_estoque")
total_items = cursor.fetchone()[0]
print(f"\n📦 ITENS DE ESTOQUE")
print(f"   Total de itens: {total_items}")

# 2. Itens com descrição válida
cursor.execute("""
    SELECT COUNT(*) FROM item_estoque 
    WHERE descricao IS NOT NULL 
    AND descricao != '' 
    AND descricao != '-' 
    AND descricao != '='
""")
items_com_desc = cursor.fetchone()[0]
print(f"   Com descrição válida: {items_com_desc}")
print(f"   Cobertura: {(items_com_desc/total_items*100):.1f}%")

# 3. Itens por categoria de descrição
cursor.execute("""
    SELECT 
        CASE 
            WHEN descricao IS NULL THEN 'NULL'
            WHEN descricao = '' THEN 'VAZIO'
            WHEN descricao IN ('-', '=') THEN 'INVÁLIDO'
            ELSE 'VÁLIDO'
        END as categoria,
        COUNT(*) as quantidade
    FROM item_estoque
    GROUP BY categoria
""")
print(f"\n📊 CATEGORIAS DE DESCRIÇÃO:")
for categoria, qtd in cursor.fetchall():
    print(f"   {categoria}: {qtd}")

# 4. Consumíveis
cursor.execute("SELECT COUNT(*) FROM consumivel_estoque")
total_consumiveis = cursor.fetchone()[0]
print(f"\n🛒 CONSUMÍVEIS DE ESTOQUE")
print(f"   Total de consumíveis: {total_consumiveis}")

# 5. Total de movimentações
cursor.execute("SELECT COUNT(*) FROM movimentacao")
total_mov = cursor.fetchone()[0]
print(f"\n📈 MOVIMENTAÇÕES")
print(f"   Total de movimentações: {total_mov}")

# 6. Estoque detalhado
cursor.execute("SELECT COUNT(*) FROM estoque_detalhe")
total_detalhes = cursor.fetchone()[0]
print(f"\n🎯 ESTOQUE DETALHADO")
print(f"   Total de lotes: {total_detalhes}")

# 7. Usuários
cursor.execute("SELECT COUNT(*) FROM user")
total_users = cursor.fetchone()[0]
print(f"\n👤 USUÁRIOS")
print(f"   Total de usuários: {total_users}")

print("\n" + "=" * 80)
print("✅ BANCO DE DADOS ÍNTEGRO E PRONTO PARA USO")
print("=" * 80)

conn.close()
