import sqlite3
from datetime import datetime, timedelta
from dateutil import parser

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Obter a data de hoje
hoje = datetime.now().date()

print("🔍 MOVIMENTAÇÕES DE HOJE")
print("=" * 80)

# Verificar movimentações de hoje
cursor.execute("""
    SELECT m.id, m.item_id, i.descricao, i.codigo, m.tipo, m.quantidade, 
           m.data_movimentacao, m.lote, m.item_nf, m.nf, m.usuario
    FROM movimentacao m
    JOIN item_estoque i ON m.item_id = i.id
    WHERE DATE(m.data_movimentacao) = ?
    ORDER BY m.data_movimentacao DESC
""", (hoje,))

movimentacoes = cursor.fetchall()

if not movimentacoes:
    print("❌ Nenhuma movimentação encontrada para hoje")
else:
    print(f"✅ Encontradas {len(movimentacoes)} movimentações de hoje:\n")
    
    for mov in movimentacoes:
        mov_id, item_id, descricao, codigo, tipo, quantidade, data_mov, lote, item_nf, nf, usuario = mov
        print(f"ID: {mov_id}")
        print(f"  Item: {codigo} - {descricao}")
        print(f"  Tipo: {tipo} | Quantidade: {quantidade}")
        print(f"  Lote: {lote} | Item NF: {item_nf} | NF: {nf}")
        print(f"  Usuário: {usuario} | Data: {data_mov}")
        print()

print("=" * 80)

# Contar por tipo
cursor.execute("""
    SELECT tipo, COUNT(*) as count, SUM(quantidade) as total
    FROM movimentacao
    WHERE DATE(data_movimentacao) = ?
    GROUP BY tipo
""", (hoje,))

resumo = cursor.fetchall()
if resumo:
    print("📊 RESUMO POR TIPO:")
    for tipo, count, total in resumo:
        print(f"  {tipo}: {count} movimentações | Total: {total}")

conn.close()
