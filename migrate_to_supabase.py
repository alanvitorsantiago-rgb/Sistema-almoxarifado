#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Migração SQLite → Supabase PostgreSQL
Migra todos os dados mantendo integridade referencial
"""

import sqlite3
import os
from datetime import datetime
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://twydlslxhtoqsqnixcmz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3eWRsc2x4aHRvcXNxbml4Y216Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMjg1NzQsImV4cCI6MjA4NTYwNDU3NH0.f8tpIaRlufhJ0hEQqeJsPMUPA6Vp8OhgeDuXp5zj82A"

# Configurações do SQLite
SQLITE_DB = "database.db"

def get_supabase_client():
    """Cria cliente Supabase."""
    if not SUPABASE_KEY:
        print("❌ Erro: SUPABASE_KEY não configurada!")
        print("Por favor, adicione sua chave anon do Supabase no script.")
        return None
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_users(sqlite_conn, supabase: Client):
    """Migra tabela user."""
    print("\n📤 Migrando usuários...")
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM user")
    users = cursor.fetchall()
    
    migrated = 0
    for user_id, username, password_hash, role in users:
        try:
            data = {
                "id": user_id,
                "username": username,
                "password_hash": password_hash,
                "role": role
            }
            supabase.table("user").insert(data).execute()
            migrated += 1
            print(f"   ✅ {username} ({role})")
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar {username}: {e}")
    
    print(f"✅ {migrated}/{len(users)} usuários migrados")
    return migrated

def migrate_items_estoque(sqlite_conn, supabase: Client):
    """Migra tabela item_estoque."""
    print("\n📤 Migrando itens de estoque...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, codigo, endereco, codigo_opcional, tipo, descricao, un, dimensao,
               cliente, qtd_estoque, estoque_minimo, estoque_ideal_compra, 
               tempo_reposicao, data_cadastro
        FROM item_estoque
    """)
    items = cursor.fetchall()
    
    migrated = 0
    for row in items:
        try:
            data = {
                "id": row[0],
                "codigo": row[1],
                "endereco": row[2],
                "codigo_opcional": row[3],
                "tipo": row[4],
                "descricao": row[5],
                "un": row[6],
                "dimensao": row[7],
                "cliente": row[8],
                "qtd_estoque": row[9] or 0,
                "estoque_minimo": row[10] or 5,
                "estoque_ideal_compra": row[11],
                "tempo_reposicao": row[12] or 7,
                "data_cadastro": row[13]
            }
            supabase.table("item_estoque").insert(data).execute()
            migrated += 1
            if migrated % 50 == 0:
                print(f"   ✅ {migrated}/{len(items)} itens migrados...")
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar item {row[1]}: {e}")
    
    print(f"✅ {migrated}/{len(items)} itens migrados")
    return migrated

def migrate_estoque_detalhe(sqlite_conn, supabase: Client):
    """Migra tabela estoque_detalhe."""
    print("\n📤 Migrando detalhes de estoque (lotes)...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, item_estoque_id, lote, item_nf, nf, validade, estacao,
               status_validade, quantidade, data_entrada, status_etiqueta,
               data_etiqueta, usuario_etiqueta
        FROM estoque_detalhe
    """)
    detalhes = cursor.fetchall()
    
    migrated = 0
    for row in detalhes:
        try:
            data = {
                "id": row[0],
                "item_estoque_id": row[1],
                "lote": row[2],
                "item_nf": row[3],
                "nf": row[4],
                "validade": row[5],
                "estacao": row[6],
                "status_validade": row[7],
                "quantidade": row[8] or 0,
                "data_entrada": row[9],
                "status_etiqueta": row[10] or 'PENDENTE',
                "data_etiqueta": row[11],
                "usuario_etiqueta": row[12]
            }
            supabase.table("estoque_detalhe").insert(data).execute()
            migrated += 1
            if migrated % 100 == 0:
                print(f"   ✅ {migrated}/{len(detalhes)} lotes migrados...")
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar lote {row[2]}: {e}")
    
    print(f"✅ {migrated}/{len(detalhes)} lotes migrados")
    return migrated

def migrate_movimentacoes(sqlite_conn, supabase: Client):
    """Migra tabela movimentacao."""
    print("\n📤 Migrando movimentações...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, item_id, tipo, quantidade, data_movimentacao, observacao,
               usuario, etapa, lote, item_nf, nf
        FROM movimentacao
    """)
    movs = cursor.fetchall()
    
    migrated = 0
    batch = []
    batch_size = 100
    
    for row in movs:
        try:
            data = {
                "id": row[0],
                "item_id": row[1],
                "tipo": row[2],
                "quantidade": row[3],
                "data_movimentacao": row[4],
                "observacao": row[5],
                "usuario": row[6],
                "etapa": row[7],
                "lote": row[8],
                "item_nf": row[9],
                "nf": row[10]
            }
            batch.append(data)
            
            # Inserir em lotes para performance
            if len(batch) >= batch_size:
                supabase.table("movimentacao").insert(batch).execute()
                migrated += len(batch)
                print(f"   ✅ {migrated}/{len(movs)} movimentações migradas...")
                batch = []
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar movimentação: {e}")
    
    # Inserir lote final
    if batch:
        try:
            supabase.table("movimentacao").insert(batch).execute()
            migrated += len(batch)
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar lote final: {e}")
    
    print(f"✅ {migrated}/{len(movs)} movimentações migradas")
    return migrated

def migrate_consumiveis(sqlite_conn, supabase: Client):
    """Migra tabela consumivel_estoque."""
    print("\n📤 Migrando consumíveis...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, n_produto, status_estoque, status_consumo, codigo_produto,
               descricao, unidade_medida, categoria, fornecedor, fornecedor2,
               valor_unitario, lead_time, estoque_seguranca, estoque_minimo,
               quantidade_atual, data_cadastro, data_atualizacao
        FROM consumivel_estoque
    """)
    consumiveis = cursor.fetchall()
    
    migrated = 0
    for row in consumiveis:
        try:
            data = {
                "id": row[0],
                "n_produto": row[1],
                "status_estoque": row[2],
                "status_consumo": row[3],
                "codigo_produto": row[4],
                "descricao": row[5],
                "unidade_medida": row[6],
                "categoria": row[7],
                "fornecedor": row[8],
                "fornecedor2": row[9],
                "valor_unitario": row[10] or 0,
                "lead_time": row[11],
                "estoque_seguranca": row[12] or 0,
                "estoque_minimo": row[13] or 0,
                "quantidade_atual": row[14] or 0,
                "data_cadastro": row[15],
                "data_atualizacao": row[16]
            }
            supabase.table("consumivel_estoque").insert(data).execute()
            migrated += 1
            if migrated % 50 == 0:
                print(f"   ✅ {migrated}/{len(consumiveis)} consumíveis migrados...")
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar consumível {row[4]}: {e}")
    
    print(f"✅ {migrated}/{len(consumiveis)} consumíveis migrados")
    return migrated

def migrate_movimentacoes_consumivel(sqlite_conn, supabase: Client):
    """Migra tabela movimentacao_consumivel."""
    print("\n📤 Migrando movimentações de consumíveis...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, consumivel_id, tipo, quantidade, data_movimentacao,
               observacao, usuario, setor_destino
        FROM movimentacao_consumivel
    """)
    movs = cursor.fetchall()
    
    migrated = 0
    batch = []
    batch_size = 100
    
    for row in movs:
        try:
            data = {
                "id": row[0],
                "consumivel_id": row[1],
                "tipo": row[2],
                "quantidade": row[3],
                "data_movimentacao": row[4],
                "observacao": row[5],
                "usuario": row[6],
                "setor_destino": row[7]
            }
            batch.append(data)
            
            if len(batch) >= batch_size:
                supabase.table("movimentacao_consumivel").insert(batch).execute()
                migrated += len(batch)
                print(f"   ✅ {migrated}/{len(movs)} movimentações migradas...")
                batch = []
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar movimentação: {e}")
    
    if batch:
        try:
            supabase.table("movimentacao_consumivel").insert(batch).execute()
            migrated += len(batch)
        except Exception as e:
            print(f"   ⚠️  Erro ao migrar lote final: {e}")
    
    print(f"✅ {migrated}/{len(movs)} movimentações de consumíveis migradas")
    return migrated

def verify_migration(sqlite_conn, supabase: Client):
    """Verifica se a migração foi bem-sucedida."""
    print("\n" + "=" * 80)
    print("🔍 VERIFICANDO MIGRAÇÃO")
    print("=" * 80)
    
    tables = [
        ("user", "user"),
        ("item_estoque", "item_estoque"),
        ("estoque_detalhe", "estoque_detalhe"),
        ("movimentacao", "movimentacao"),
        ("consumivel_estoque", "consumivel_estoque"),
        ("movimentacao_consumivel", "movimentacao_consumivel")
    ]
    
    all_ok = True
    cursor = sqlite_conn.cursor()
    
    for sqlite_table, supabase_table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
        sqlite_count = cursor.fetchone()[0]
        
        try:
            result = supabase.table(supabase_table).select("id", count="exact").execute()
            supabase_count = result.count
            
            if sqlite_count == supabase_count:
                print(f"✅ {supabase_table}: {sqlite_count} = {supabase_count}")
            else:
                print(f"⚠️  {supabase_table}: SQLite={sqlite_count}, Supabase={supabase_count}")
                all_ok = False
        except Exception as e:
            print(f"❌ {supabase_table}: Erro ao verificar - {e}")
            all_ok = False
    
    return all_ok

def main():
    """Função principal de migração."""
    print("=" * 80)
    print("🚀 MIGRAÇÃO SQLITE → SUPABASE")
    print("=" * 80)
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Origem: {SQLITE_DB}")
    print(f"Destino: {SUPABASE_URL}")
    print("=" * 80)
    
    # Verificar se o banco SQLite existe
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Erro: Banco de dados '{SQLITE_DB}' não encontrado!")
        return
    
    # Conectar ao Supabase
    supabase = get_supabase_client()
    if not supabase:
        return
    
    # Conectar ao SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    
    try:
        # Migrar dados na ordem correta (respeitando FKs)
        total_migrated = 0
        
        total_migrated += migrate_users(sqlite_conn, supabase)
        total_migrated += migrate_items_estoque(sqlite_conn, supabase)
        total_migrated += migrate_estoque_detalhe(sqlite_conn, supabase)
        total_migrated += migrate_movimentacoes(sqlite_conn, supabase)
        total_migrated += migrate_consumiveis(sqlite_conn, supabase)
        total_migrated += migrate_movimentacoes_consumivel(sqlite_conn, supabase)
        
        print("\n" + "=" * 80)
        print(f"✅ MIGRAÇÃO CONCLUÍDA!")
        print(f"Total de registros migrados: {total_migrated}")
        print("=" * 80)
        
        # Verificar integridade
        if verify_migration(sqlite_conn, supabase):
            print("\n✅ Verificação: TODOS OS DADOS MIGRADOS COM SUCESSO!")
        else:
            print("\n⚠️  Verificação: Algumas diferenças encontradas. Revise acima.")
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
    finally:
        sqlite_conn.close()
    
    print("\n" + "=" * 80)
    print("🎉 PROCESSO FINALIZADO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
