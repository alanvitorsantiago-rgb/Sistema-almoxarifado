#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar dados corrigidos."""

from app import db, app
from models import ItemEstoque

with app.app_context():
    items = db.session.query(ItemEstoque).limit(10).all()
    for i, item in enumerate(items, 1):
        print(f'=== Item {i} ({item.codigo}) ===')
        print(f'TIPO: {item.tipo}')
        print(f'DESCRIÇÃO: {item.descricao}')
        print(f'LOCAL: {item.endereco}')
        print(f'UN: {item.un}')
        print(f'DIMENSÃO: {item.dimensao}')
        detalhe = item.detalhes_estoque.first()
        if detalhe:
            print(f'LOTE: {detalhe.lote}')
            print(f'ITEM NF: {detalhe.item_nf}')
            print(f'NF: {detalhe.nf}')
        print()
