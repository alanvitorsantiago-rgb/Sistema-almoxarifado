from app import app, criar_banco_de_dados
import socket
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

PORTA = 8080

def obter_ip_local():
    """Tenta descobrir o IP local da máquina na rede."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conecta a um IP externo (não envia dados) para obter o IP da interface de rede principal
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1" # Retorna localhost em caso de falha
    finally:
        s.close()

if __name__ == "__main__":
    # Garante que o banco de dados e o usuário admin existam antes de iniciar o servidor.
    criar_banco_de_dados(app.app_context())

    print("\n!!! SERVIDOR EM MODO DE DEPURAÇÃO (FLASK) !!!")
    print(f"    Acesse em seu navegador: http://{obter_ip_local()}:{PORTA}")
    # Executa o servidor de desenvolvimento do Flask, acessível na rede local.
    app.run(debug=True, host="0.0.0.0", port=PORTA)