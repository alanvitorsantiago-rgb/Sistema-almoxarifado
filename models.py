# /models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Instância do SQLAlchemy, será inicializada no app.py
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Modelo para os usuários do sistema."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # 'admin' ou 'user'

class ItemEstoque(db.Model):
    """
    Modelo que representa um item no estoque do almoxarifado.
    """
    __tablename__ = 'item_estoque'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    endereco = db.Column(db.String(100))
    codigo_opcional = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.String(255), nullable=False)
    un = db.Column(db.String(10))
    dimensao = db.Column(db.String(50))
    cliente = db.Column(db.String(100))
    qtd_estoque = db.Column(db.Float, nullable=False, default=0) # Será a soma dos detalhes_estoque
    estoque_minimo = db.Column(db.Float, nullable=False, default=5) # Novo campo para estoque mínimo
    estoque_ideal_compra = db.Column(db.Float, nullable=True) # Quantidade ideal para comprar quando atingir o mínimo
    tempo_reposicao = db.Column(db.Integer, default=7) # Tempo de reposição em dias (lead time)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<ItemEstoque {self.codigo}: {self.descricao}>'

class EstoqueDetalhe(db.Model):
    """
    Modelo que representa um detalhe de estoque por lote/NF para um ItemEstoque.
    Permite rastrear quantidades específicas de lotes para FIFO.
    """
    __tablename__ = 'estoque_detalhe'

    id = db.Column(db.Integer, primary_key=True)
    item_estoque_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    lote = db.Column(db.String(100), nullable=False)
    item_nf = db.Column(db.String(100))
    nf = db.Column(db.String(100))
    validade = db.Column(db.Date)
    estacao = db.Column(db.String(50))
    status_validade = db.Column(db.String(50))
    quantidade = db.Column(db.Float, nullable=False, default=0)
    data_entrada = db.Column(db.DateTime, default=datetime.now) # Para controle FIFO
    
    # Controle de Status Operacional (Etiqueta Vermelha)
    status_etiqueta = db.Column(db.String(50), default='PENDENTE') # 'PENDENTE' ou 'CONCLUÍDO'
    data_etiqueta = db.Column(db.DateTime)
    usuario_etiqueta = db.Column(db.String(100))


    item_estoque = db.relationship('ItemEstoque', backref=db.backref('detalhes_estoque', lazy='dynamic', cascade="all, delete-orphan"))

class Movimentacao(db.Model):
    """
    Modelo que representa uma movimentação de estoque (entrada ou saída).
    """
    __tablename__ = 'movimentacao'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # "ENTRADA" ou "SAÍDA"
    quantidade = db.Column(db.Float, nullable=False)
    data_movimentacao = db.Column(db.DateTime, default=datetime.now)
    observacao = db.Column(db.String(255))
    usuario = db.Column(db.String(100)) # Provisoriamente, será fixo
    etapa = db.Column(db.String(100)) # Novo campo para a etapa do processo
    lote = db.Column(db.String(100)) # Para registrar o lote movimentado
    item_nf = db.Column(db.String(100)) # Para registrar o item_nf movimentado
    nf = db.Column(db.String(100), nullable=True)

    item = db.relationship('ItemEstoque', backref=db.backref('movimentacoes', lazy='dynamic', cascade="all, delete-orphan"))

class ConsumivelEstoque(db.Model):
    """
    Modelo que representa um item consumível no estoque.
    Inclui informações de fornecedores, categorias e controle de quantidade.
    """
    __tablename__ = 'consumivel_estoque'

    id = db.Column(db.Integer, primary_key=True)
    n_produto = db.Column(db.String(50), unique=True, nullable=False)
    status_estoque = db.Column(db.String(50))  # Ex: "Ativo", "Inativo"
    status_consumo = db.Column(db.String(50))  # Ex: "Consumível", "Material Específico"
    codigo_produto = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    unidade_medida = db.Column(db.String(20))  # Ex: "UN", "CX", "KG", "L"
    categoria = db.Column(db.String(100))  # Ex: "Papel", "Ferramentas", "Tintas"
    fornecedor = db.Column(db.String(150))
    fornecedor2 = db.Column(db.String(150))
    valor_unitario = db.Column(db.Float, default=0)
    lead_time = db.Column(db.Integer)  # Tempo de reposição em dias
    estoque_seguranca = db.Column(db.Float, default=0)  # Estoque de segurança
    estoque_minimo = db.Column(db.Float, default=0)
    quantidade_atual = db.Column(db.Float, nullable=False, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ConsumivelEstoque {self.codigo_produto}: {self.descricao}>'

class MovimentacaoConsumivel(db.Model):
    """
    Modelo que representa uma movimentação de consumível (entrada ou saída).
    """
    __tablename__ = 'movimentacao_consumivel'

    id = db.Column(db.Integer, primary_key=True)
    consumivel_id = db.Column(db.Integer, db.ForeignKey('consumivel_estoque.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # "ENTRADA" ou "SAÍDA"
    quantidade = db.Column(db.Float, nullable=False)
    data_movimentacao = db.Column(db.DateTime, default=datetime.now)
    observacao = db.Column(db.String(255))
    usuario = db.Column(db.String(100))
    setor_destino = db.Column(db.String(100))  # Setor ou etapa de destino

    consumivel = db.relationship('ConsumivelEstoque', backref=db.backref('movimentacoes', lazy='dynamic', cascade="all, delete-orphan"))
