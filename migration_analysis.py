#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análise do Banco de Dados SQLite
Gera relatório completo antes da migração para Supabase
"""

import sqlite3
import os
from datetime import datetime
from collections import defaultdict

def analyze_database(db_path='database.db'):
    """Analisa o banco de dados SQLite e gera relatório detalhado."""
    
    if not os.path.exists(db_path):
        print(f"❌ Erro: Banco de dados '{db_path}' não encontrado!")
        return
    
    print("=" * 80)
    print("📊 ANÁLISE DO BANCO DE DADOS SQLITE")
    print("=" * 80)
    print(f"Arquivo: {db_path}")
    print(f"Tamanho: {os.path.getsize(db_path) / 1024:.2f} KB")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📋 TABELAS ENCONTRADAS: {len(tables)}")
    print("-" * 80)
    
    total_records = 0
    table_stats = {}
    
    for table in tables:
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_records += count
        
        # Obter informações das colunas
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        table_stats[table] = {
            'count': count,
            'columns': len(columns),
            'column_details': columns
        }
        
        print(f"\n✅ {table}")
        print(f"   Registros: {count:,}")
        print(f"   Colunas: {len(columns)}")
        
        # Mostrar primeiras 5 colunas
        for col in columns[:5]:
            col_id, col_name, col_type, not_null, default_val, pk = col
            pk_marker = " [PK]" if pk else ""
            null_marker = " NOT NULL" if not_null else ""
            print(f"      - {col_name} ({col_type}){pk_marker}{null_marker}")
        
        if len(columns) > 5:
            print(f"      ... e mais {len(columns) - 5} colunas")
    
    print("\n" + "=" * 80)
    print(f"📊 RESUMO GERAL")
    print("=" * 80)
    print(f"Total de Tabelas: {len(tables)}")
    print(f"Total de Registros: {total_records:,}")
    print()
    
    # 2. Verificar integridade referencial
    print("=" * 80)
    print("🔗 VERIFICAÇÃO DE INTEGRIDADE REFERENCIAL")
    print("=" * 80)
    
    integrity_issues = []
    
    # Verificar FK: estoque_detalhe -> item_estoque
    cursor.execute("""
        SELECT COUNT(*) FROM estoque_detalhe 
        WHERE item_estoque_id NOT IN (SELECT id FROM item_estoque)
    """)
    orphan_detalhes = cursor.fetchone()[0]
    if orphan_detalhes > 0:
        integrity_issues.append(f"⚠️  {orphan_detalhes} registros órfãos em estoque_detalhe")
    else:
        print("✅ estoque_detalhe -> item_estoque: OK")
    
    # Verificar FK: movimentacao -> item_estoque
    cursor.execute("""
        SELECT COUNT(*) FROM movimentacao 
        WHERE item_id NOT IN (SELECT id FROM item_estoque)
    """)
    orphan_movs = cursor.fetchone()[0]
    if orphan_movs > 0:
        integrity_issues.append(f"⚠️  {orphan_movs} registros órfãos em movimentacao")
    else:
        print("✅ movimentacao -> item_estoque: OK")
    
    # Verificar FK: movimentacao_consumivel -> consumivel_estoque
    cursor.execute("""
        SELECT COUNT(*) FROM movimentacao_consumivel 
        WHERE consumivel_id NOT IN (SELECT id FROM consumivel_estoque)
    """)
    orphan_cons_movs = cursor.fetchone()[0]
    if orphan_cons_movs > 0:
        integrity_issues.append(f"⚠️  {orphan_cons_movs} registros órfãos em movimentacao_consumivel")
    else:
        print("✅ movimentacao_consumivel -> consumivel_estoque: OK")
    
    if integrity_issues:
        print("\n⚠️  PROBLEMAS ENCONTRADOS:")
        for issue in integrity_issues:
            print(f"   {issue}")
    else:
        print("\n✅ Nenhum problema de integridade encontrado!")
    
    # 3. Estatísticas adicionais
    print("\n" + "=" * 80)
    print("📈 ESTATÍSTICAS DETALHADAS")
    print("=" * 80)
    
    # Usuários
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT role) FROM user")
    user_count, role_count = cursor.fetchone()
    print(f"\n👥 Usuários: {user_count}")
    cursor.execute("SELECT role, COUNT(*) FROM user GROUP BY role")
    for role, count in cursor.fetchall():
        print(f"   - {role}: {count}")
    
    # Itens de estoque
    cursor.execute("SELECT SUM(qtd_estoque), AVG(qtd_estoque), MAX(qtd_estoque) FROM item_estoque")
    total_qty, avg_qty, max_qty = cursor.fetchone()
    print(f"\n📦 Estoque Principal:")
    print(f"   - Quantidade Total: {total_qty:,.2f}")
    print(f"   - Média por Item: {avg_qty:,.2f}")
    print(f"   - Maior Quantidade: {max_qty:,.2f}")
    
    cursor.execute("SELECT COUNT(*) FROM item_estoque WHERE qtd_estoque = 0")
    zero_stock = cursor.fetchone()[0]
    print(f"   - Itens Zerados: {zero_stock}")
    
    # Lotes com validade
    cursor.execute("SELECT COUNT(*) FROM estoque_detalhe WHERE validade IS NOT NULL")
    lotes_com_validade = cursor.fetchone()[0]
    print(f"\n📅 Lotes com Validade: {lotes_com_validade}")
    
    cursor.execute("""
        SELECT COUNT(*) FROM estoque_detalhe 
        WHERE validade IS NOT NULL AND validade < date('now')
    """)
    lotes_vencidos = cursor.fetchone()[0]
    print(f"   - Vencidos: {lotes_vencidos}")
    
    # Movimentações
    cursor.execute("SELECT tipo, COUNT(*), SUM(quantidade) FROM movimentacao GROUP BY tipo")
    print(f"\n📊 Movimentações:")
    for tipo, count, total_qty in cursor.fetchall():
        print(f"   - {tipo}: {count:,} movimentações ({total_qty:,.2f} unidades)")
    
    # Consumíveis
    cursor.execute("SELECT SUM(quantidade_atual), COUNT(*) FROM consumivel_estoque")
    total_cons, count_cons = cursor.fetchone()
    if total_cons:
        print(f"\n🛠️  Consumíveis:")
        print(f"   - Total de Itens: {count_cons}")
        print(f"   - Quantidade Total: {total_cons:,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISE CONCLUÍDA!")
    print("=" * 80)
    print()
    print("📝 Próximos Passos:")
    print("   1. Revisar este relatório")
    print("   2. Corrigir problemas de integridade (se houver)")
    print("   3. Criar projeto no Supabase")
    print("   4. Executar migração com migrate_to_supabase.py")
    print()
    
    conn.close()
    
    return table_stats, integrity_issues

if __name__ == "__main__":
    analyze_database()
