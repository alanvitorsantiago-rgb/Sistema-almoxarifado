#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar o banco de dados SQLite adicionando a coluna estoque_ideal_compra
sem perder dados existentes.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Adiciona as colunas estoque_ideal_compra e tempo_reposicao à tabela item_estoque."""
    
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando estrutura do banco de dados...")
        
        # Verifica quais colunas existem
        cursor.execute("PRAGMA table_info(item_estoque)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Adiciona estoque_ideal_compra se não existir
        if 'estoque_ideal_compra' not in columns:
            print("📝 Adicionando coluna 'estoque_ideal_compra'...")
            cursor.execute("""
                ALTER TABLE item_estoque 
                ADD COLUMN estoque_ideal_compra FLOAT NULL
            """)
            print("✅ Coluna 'estoque_ideal_compra' adicionada!")
        else:
            print("✅ Coluna 'estoque_ideal_compra' já existe!")
        
        # Adiciona tempo_reposicao se não existir
        if 'tempo_reposicao' not in columns:
            print("📝 Adicionando coluna 'tempo_reposicao'...")
            cursor.execute("""
                ALTER TABLE item_estoque 
                ADD COLUMN tempo_reposicao INTEGER DEFAULT 7
            """)
            print("✅ Coluna 'tempo_reposicao' adicionada com padrão 7 dias!")
        else:
            print("✅ Coluna 'tempo_reposicao' já existe!")
        
        conn.commit()
        print(f"✅ Migração concluída em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Verifica as colunas finais
        cursor.execute("PRAGMA table_info(item_estoque)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'estoque_ideal_compra' in columns and 'tempo_reposicao' in columns:
            print("✅ Todas as colunas verificadas e confirmadas!")
        
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
