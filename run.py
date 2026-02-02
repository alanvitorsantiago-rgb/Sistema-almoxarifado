from app import app, socketio, criar_banco_de_dados

# --- CONTROLE DE AMBIENTE ---
# Altere para False para usar o servidor de produção (Waitress)
MODO_DEBUG = True

if __name__ == "__main__":
    # Garante que o banco de dados e o usuário admin existam antes de iniciar o servidor.
    # Isso é executado uma vez, sempre que o servidor é iniciado via 'run.py'.
    with app.app_context():
        criar_banco_de_dados()

    if MODO_DEBUG:
        # --- MODO DE DEPURACAO ---
        # Mostra erros detalhados no navegador e reinicia automaticamente após alterações no código.
        # Ideal para desenvolvimento.
        print("!!! SERVIDOR EM MODO DE DEPURAÇÃO ATIVADO !!!")
        print("Acesse em http://127.0.0.1:5000") 
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
    else:
        # --- MODO DE PRODUÇÃO ---
        # Servidor otimizado para estabilidade e segurança, usado quando o sistema está pronto.
        print("Servidor de produção (Waitress) iniciado em http://0.0.0.0:5000")
        socketio.run(app, host="0.0.0.0", port=5000)