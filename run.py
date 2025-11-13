from waitress import serve
from app import app, criar_banco_de_dados
import socket
import os
from pyngrok import ngrok, conf
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONTROLE DE AMBIENTE ---
# Altere para False para usar o servidor de produção (Waitress)
# Definido como False para usar Waitress por padrão, que é mais estável e não requer permissões elevadas.
MODO_DEBUG = True
PORTA = 8080
# --- CONFIGURAÇÃO NGROK ---
# Coloque seu Authtoken do ngrok aqui. Obtenha em: https://dashboard.ngrok.com/get-started/your-authtoken
# Você pode definir como uma variável de ambiente NGROK_AUTHTOKEN ou colar diretamente aqui.
NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN", None)
NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", None) # Lê o domínio do arquivo .env
def obter_ip_local():
    """Tenta descobrir o IP local da máquina na rede."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conecta a um IP externo (não envia dados) para obter o IP da interface de rede principal
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1" # Retorna localhost em caso de falha

if __name__ == "__main__":
    # Garante que o banco de dados e o usuário admin existam antes de iniciar o servidor.
    # Isso é executado uma vez, sempre que o servidor é iniciado via 'run.py'.
    criar_banco_de_dados(app.app_context())

    # --- INICIALIZAÇÃO DO NGROK ---
    if not MODO_DEBUG:
        try:
            if NGROK_AUTHTOKEN:
                ngrok.set_auth_token(NGROK_AUTHTOKEN)
            
            # Se um domínio fixo foi definido no .env, usa ele. Senão, cria um aleatório.
            if NGROK_DOMAIN:
                public_url = ngrok.connect(PORTA, "http", domain=NGROK_DOMAIN)
            else:
                public_url = ngrok.connect(PORTA, "http")
        except Exception as e:
            print(f" !!! ERRO AO INICIAR O NGROK: {e}")
            print("     O servidor continuará localmente, mas não estará acessível externamente via ngrok.")

    local_ip = obter_ip_local()

    if MODO_DEBUG:
        # --- MODO DE DEPURACAO ---
        print("\n!!! SERVIDOR EM MODO DE DEPURAÇÃO (FLASK) !!!")
        print(f"    SERVIDOR DISPONÍVEL EM: http://{local_ip}:{PORTA}")
        app.run(debug=True, host="0.0.0.0", port=PORTA)
    else:
        # --- MODO DE PRODUÇÃO ---
        print("\n--- SERVIDOR DE PRODUÇÃO (WAITRESS) ---")
        print(f"    ACESSO LOCAL: http://{local_ip}:{PORTA}")
        if 'public_url' in locals():
            print(f"    ACESSO EXTERNO: {public_url}")
            print("    (Use o link acima para acessar de outros computadores/redes)")
        serve(app, host="0.0.0.0", port=PORTA)