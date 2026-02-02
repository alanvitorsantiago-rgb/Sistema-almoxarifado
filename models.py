# /models.py

from flask_login import UserMixin
from datetime import datetime

# db = SQLAlchemy() - Removido

class ModelWrapper:
    """Class base para envolver dicionários do Supabase como objetos"""
    def __init__(self, data=None, **kwargs):
        self._data = data if data else {}
        self._data.update(kwargs)
        
        # Lista de campos que devem ser convertidos para datetime
        date_fields = ['data_movimentacao', 'data_entrada', 'validade', 'created_at']
        
        # Define atributos dinamicamente
        for key, value in self._data.items():
            if key in date_fields and isinstance(value, str):
                try:
                    # Supabase ISO format usually: '2025-01-30T10:00:00+00:00' or '2025-01-30'
                    # Handle basic ISO format
                    if 'T' in value:
                        # Remove timezone simple if needed or keep it.
                        # datetime.fromisoformat works well in recent python
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    else:
                        # Date only
                         value = datetime.strptime(value, '%Y-%m-%d').date() if '-' in value else value
                except (ValueError, TypeError):
                    pass # Keep as string if parsing fails
            
            setattr(self, key, value)

    def to_dict(self):
        return self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

class User(UserMixin, ModelWrapper):
    """Modelo para os usuários do sistema."""
    
    def get_id(self):
        return str(getattr(self, 'id', ''))
        
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False

class ItemEstoque(ModelWrapper):
    """Modelo que representa um item no estoque."""
    pass

class EstoqueDetalhe(ModelWrapper):
    """Modelo que representa um detalhe de estoque."""
    @property
    def item_estoque(self):
        # Supabase retorna 'item_estoque' como dict aninhado
        data = self.get('item_estoque')
        return ItemEstoque(data) if data else None

class Movimentacao(ModelWrapper):
    """Modelo que representa uma movimentação de estoque."""
    @property
    def item(self):
        # Mapeia 'item' para 'item_estoque' vindo do Supabase
        data = self.get('item_estoque')
        return ItemEstoque(data) if data else None

class ConsumivelEstoque(ModelWrapper):
    """Modelo que representa um item consumível."""
    pass

class MovimentacaoConsumivel(ModelWrapper):
    """Modelo que representa uma movimentação de consumível."""
    @property
    def consumivel(self):
        # Mapeia 'consumivel' para 'consumivel_estoque' (suposição, validar se necessário)
        # Se a query for select('*, consumivel_estoque(*)')
        data = self.get('consumivel_estoque') # ou 'consumivel' dependendo do nome da tabela
        return ConsumivelEstoque(data) if data else None

class Pagination:
    """Simula a classe Pagination do Flask-SQLAlchemy para as templates."""
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = int((total + per_page - 1) / per_page)
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

# Mocking db object to prevent immediate import errors in app.py before full cleanup

