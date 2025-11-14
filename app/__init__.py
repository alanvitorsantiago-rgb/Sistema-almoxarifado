# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'production') # Default to production for safety

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # render_as_batch=True is important for SQLite compatibility in migrations.
    migrate.init_app(app, db, render_as_batch=True) 

    login_manager.login_view = 'main.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Import and register blueprint
        from .routes import main as main_blueprint
        app.register_blueprint(main_blueprint)

        # Import and register context processor
        from .context_processors import utility_processor
        app.context_processor(utility_processor)
        
        @login_manager.user_loader
        def load_user(user_id):
            # models need to be imported within the context
            from .models import User
            return User.query.get(int(user_id))

    return app
