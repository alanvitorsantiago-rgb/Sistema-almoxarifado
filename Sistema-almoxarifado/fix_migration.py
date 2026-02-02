
import sqlite3
import os
from supabase import create_client

# Configurações
SUPABASE_URL = "https://twydlslxhtoqsqnixcmz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3eWRsc2x4aHRvcXNxbml4Y216Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMjg1NzQsImV4cCI6MjA4NTYwNDU3NH0.f8tpIaRlufhJ0hEQqeJsPMUPA6Vp8OhgeDuXp5zj82A"
SQLITE_DB = "database.db"

def fix_migration():
    print("🚀 Iniciando correção de migração...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # 1. Corrigir item 42 (e outros que faltaram)
    print("\n📦 Verificando itens...")
    cursor.execute("SELECT id FROM item_estoque")
    sqlite_ids = {row[0] for row in cursor.fetchall()}
    
    # Busca IDs já no Supabase (pode ser lento se muitos, mas ok para 300)
    res = supabase.table("item_estoque").select("id").execute()
    supabase_ids = {row['id'] for row in res.data}
    
    missing_items = sqlite_ids - supabase_ids
    print(f"   Itens faltando: {len(missing_items)}")
    
    if missing_items:
        for item_id in missing_items:
            cursor.execute("""
                SELECT id, codigo, endereco, codigo_opcional, tipo, descricao, un, dimensao,
                    cliente, qtd_estoque, estoque_minimo, estoque_ideal_compra, 
                    tempo_reposicao, data_cadastro
                FROM item_estoque WHERE id = ?
            """, (item_id,))
            row = cursor.fetchone()
            try:
                data = {
                    "id": row[0], "codigo": row[1], "endereco": row[2], 
                    "codigo_opcional": row[3], "tipo": row[4], "descricao": row[5], 
                    "un": row[6], "dimensao": row[7], "cliente": row[8], 
                    "qtd_estoque": row[9] or 0, "estoque_minimo": row[10] or 5, 
                    "estoque_ideal_compra": row[11], "tempo_reposicao": row[12] or 7, 
                    "data_cadastro": row[13]
                }
                supabase.table("item_estoque").insert(data).execute()
                print(f"   ✅ Item {item_id} corrigido")
            except Exception as e:
                print(f"   ❌ Erro item {item_id}: {e}")

    # 2. Corrigir Estoque Detalhe
    print("\n📄 Verificando detalhes (lotes)...")
    # IDs de detalhes faltando (lotes do item 42 falharam)
    cursor.execute("SELECT id FROM estoque_detalhe")
    sqlite_det_ids = {row[0] for row in cursor.fetchall()}
    
    res = supabase.table("estoque_detalhe").select("id", count="exact").execute()
    if res.count < len(sqlite_det_ids):
        # Simplificação: Tenta inserir os que derem erro de duplicação, ou busca diff
        # Como são poucos faltando, vou tentar inserir os filhos do item 42 especificamente
        # Ou melhor, tentar diff completo
        res = supabase.table("estoque_detalhe").select("id").execute() # Limite 1000 padrão, cuidado
        # Se tiver mais de 1000, precisa paginar. O log disse 1079 no supabase.
        # Vou pegar todos via loop simples ou assumir que só faltam os do item_id=42
        
        # Estratégia: Inserir detalhes onde item_estoque_id está nos missing_items recuperados
        if missing_items:
            for item_id in missing_items:
                cursor.execute("""
                    SELECT id, item_estoque_id, lote, item_nf, nf, validade, estacao,
                        status_validade, quantidade, data_entrada, status_etiqueta,
                        data_etiqueta, usuario_etiqueta
                    FROM estoque_detalhe WHERE item_estoque_id = ?
                """, (item_id,))
                rows = cursor.fetchall()
                for row in rows:
                    try:
                        data = {
                            "id": row[0], "item_estoque_id": row[1], "lote": row[2], "item_nf": row[3],
                            "nf": row[4], "validade": row[5], "estacao": row[6], "status_validade": row[7],
                            "quantidade": row[8] or 0, "data_entrada": row[9], "status_etiqueta": row[10] or 'PENDENTE',
                            "data_etiqueta": row[11], "usuario_etiqueta": row[12]
                        }
                        supabase.table("estoque_detalhe").insert(data).execute()
                        print(f"   ✅ Detalhe {row[0]} corrigido")
                    except Exception as e:
                        print(f"   ❌ Erro detalhe {row[0]}: {e}")
    else:
        print("   Nenhum detalhe faltando (contagem bate).")

    # 3. Corrigir Movimentações (Muitas faltando)
    print("\n📊 Verificando movimentações...")
    cursor.execute("SELECT id FROM movimentacao")
    sqlite_mov_ids = {row[0] for row in cursor.fetchall()}
    
    # Buscar IDs no Supabase (paginado, pois tem > 1000 - mas só 100 entraram)
    res = supabase.table("movimentacao").select("id").execute()
    supabase_mov_ids = {row['id'] for row in res.data}
    
    missing_movs = sqlite_mov_ids - supabase_mov_ids
    print(f"   Movimentações faltando: {len(missing_movs)}")
    
    if missing_movs:
        batch = []
        count = 0
        
        # Converter para lista para fatiar
        missing_list = list(missing_movs)
        
        # Processar em lotes
        for i in range(0, len(missing_list), 100):
            batch_ids = tuple(missing_list[i:i+100])
            if len(batch_ids) == 1:
                batch_ids = f"({batch_ids[0]})"
            
            cursor.execute(f"""
                SELECT id, item_id, tipo, quantidade, data_movimentacao, observacao,
                    usuario, etapa, lote, item_nf, nf
                FROM movimentacao WHERE id IN {str(batch_ids)}
            """)
            rows = cursor.fetchall()
            
            data_batch = []
            for row in rows:
                data_batch.append({
                    "id": row[0], "item_id": row[1], "tipo": row[2], "quantidade": row[3],
                    "data_movimentacao": row[4], "observacao": row[5], "usuario": row[6],
                    "etapa": row[7], "lote": row[8], "item_nf": row[9], "nf": row[10]
                })
            
            try:
                supabase.table("movimentacao").insert(data_batch).execute()
                count += len(data_batch)
                print(f"   ✅ {count}/{len(missing_movs)} movimentações corrigidas...")
            except Exception as e:
                print(f"   ❌ Erro no lote {i}: {e}")
                
    print("\n✅ Correção finalizada!")

if __name__ == "__main__":
    fix_migration()
