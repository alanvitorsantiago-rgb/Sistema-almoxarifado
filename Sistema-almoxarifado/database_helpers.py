#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Helpers - Funções auxiliares para operações de banco de dados via Supabase
Substitui as operações SQLAlchemy mantendo a mesma interface
"""

from typing import Optional, Dict, List, Any
from Sistema-almoxarifado.supabase_client import supabase, select_one, select_many, insert_one, update_one, delete_one
from flask import abort


# ============================================================
# USER OPERATIONS
# ============================================================

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Busca usuário por ID.
    Equivalente a: User.query.get(user_id)
    """
    return select_one('user', {'id': user_id})


def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Busca usuário por username.
    Equivalente a: User.query.filter_by(username=username).first()
    """
    return select_one('user', {'username': username})


def get_all_users(order_by: str = 'username') -> List[Dict]:
    """
    Lista todos os usuários ordenados.
    Equivalente a: User.query.order_by(User.username).all()
    """
    return select_many('user', order_by=order_by)


def create_user(username: str, password_hash: str, role: str = 'user') -> Optional[Dict]:
    """
    Cria um novo usuário.
    Equivalente a: db.session.add(User(...)); db.session.commit()
    """
    data = {
        'username': username,
        'password_hash': password_hash,
        'role': role
    }
    return insert_one('user', data)


def update_user(user_id: int, data: Dict[str, Any]) -> Optional[Dict]:
    """
    Atualiza um usuário.
    Equivalente a: user.attr = value; db.session.commit()
    """
    return update_one('user', {'id': user_id}, data)


def delete_user(user_id: int) -> bool:
    """
    Deleta um usuário.
    Equivalente a: db.session.delete(user); db.session.commit()
    """
    return delete_one('user', {'id': user_id})


def get_user_by_id_or_404(user_id: int) -> Dict:
    """
    Busca usuário ou retorna 404.
    Equivalente a: User.query.get_or_404(user_id)
    """
    user = get_user_by_id(user_id)
    if not user:
        abort(404, description=f"Usuário com ID {user_id} não encontrado")
    return user


# ============================================================
# ITEM ESTOQUE OPERATIONS
# ============================================================

def get_item_estoque_by_id(item_id: int) -> Optional[Dict]:
    """Busca item de estoque por ID"""
    return select_one('item_estoque', {'id': item_id})


def get_item_estoque_by_codigo(codigo: str) -> Optional[Dict]:
    """Busca item de estoque por código"""
    return select_one('item_estoque', {'codigo': codigo})


def get_all_items_estoque(filters: Optional[Dict] = None, order_by: str = 'descricao') -> List[Dict]:
    """Lista todos os itens de estoque"""
    return select_many('item_estoque', filters=filters, order_by=order_by)


def create_item_estoque(data: Dict[str, Any]) -> Optional[Dict]:
    """Cria um novo item de estoque"""
    return insert_one('item_estoque', data)


def update_item_estoque(item_id: int, data: Dict[str, Any]) -> Optional[Dict]:
    """Atualiza um item de estoque"""
    return update_one('item_estoque', {'id': item_id}, data)


def delete_item_estoque(item_id: int) -> bool:
    """Deleta um item de estoque"""
    return delete_one('item_estoque', {'id': item_id})


# ============================================================
# ESTOQUE DETALHE OPERATIONS
# ============================================================

def get_estoque_detalhes_by_item(item_id: int) -> List[Dict]:
    """Busca todos os detalhes de estoque de um item"""
    return select_many('estoque_detalhe', filters={'item_estoque_id': item_id})


def create_estoque_detalhe(data: Dict[str, Any]) -> Optional[Dict]:
    """Cria um novo detalhe de estoque"""
    return insert_one('estoque_detalhe', data)


def update_estoque_detalhe(detalhe_id: int, data: Dict[str, Any]) -> Optional[Dict]:
    """Atualiza um detalhe de estoque"""
    return update_one('estoque_detalhe', {'id': detalhe_id}, data)


# ============================================================
# MOVIMENTACAO OPERATIONS
# ============================================================

def create_movimentacao(data: Dict[str, Any]) -> Optional[Dict]:
    """Registra uma movimentação"""
    return insert_one('movimentacao', data)


def get_movimentacoes_by_item(item_id: int, limit: Optional[int] = None) -> List[Dict]:
    """Busca movimentações de um item"""
    return select_many('movimentacao', filters={'item_id': item_id}, order_by='-data_movimentacao', limit=limit)

def get_item_movements_in_period(item_id: int, days: int = 90, tipo: str = 'SAIDA') -> List[Dict]:
    """Busca movimentações de um tipo específico nos últimos X dias"""
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        response = supabase.table('movimentacao') \
            .select('*') \
            .eq('item_id', item_id) \
            .eq('tipo', tipo) \
            .gte('data_movimentacao', start_date) \
            .order('data_movimentacao', desc=False) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_item_movements_in_period: {str(e)}")
        return []

def get_all_movimentacoes(order_by: str = '-data_movimentacao', limit: Optional[int] = None) -> List[Dict]:
    """Lista todas as movimentações"""
    return select_many('movimentacao', order_by=order_by, limit=limit)


# ============================================================
# CONSUMIVEL ESTOQUE OPERATIONS
# ============================================================

def get_consumivel_by_id(consumivel_id: int) -> Optional[Dict]:
    """Busca consumível por ID"""
    return select_one('consumivel_estoque', {'id': consumivel_id})


def get_all_consumiveis(order_by: str = 'nome') -> List[Dict]:
    """Lista todos os consumíveis"""
    return select_many('consumivel_estoque', order_by=order_by)


def create_consumivel(data: Dict[str, Any]) -> Optional[Dict]:
    """Cria um novo consumível"""
    return insert_one('consumivel_estoque', data)


def update_consumivel(consumivel_id: int, data: Dict[str, Any]) -> Optional[Dict]:
    """Atualiza um consumível"""
    return update_one('consumivel_estoque', {'id': consumivel_id}, data)


# ============================================================
# MOVIMENTACAO CONSUMIVEL OPERATIONS
# ============================================================

def create_movimentacao_consumivel(data: Dict[str, Any]) -> Optional[Dict]:
    """Registra uma movimentação de consumível"""
    return insert_one('movimentacao_consumivel', data)


def get_movimentacoes_consumivel(consumivel_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
    """Busca movimentações de consumíveis"""
    filters = {'consumivel_id': consumivel_id} if consumivel_id else None
    return select_many('movimentacao_consumivel', filters=filters, order_by='-data_movimentacao', limit=limit)


# ============================================================
# COMPLEX QUERIES (que precisam de query builder customizado)
# ============================================================

def search_items_estoque(search_term: str, limite: int = 10) -> List[Dict]:
    """
    Busca itens por código ou descrição (para autocompletar).
    Equivalente a: ItemEstoque.query.filter(or_(codigo.ilike(), descricao.ilike())).limit(10)
    """
    try:
        # Supabase usa "ilike" para case-insensitive LIKE
        response = supabase.table('item_estoque') \
            .select('id, codigo, descricao') \
            .or_(f'codigo.ilike.%{search_term}%,descricao.ilike.%{search_term}%') \
            .limit(limite) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro ao buscar itens: {str(e)}")
        return []


def count_items_estoque(filters: Optional[Dict] = None) -> int:
    """
    Conta itens de estoque com filtros opcionais.
    """
    try:
        query = supabase.table('item_estoque').select('*', count='exact')
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        print(f"❌ Erro ao contar itens: {str(e)}")
        return 0


# ============================================================
# DASHBOARD & REPORTS (Complex Aggregations)
# ============================================================

def get_dashboard_metrics():
    """Calcula métricas do dashboard via Python (para evitar complexidade SQL na API)"""
    try:
        # Total Itens
        total_items = count_items_estoque()
        
        # Total Unidades e Itens Zerados
        # Buscamos qtd_estoque apenas para economizar banda
        items_resp = supabase.table('item_estoque').select('qtd_estoque, tipo').execute()
        items = items_resp.data if items_resp.data else []
        
        total_unidades = sum(item.get('qtd_estoque', 0) for item in items)
        itens_zerados = sum(1 for item in items if item.get('qtd_estoque', 0) == 0)
        
        # Agrupamento por Tipo (Pizza)
        tipos_count = {}
        for item in items:
            tipo = item.get('tipo') or 'Não categorizado'
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
            
        tipos_chart_data = {
            'labels': list(tipos_count.keys()),
            'counts': list(tipos_count.values())
        }
        
        return {
            'total_items_distintos': total_items,
            'total_unidades': total_unidades,
            'itens_zerados': itens_zerados,
            'tipos_chart_data': tipos_chart_data
        }
    except Exception as e:
        print(f"❌ Erro em get_dashboard_metrics: {str(e)}")
        return {
            'total_items_distintos': 0, 'total_unidades': 0, 
            'itens_zerados': 0, 'tipos_chart_data': {'labels': [], 'counts': []}
        }

def get_critical_lotes(days=30):
    """Busca lotes vencendo nos próximos X dias"""
    try:
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        response = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao)') \
            .lte('validade', target_date) \
            .gt('quantidade', 0) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro em get_critical_lotes: {str(e)}")
        return []

def get_recent_movimentacoes(limit=5):
    """Busca últimas movimentações com detalhes do item"""
    try:
        response = supabase.table('movimentacao') \
            .select('*, item_estoque(codigo, descricao)') \
            .order('data_movimentacao', desc=True) \
            .limit(limit) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro em get_recent_movimentacoes: {str(e)}")
        return []

def get_movimentacoes_report(data_inicio=None, data_fim=None, search_term=None):
    """Relatório de movimentações com filtros"""
    try:
        query = supabase.table('movimentacao').select('*, item_estoque(codigo, descricao)')
        
        if data_inicio:
            query = query.gte('data_movimentacao', data_inicio)
        if data_fim:
             # Adiciona o final do dia
            query = query.lte('data_movimentacao', f"{data_fim} 23:59:59")
            
        response = query.order('data_movimentacao', desc=True).execute()
        data = response.data if response.data else []
        
        # Filtro de texto em Python (mais flexível para joins com OR)
        if search_term:
            term = search_term.lower()
            filtered = []
            for mov in data:
                item = mov.get('item_estoque', {}) or {}
                # Verifica se search_term está em algum campo relevante
                if (term in str(item.get('codigo', '')).lower() or
                    term in str(item.get('descricao', '')).lower() or
                    term in str(mov.get('lote', '')).lower() or
                    term in str(mov.get('usuario', '')).lower() or
                    term in str(mov.get('observacao', '')).lower()):
                    filtered.append(mov)
            data = filtered
            
        return data
    except Exception as e:
        print(f"❌ Erro report movimentacoes: {str(e)}")
        return []

def get_top_items(limit=5, order_by='qtd_estoque', desc=True):
    """Busca top items (mais ou menos estoque)"""
    try:
        query = supabase.table('item_estoque').select('*')
        # Filtra inválidos
        query = query.neq('descricao', '').neq('descricao', '-').neq('descricao', '=')
        
        # Ordenação
        query = query.order(order_by, desc=desc).limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_top_items: {str(e)}")
        return []

def get_low_stock_items(limit=5):
    """Itens com estoque baixo (qtd <= estoque_minimo)"""
    try:
        # Supabase não suporta comparação entre colunas ('qtd_estoque' <= 'estoque_minimo') diretamente via API REST simples
        # Precisaríamos de uma VIEW ou RPC.
        # Workaround: Pegar itens com qtde baixa e filtrar em Python
        
        response = supabase.table('item_estoque') \
            .select('*') \
            .gt('qtd_estoque', 0) \
            .neq('descricao', '') \
            .neq('descricao', '-') \
            .neq('descricao', '=') \
            .order('qtd_estoque', desc=False) \
            .limit(100) \
            .execute()
            
        items = response.data if response.data else []
        
        # Filtra Python side: qtd <= estoque_minimo
        low_stock = [item for item in items if item.get('qtd_estoque', 0) <= item.get('estoque_minimo', 5)]
        return low_stock[:limit]
    except Exception as e:
        print(f"❌ Erro get_low_stock_items: {str(e)}")
        return []

def get_expiring_lots(days=40, today_only=False):
    """Lotes vencendo hoje ou em breve"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao, endereco)') \
            .gt('quantidade', 0) \
        
        if today_only:
            query = query.eq('validade', today)
        else:
            query = query.gt('validade', today).lte('validade', target_date)
            
        response = query.order('validade').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_expiring_lots: {str(e)}")
        return []

def get_etiqueta_vermelha_items(days=40):
    """Busca itens para etiqueta vermelha (pendentes)"""
    try:
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Filtro OR é chato no Supabase client simples.
        # Mas status_etiqueta ser NULL ou 'PENDENTE'.
        # O filtro .or_('status_etiqueta.eq.PENDENTE,status_etiqueta.is.null') funciona na string query
        
        response = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao, endereco)') \
            .lte('validade', target_date) \
            .gt('quantidade', 0) \
            .or_('status_etiqueta.eq.PENDENTE,status_etiqueta.is.null') \
            .order('validade') \
            .execute()
            
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_etiqueta_vermelha_items: {str(e)}")
        return []

def get_historico_etiquetas(limit=500):
    """Busca histórico de etiquetas concluídas"""
    try:
        response = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao, endereco)') \
            .eq('status_etiqueta', 'CONCLUÍDO') \
            .order('data_etiqueta', desc=True) \
            .limit(limit) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_historico_etiquetas: {str(e)}")
        return []

def get_estoque_detalhado(page=1, per_page=25, search_term=None):
    """
    Busca detalhes de estoque (batches) com paginação e busca.
    Sort by: validade ASC (nulls last would be ideal but hard in basic REST, default ASC puts nulls last usually or first depending on DB)
    Supabase: .order('validade', nulls_first=False)
    """
    try:
        query = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao, endereco)', count='exact') \
            .gt('quantidade', 0)
            
        if search_term:
            # Search is tricky on nested joined tables via single OR.
            # Best effort: filter on details fields or fetch all and filter python (bad for pagination).
            # Supabase DOES support filtering on joined tables for exact matches (item_estoque.codigo.eq...), but ILIKE with OR across tables is hard.
            # For now, let's implement simple search on lote/nf/item_nf.
            # For item code/desc search, ideally we use proper search text search or RPC.
            term = f"%{search_term}%"
            # Attempting complex filter if possible? No, it often breaks.
            # Let's try searching local fields first.
            query = query.or_(f"lote.ilike.{term},nf.ilike.{term},item_nf.ilike.{term}")
            
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        # Order by validade ASC
        query = query.order('validade', desc=False).range(start, end)
        
        response = query.execute()
        items = response.data if response.data else []
        total = response.count if hasattr(response, 'count') else 0
        
        return items, total
    except Exception as e:
        print(f"❌ Erro get_estoque_detalhado: {str(e)}")
        return [], 0

def get_item_movements_by_item_id(item_id):
    """Busca todas as movimentações de um item"""
    try:
        response = supabase.table('movimentacao') \
            .select('*, item_estoque(codigo, descricao)') \
            .eq('item_id', item_id) \
            .order('data_movimentacao', desc=True) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_item_movements_by_item_id: {str(e)}")
        return []

def get_detalhes_by_item(item_id, filtro_critico=False):
    """Busca detalhes (lotes) de um item"""
    try:
        query = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(codigo, descricao)') \
            .eq('item_estoque_id', item_id)
            
        if filtro_critico:
            today = datetime.now()
            target_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
            query = query.gt('quantidade', 0).lte('validade', target_date).neq('validade', None)
            
        response = query.order('data_entrada', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_detalhes_by_item: {str(e)}")
        return []
        
def get_consumiveis(search_term=None):
    """Busca consumiveis com filtro opcional"""
    try:
        query = supabase.table('consumivel_estoque').select('*')
        if search_term:
            term = f"%{search_term}%"
            query = query.or_(f"codigo_produto.ilike.{term},descricao.ilike.{term},categoria.ilike.{term}")
        
        response = query.order('codigo_produto').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_consumiveis: {str(e)}")
        return []

def get_movimentacoes_consumivel(limit=None):
    """Busca movimentos de consumíveis"""
    try:
        query = supabase.table('movimentacao_consumivel') \
            .select('*, consumivel_estoque(*)') \
            .order('data_movimentacao', desc=True)
            
        if limit:
            query = query.limit(limit)
            
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro get_movimentacoes_consumivel: {str(e)}")
        return []

def delete_movimentacao(mov_id):
    """Deleta uma movimentacao pelo ID"""
    try:
        response = supabase.table('movimentacao').delete().eq('id', mov_id).execute()
        return response
    except Exception as e:
        print(f"❌ Erro delete_movimentacao: {str(e)}")
        raise e

