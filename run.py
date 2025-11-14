import os
from app import create_app

# Cria a instância da aplicação usando a factory
# O Render define a variável de ambiente NODE_ENV=production, que podemos usar para carregar a config correta.
config_name = os.getenv('FLASK_CONFIG', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()