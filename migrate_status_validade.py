#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar o banco de dados SQLite adicionando colunas de controle de status
para a funcionalidade de Controle de Validade (Etiqueta Vermelha).
"""

import sqlite3
import os
from datetime import datetime

def migrate_status_validade():
    """Adiciona as colunas status_etiqueta, data_etiqueta e usuario_etiqueta à tabela estoque_detalhe."""
    
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando estrutura da tabela estoque_detalhe...")
        
        # Verifica quais colunas existem
        cursor.execute("PRAGMA table_info(estoque_detalhe)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Adiciona status_etiqueta (PENDENTE | CONCLUÍDO)
        if 'status_etiqueta' not in columns:
            print("📝 Adicionando coluna 'status_etiqueta'...")
            cursor.execute("""
                ALTER TABLE estoque_detalhe 
                ADD COLUMN status_etiqueta TEXT DEFAULT 'PENDENTE'
            """)
            print("✅ Coluna 'status_etiqueta' adicionada com padrão 'PENDENTE'!")
        else:
            print("✅ Coluna 'status_etiqueta' já existe!")
            
        # Adiciona data_etiqueta
        if 'data_etiqueta' not in columns:
            print("📝 Adicionando coluna 'data_etiqueta'...")
            cursor.execute("""
                ALTER TABLE estoque_detalhe 
                ADD COLUMN data_etiqueta TIMESTAMP NULL
            """)
            print("✅ Coluna 'data_etiqueta' adicionada!")
        else:
            print("✅ Coluna 'data_etiqueta' já existe!")

        # Adiciona usuario_etiqueta
        if 'usuario_etiqueta' not in columns:
            print("📝 Adicionando coluna 'usuario_etiqueta'...")
            cursor.execute("""
                ALTER TABLE estoque_detalhe 
                ADD COLUMN usuario_etiqueta TEXT NULL
            """)
            print("✅ Coluna 'usuario_etiqueta' adicionada!")
        else:
            print("✅ Coluna 'usuario_etiqueta' já existe!")
        
        conn.commit()
        print(f"✅ Migração de status concluída com sucesso em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar banco de dados: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == '__main__':
    success = migrate_status_validade()
    exit(0 if success else 1)
