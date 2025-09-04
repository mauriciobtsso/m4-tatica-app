import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

def format_currency(value):
    if value is None:
        return "N/A"
    formatted_value = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted_value}"

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-de-fallback-muito-segura')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    db.init_app(app)
    login_manager.init_app(app)

    app.jinja_env.filters['currency'] = format_currency

    # AQUI ESTÁ A CORREÇÃO: Importamos o 'main' do pacote app.main
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    with app.app_context():
        from . import models
        db.create_all()

    return app