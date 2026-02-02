import sqlite3
import re
from collections import defaultdict

db_file = 'database.db'
input_file = r'c:\Users\ALMOXARIFADO_4\OneDrive\Desktop\descrição.txt'

print("🔄 ATUALIZAÇÃO AVANÇADA DE DESCRIÇÕES")
print("=" * 80)

try:
    # Ler o arquivo
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print("\n📋 PROCESSANDO ARQUIVO...")
    
    # Dividir por linhas
    lines = content.split('\n')
    
    # Dicionário para armazenar descrições
    descricoes_map = defaultdict(list)
    
    for line in lines[1:]:  # Pular cabeçalho
        if not line.strip() or len(line) < 10:
            continue
        
        try:
            # Regex para extrair código no início da linha
            match = re.match(r'^(\S+)\s+(.+)$', line)
            if not match:
                continue
            
            codigo = match.group(1).strip()
            resto = match.group(2).strip()
            
            if not codigo or codigo == '-' or len(codigo) > 20:
                continue
            
            # Se resto tem muito conteúdo, extrair descrição
            if len(resto) > 5:
                # Limpar a descrição
                desc = ' '.join(resto.split())[:200]
                if desc and desc not in ['-', '=']:
                    descricoes_map[codigo].append(desc)
        
        except:
            continue
    
    # Para cada código, pegar a melhor descrição (a mais longa e completa)
    descricoes_final = {}
    for codigo, descs in descricoes_map.items():
        # Pegar a descrição mais longa (provavelmente a mais completa)
        melhor_desc = max(descs, key=len) if descs else ""
        if melhor_desc and melhor_desc not in ['-', '=', '']:
            descricoes_final[codigo] = melhor_desc
    
    print(f"  ✅ {len(descricoes_final)} descrições extraídas")
    
    # Conectar ao banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Primeiro, pegar itens sem descrição
    cursor.execute("""
        SELECT id, codigo, descricao FROM item_estoque 
        WHERE descricao IS NULL OR descricao = '' OR descricao = '-' OR descricao = '='
    """)
    
    itens_sem_desc = cursor.fetchall()
    print(f"\n📊 Itens sem descrição no banco: {len(itens_sem_desc)}")
    
    # Atualizar descrições
    print("\n🔧 ATUALIZANDO BANCO DE DADOS...")
    
    atualizados = 0
    nao_encontrados = []
    
    for item_id, codigo, desc_atual in itens_sem_desc:
        if codigo in descricoes_final:
            nova_desc = descricoes_final[codigo]
            try:
                cursor.execute("""
                    UPDATE item_estoque 
                    SET descricao = ?
                    WHERE id = ?
                """, (nova_desc, item_id))
                
                if cursor.rowcount > 0:
                    atualizados += 1
                    print(f"  ✅ {codigo}: {nova_desc[:60]}...")
            
            except Exception as e:
                print(f"  ❌ Erro ao atualizar {codigo}: {e}")
        else:
            nao_encontrados.append(codigo)
    
    conn.commit()
    
    # Verificar quantos ainda faltam
    cursor.execute("""
        SELECT COUNT(*) FROM item_estoque 
        WHERE descricao IS NULL OR descricao = '' OR descricao = '-' OR descricao = '='
    """)
    
    ainda_sem = cursor.fetchone()[0]
    conn.close()
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO:")
    print(f"  ✅ Descrições atualizadas: {atualizados}")
    print(f"  ⚠️  Itens ainda sem descrição: {ainda_sem}")
    print(f"  ❌ Códigos não encontrados: {len(nao_encontrados)}")
    
    if nao_encontrados and len(nao_encontrados) <= 10:
        print(f"\n  Códigos não encontrados: {', '.join(nao_encontrados)}")
    
    print("\n✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERRO GERAL: {e}")
    import traceback
    traceback.print_exc()
