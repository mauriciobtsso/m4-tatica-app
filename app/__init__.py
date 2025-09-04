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

# Função para formatar valores como moeda brasileira
def format_currency(value):
    if value is None:
        return "N/A"
    # Formata com 2 casas decimais e separador de milhar, depois inverte . e ,
    formatted_value = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted_value}"

def create_app():
    app = Flask(__name__)

    # ... (o resto das configurações continua igual)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-de-fallback-muito-segura')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    db.init_app(app)
    login_manager.init_app(app)

    # Registra nosso filtro de moeda customizado no ambiente do Jinja2
    app.jinja_env.filters['currency'] = format_currency

    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    with app.app_context():
        from . import models
        db.create_all()

    return app