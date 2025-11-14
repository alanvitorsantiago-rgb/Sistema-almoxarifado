# app/models.py
from . import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # 'user' ou 'admin'

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class ItemEstoque(db.Model):
    __tablename__ = 'item_estoque'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    endereco = db.Column(db.String(100))
    codigo_opcional = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.String(200), nullable=False)
    un = db.Column(db.String(10))
    dimensao = db.Column(db.String(50))
    estoque_minimo = db.Column(db.Float, default=5.0)
    cliente = db.Column(db.String(100))
    qtd_estoque = db.Column(db.Float, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    movimentacoes = db.relationship('Movimentacao', backref='item', lazy='dynamic', cascade="all, delete-orphan")
    detalhes_estoque = db.relationship('EstoqueDetalhe', backref='item_estoque', lazy='dynamic', cascade="all, delete-orphan")

class EstoqueDetalhe(db.Model):
    __tablename__ = 'estoque_detalhe'
    id = db.Column(db.Integer, primary_key=True)
    item_estoque_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    lote = db.Column(db.String(50))
    item_nf = db.Column(db.String(50))
    nf = db.Column(db.String(50))
    validade = db.Column(db.Date)
    estacao = db.Column(db.String(50))
    quantidade = db.Column(db.Float, nullable=False, default=0)
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('item_estoque_id', 'lote', 'item_nf', 'nf', name='_item_lote_nf_uc'),)

class Movimentacao(db.Model):
    __tablename__ = 'movimentacao'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False) # 'ENTRADA', 'SAIDA', 'AJUSTE'
    quantidade = db.Column(db.Float, nullable=False)
    lote = db.Column(db.String(50))
    item_nf = db.Column(db.String(50))
    etapa = db.Column(db.String(100))
    observacao = db.Column(db.String(255))
    usuario = db.Column(db.String(80))
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)