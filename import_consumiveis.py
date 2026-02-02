import sqlite3
import csv
from datetime import datetime

# Ler o arquivo CSV de consumíveis
csv_file = 'exemplo_consumiveis.csv'
db_file = 'database.db'

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print("📥 IMPORTANDO CONSUMÍVEIS DO ARQUIVO CSV")
print("=" * 60)

try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            # Converter os dados
            n_produto = row['Nº PRODUTO'].strip()
            status_estoque = row['STATUS ESTOQUE'].strip()
            status_consumo = row['STATUS CONSUMO'].strip()
            codigo_produto = row['CÓDIGO PRODUTO'].strip()
            descricao = row['DESCRIÇÃO DO PRODUTO'].strip()
            unidade_medida = row['UNIDADE MEDIDA'].strip()
            categoria = row['CATEGORIA'].strip()
            fornecedor = row['FORNECEDOR'].strip() if row['FORNECEDOR'].strip() else None
            fornecedor2 = row['FORNECEDOR 2'].strip() if row['FORNECEDOR 2'].strip() else None
            valor_unitario = float(row['VALOR UNITÁRIO'].replace(',', '.')) if row['VALOR UNITÁRIO'] else 0
            lead_time = int(row['LEAD TIME']) if row['LEAD TIME'] else 7
            estoque_seguranca = float(row['% ESTOQUE DE SEGURANÇA'].replace(',', '.')) if row['% ESTOQUE DE SEGURANÇA'] else 0
            estoque_minimo = float(row['ESTOQUE MÍNIMO POR ATUALIZAR'].replace(',', '.')) if row['ESTOQUE MÍNIMO POR ATUALIZAR'] else 0
            quantidade_atual = float(row['ESTOQUE ATUAL'].replace(',', '.')) if row['ESTOQUE ATUAL'] else 0
            
            # Inserir no banco
            cursor.execute("""
                INSERT INTO consumivel_estoque 
                (n_produto, status_estoque, status_consumo, codigo_produto, descricao, 
                 unidade_medida, categoria, fornecedor, fornecedor2, valor_unitario, 
                 lead_time, estoque_seguranca, estoque_minimo, quantidade_atual, 
                 data_cadastro, data_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (n_produto, status_estoque, status_consumo, codigo_produto, descricao,
                 unidade_medida, categoria, fornecedor, fornecedor2, valor_unitario,
                 lead_time, estoque_seguranca, estoque_minimo, quantidade_atual,
                 datetime.now(), datetime.now()))
            
            count += 1
            print(f"  ✅ {n_produto}: {descricao} ({quantidade_atual} {unidade_medida})")
        
        conn.commit()
        print()
        print("=" * 60)
        print(f"✅ {count} consumíveis importados com sucesso!")
        
        # Verificar
        cursor.execute("SELECT COUNT(*) FROM consumivel_estoque")
        total = cursor.fetchone()[0]
        print(f"📊 Total de consumíveis no banco: {total}")
        
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
finally:
    conn.close()
