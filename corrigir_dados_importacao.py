#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corrigir dados importados incorretamente.

PROBLEMA REAL IDENTIFICADO:
Os dados foram importados com as DESCRIÇÕES contendo concatenação de múltiplos campos:
- TIPO: Correto (descrição do tipo do material) ✅
- DESCRIÇÃO: Contém concatenação (tipo + dimensão + UN + qtd + cliente + lote + item_nf + nf + validade)  ❌
- LOCAL (endereco): Contém categoria (HARDWARE, PERECÍVEIS, PAINEL) - INCORRETO ❌
- UN: Contém dimensão (A2.1, B2.6, etc) - INCORRETO ❌

A causa foi na importação original - o arquivo Excel tinha dados concatenados em uma única coluna DESCRIÇÃO.

SOLUÇÃO:
1. Separar a DESCRIÇÃO concatenada usando a informação do EstoqueDetalhe como referência
2. TIPO permanece como está (correto)
3. DESCRIÇÃO ← TIPO (será a descrição real do tipo)
4. DIMENSÃO ← UN (será a dimensão extraída)
5. UN ← 'UN' (padrão)
6. LOCAL ← manter como está ou usar a categoria
"""

import re
from app import db, app
from models import ItemEstoque, EstoqueDetalhe

def extrair_dimensao(un_field):
    """Extrai dimensão do campo UN que contém valores como 'A2.1', 'B2.6', 'DEFINIR', etc."""
    if not un_field or un_field in ['UN', 'DEFINIR', '']:
        return ''
    return str(un_field).strip()

def corrigir_dados():
    """
    Corrige os dados importados incorretamente no banco.
    
    Estratégia:
    - TIPO já está correto, não alterar
    - DESCRIÇÃO será substituída pelo TIPO (que é a descrição real)
    - DIMENSÃO receberá o valor de UN (que contém a dimensão)
    - UN será sempre 'UN' (unidade de medida padrão)
    - ENDERECO (LOCAL) manterá a categoria como localização (HARDWARE, PERECÍVEIS, PAINEL)
    """
    
    with app.app_context():
        items = db.session.query(ItemEstoque).all()
        
        total_corrigidos = 0
        
        for item in items:
            tipo_correto = item.tipo or ''  # Descrição do tipo - JÁ ESTÁ CORRETO
            dimensao_extraida = extrair_dimensao(item.un)  # Dimensão vinha em UN
            
            # Aplicar as correções
            item.descricao = tipo_correto  # DESCRIÇÃO = TIPO (verdadeira descrição)
            item.dimensao = dimensao_extraida  # DIMENSÃO = o que estava em UN
            item.un = 'UN'  # UN sempre 'UN' (unidade de medida)
            # item.endereco (LOCAL) permanece como está (categoria)
            # item.tipo permanece como está
            
            total_corrigidos += 1
            
            print(f"✅ Item {item.codigo}:")
            print(f"   TIPO: {item.tipo[:50]}")
            print(f"   DESCRIÇÃO: {item.descricao[:50]}")
            print(f"   LOCAL: {item.endereco}")
            print(f"   UN: {item.un}")
            print(f"   DIMENSÃO: {item.dimensao}")
            print()
        
        # Confirmar as alterações
        try:
            db.session.commit()
            print(f"\n✅ SUCESSO! {total_corrigidos} itens corrigidos e salvos no banco de dados.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao salvar: {e}")
            return False

if __name__ == '__main__':
    sucesso = corrigir_dados()
    exit(0 if sucesso else 1)
