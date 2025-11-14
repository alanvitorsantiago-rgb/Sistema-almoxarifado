import os

class Config:
    """Configurações base."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uma-chave-padrao-para-desenvolvimento-deve-ser-alterada')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Outras configurações globais

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

class ProductionConfig(Config):
    """Configurações de produção."""
    DEBUG = False
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # A URL do Render vem como 'postgres://...', mas SQLAlchemy prefere 'postgresql://...'
        SQLALCHEMY_DATABASE_URI = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        # Fallback para SQLite se DATABASE_URL não estiver definida, embora não seja o ideal para produção.
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
