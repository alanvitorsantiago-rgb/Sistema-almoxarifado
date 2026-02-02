import subprocess
import sqlite3
import os

print("🔍 Procurando pelo commit com consumivel_estoque...")
print()

# Obter todos os commits
result = subprocess.run(['git', 'log', '--all', '--oneline'], 
                       capture_output=True, text=True)
commits = result.stdout.strip().split('\n')

found = False
for commit_info in commits[:30]:  # Verificar últimos 30 commits
    commit_hash = commit_info.split()[0]
    
    # Tentar extrair o banco daquele commit
    try:
        subprocess.run(['git', 'show', f'{commit_hash}:database.db'], 
                      stdout=open('test_db.tmp', 'wb'), 
                      stderr=subprocess.DEVNULL, timeout=2)
        
        # Verificar se conseguiu extrair um banco válido
        if os.path.getsize('test_db.tmp') > 1000:
            conn = sqlite3.connect('test_db.tmp')
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM consumivel_estoque")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"✅ ENCONTRADO em {commit_hash}: {count} consumíveis")
                    print(f"   Mensagem: {commit_info[7:]}")
                    found = True
                    conn.close()
                    os.remove('test_db.tmp')
                    break
                conn.close()
            except:
                conn.close()
        
        os.remove('test_db.tmp')
    except:
        pass

if not found:
    print("❌ Não encontrou consumivel_estoque em nenhum commit recente")
    print("   Os dados de consumíveis podem nunca ter sido salvos no banco")
