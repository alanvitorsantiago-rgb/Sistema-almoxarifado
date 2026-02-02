"""
Ponto de entrada para Vercel Serverless Functions.
Este arquivo importa e expõe a aplicação Flask para a Vercel.
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importa a aplicação Flask do main.py
from main import app

# Vercel procura por uma variável chamada 'app' ou 'application'
# ou uma função handler
def handler(request):
    """Handler para Vercel Serverless Functions"""
    return app(request.environ, lambda *args: None)

# Exporta a aplicação
application = app

# Para compatibilidade com Vercel
if __name__ == "__main__":
    app.run()
