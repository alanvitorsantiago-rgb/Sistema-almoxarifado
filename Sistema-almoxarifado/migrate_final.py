#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar o banco de dados SQLite adicionando colunas faltantes
sem perder dados existentes.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Adiciona as colunas faltantes ao banco de dados."""
    
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando estrutura do banco de dados...")
        print()
        
        # ===== TABELA: item_estoque =====
        print("📋 Verificando tabela 'item_estoque'...")
        cursor.execute("PRAGMA table_info(item_estoque)")
        cols = [col[1] for col in cursor.fetchall()]
        
        # Adiciona estoque_ideal_compra se não existir
        if 'estoque_ideal_compra' not in cols:
            print("  📝 Adicionando 'estoque_ideal_compra'...")
            cursor.execute("ALTER TABLE item_estoque ADD COLUMN estoque_ideal_compra FLOAT NULL")
            print("  ✅ Coluna 'estoque_ideal_compra' adicionada!")
        else:
            print("  ✅ 'estoque_ideal_compra' já existe")
        
        # Adiciona tempo_reposicao se não existir
        if 'tempo_reposicao' not in cols:
            print("  📝 Adicionando 'tempo_reposicao'...")
            cursor.execute("ALTER TABLE item_estoque ADD COLUMN tempo_reposicao INTEGER DEFAULT 7")
            print("  ✅ Coluna 'tempo_reposicao' adicionada!")
        else:
            print("  ✅ 'tempo_reposicao' já existe")
        
        # ===== TABELA: movimentacao =====
        print()
        print("📋 Verificando tabela 'movimentacao'...")
        cursor.execute("PRAGMA table_info(movimentacao)")
        cols = [col[1] for col in cursor.fetchall()]
        
        # Adiciona nf se não existir
        if 'nf' not in cols:
            print("  📝 Adicionando 'nf'...")
            cursor.execute("ALTER TABLE movimentacao ADD COLUMN nf VARCHAR(100) NULL")
            print("  ✅ Coluna 'nf' adicionada!")
        else:
            print("  ✅ 'nf' já existe")
        
        # ===== COMMIT =====
        conn.commit()
        print()
        print(f"✅ Migração concluída em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("✅ BANCO DE DADOS SINCRONIZADO COM SUCESSO!")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar banco de dados: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == '__main__':
    success = migrate_database()
    exit(0 if success else 1)
