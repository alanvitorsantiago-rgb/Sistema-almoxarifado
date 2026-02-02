#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cliente Supabase Centralizado
Gerencia todas as conexões e operações com o Supabase via REST API (HTTPS/443)
"""

import os
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env.supabase')

# Configuração do cliente Supabase
SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')

# Inicializa o cliente Supabase (inicialização segura para Vercel)
# Se não houver chaves agora, o objeto 'supabase' será None ou falhará apenas ao ser usado.
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Cliente Supabase inicializado com sucesso (HTTPS/443)")
    except Exception as e:
        print(f"⚠️ Erro ao criar cliente Supabase: {e}")
else:
    print("⚠️ SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontrados. O cliente será inicializado sem conexão.")


# ============================================================
# FUNÇÕES HELPER PARA OPERAÇÕES COMUNS
# ============================================================

def safe_execute(query, operation: str = "query"):
    """
    Executa uma query Supabase com error handling padrão.
    
    Args:
        query: Query Supabase (ex: supabase.table('user').select('*'))
        operation: Nome da operação para logging
    
    Returns:
        dict com 'success', 'data', 'error'
    """
    try:
        response = query.execute()
        return {
            'success': True,
            'data': response.data,
            'error': None
        }
    except Exception as e:
        print(f"❌ Erro em {operation}: {str(e)}")
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


def insert_one(table: str, data: Dict[str, Any]) -> Optional[Dict]:
    """
    Insere um registro em uma tabela.
    
    Args:
        table: Nome da tabela
        data: Dicionário com os dados
    
    Returns:
        Registro inserido ou None se houver erro
    """
    if not supabase: return None
    result = safe_execute(
        supabase.table(table).insert(data),
        operation=f"INSERT em {table}"
    )
    return result['data'][0] if result['success'] and result['data'] else None


def update_one(table: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Optional[Dict]:
    """
    Atualiza um registro em uma tabela.
    
    Args:
        table: Nome da tabela
        filters: Filtros para encontrar o registro (ex: {'id': 1})
        data: Dados a serem atualizados
    
    Returns:
        Registro atualizado ou None se houver erro
    """
    if not supabase: return None
    query = supabase.table(table).update(data)
    for key, value in filters.items():
        query = query.eq(key, value)
    
    result = safe_execute(query, operation=f"UPDATE em {table}")
    return result['data'][0] if result['success'] and result['data'] else None


def select_one(table: str, filters: Dict[str, Any], columns: str = '*') -> Optional[Dict]:
    """
    Seleciona um único registro de uma tabela.
    
    Args:
        table: Nome da tabela
        filters: Filtros (ex: {'username': 'admin'})
        columns: Colunas a retornar (padrão: todas)
    
    Returns:
        Registro encontrado ou None
    """
    if not supabase: return None
    query = supabase.table(table).select(columns)
    for key, value in filters.items():
        query = query.eq(key, value)
    
    result = safe_execute(query.limit(1), operation=f"SELECT em {table}")
    return result['data'][0] if result['success'] and result['data'] else None


def select_many(table: str, filters: Optional[Dict[str, Any]] = None, 
                columns: str = '*', order_by: Optional[str] = None,
                limit: Optional[int] = None) -> List[Dict]:
    """
    Seleciona múltiplos registros de uma tabela.
    
    Args:
        table: Nome da tabela
        filters: Filtros opcionais
        columns: Colunas a retornar
        order_by: Coluna para ordenação (ex: 'created_at')
        limit: Limite de registros
    
    Returns:
        Lista de registros
    """
    if not supabase: return []
    query = supabase.table(table).select(columns)
    
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    if order_by:
        desc = order_by.startswith('-')
        col = order_by.lstrip('-')
        query = query.order(col, desc=desc)
    
    if limit:
        query = query.limit(limit)
    
    result = safe_execute(query, operation=f"SELECT MANY em {table}")
    return result['data'] if result['success'] else []


def delete_one(table: str, filters: Dict[str, Any]) -> bool:
    """
    Deleta um registro de uma tabela.
    
    Args:
        table: Nome da tabela
        filters: Filtros para identificar o registro
    
    Returns:
        True se deletado com sucesso
    """
    if not supabase: return False
    query = supabase.table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)
    
    result = safe_execute(query, operation=f"DELETE em {table}")
    return result['success']


# ============================================================
# OPERAÇÕES ESPECÍFICAS DO DOMÍNIO
# ============================================================

def get_user_by_username(username: str) -> Optional[Dict]:
    """Busca usuário por username"""
    return select_one('user', {'username': username})


def get_item_estoque_by_id(item_id: int) -> Optional[Dict]:
    """Busca item de estoque por ID"""
    return select_one('item_estoque', {'id': item_id})


def get_all_items_estoque() -> List[Dict]:
    """Lista todos os itens de estoque"""
    return select_many('item_estoque', order_by='descricao')


def create_movimentacao(data: Dict[str, Any]) -> Optional[Dict]:
    """Registra uma movimentação de estoque"""
    return insert_one('movimentacao', data)


# ============================================================
# TESTES DE CONEXÃO
# ============================================================

def test_connection() -> bool:
    """
    Testa a conexão com o Supabase.
    
    Returns:
        True se conectado com sucesso
    """
    try:
        if not supabase:
             return False
        # Tenta fazer uma query simples
        response = supabase.table('user').select('count', count='exact').execute()
        print(f"✅ Conexão OK - {response.count} usuários encontrados")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False


if __name__ == "__main__":
    # Teste rápido ao executar o arquivo diretamente
    print("🧪 Testando conexão com Supabase...")
    if test_connection():
        print("✅ Cliente Supabase funcionando corretamente!")
    else:
        print("❌ Falha na conexão com Supabase")
