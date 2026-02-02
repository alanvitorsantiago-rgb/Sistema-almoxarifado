import sqlite3
import re
from datetime import datetime

db_file = 'database.db'
input_file = 'c:\\Users\\ALMOXARIFADO_4\\OneDrive\\Desktop\\descrição.txt'

print("🔄 ATUALIZANDO DESCRIÇÕES DOS ITENS")
print("=" * 80)

try:
    # Ler o arquivo
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Processar linhas para extrair código e descrição
    print("\n📋 PROCESSANDO ARQUIVO...")
    
    descricoes_map = {}
    
    for line in lines[1:]:  # Pular cabeçalho
        if not line.strip():
            continue
        
        try:
            # Dividir por espaços/tabs
            parts = line.split()
            if len(parts) < 3:
                continue
            
            # O primeiro campo é o código
            codigo = parts[0].strip()
            
            if not codigo or codigo == '-':
                continue
            
            # O resto é a descrição (tudo depois do código até o tipo ou local)
            # Vamos pegar a linha toda e extrair melhor
            match = re.match(r'(\S+)\s+(.+)', line)
            if not match:
                continue
            
            codigo = match.group(1).strip()
            resto = match.group(2).strip()
            
            # Extrair descrição - está entre o código opcional e o tipo
            # Formato: CÓDIGO CÓDIGO_OPCIONAL TIPO DESCRIÇÃO LOCAL UN DIM CLIENTE LOTE ITEM_NF
            # Vamos tentar extrair pelo padrão
            
            # Se já temos esse código, pular
            if codigo in descricoes_map:
                continue
            
            # Tentar extrair a descrição
            # Procurar por palavras-chave: PAINEL, HARDWARE, PERECÁVEIS, MANTA, KIT
            tipos = ['PAINEL', 'HARDWARE', 'PERECÁVEIS', 'MANTA', 'KIT', 'INDEFINIDO']
            
            descricao = ""
            tipo_encontrado = None
            
            for tipo in tipos:
                if tipo in resto:
                    # Encontrou o tipo, tudo antes dele é código/código_opcional
                    partes = resto.split(tipo)
                    if len(partes) >= 2:
                        tipo_encontrado = tipo
                        # A descrição é tudo depois do tipo
                        desc_raw = partes[1].strip()
                        
                        # Limpar espaços extras
                        descricao = ' '.join(desc_raw.split())
                        
                        # Limitar a 255 caracteres
                        descricao = descricao[:255]
                        
                        break
            
            if descricao:
                descricoes_map[codigo] = descricao
        
        except Exception as e:
            continue
    
    print(f"  ✅ {len(descricoes_map)} descrições extraídas")
    
    # Conectar ao banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Atualizar descrições
    print("\n🔧 ATUALIZANDO BANCO DE DADOS...")
    
    atualizados = 0
    nao_encontrados = []
    
    for codigo, descricao in descricoes_map.items():
        try:
            cursor.execute("""
                UPDATE item_estoque 
                SET descricao = ?
                WHERE codigo = ?
            """, (descricao, codigo))
            
            if cursor.rowcount > 0:
                atualizados += 1
                print(f"  ✅ {codigo}: {descricao[:50]}...")
            else:
                nao_encontrados.append(codigo)
        
        except Exception as e:
            print(f"  ❌ Erro ao atualizar {codigo}: {e}")
    
    conn.commit()
    conn.close()
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO:")
    print(f"  ✅ Descrições atualizadas: {atualizados}")
    print(f"  ⚠️  Códigos não encontrados: {len(nao_encontrados)}")
    
    if nao_encontrados and len(nao_encontrados) <= 20:
        print(f"\n  Códigos não encontrados: {', '.join(nao_encontrados[:20])}")
    
    print("\n✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERRO GERAL: {e}")
    import traceback
    traceback.print_exc()
