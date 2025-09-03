from . import db, login_manager
from flask_login import UserMixin

# O decorador @login_manager.user_loader conecta o Flask-Login com nosso modelo de usuário
@login_manager.user_loader
def load_user(user_id):
    # Como temos um usuário fixo, retornamos o objeto User se o ID for '1'
    return User.query.get(int(user_id))

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    valor_fornecedor_real = db.Column(db.Float, nullable=False)
    desconto_fornecedor_percentual = db.Column(db.Float, default=0.0)
    frete_real = db.Column(db.Float, default=0.0)
    ipi_valor = db.Column(db.Float, default=0.0)
    difal_percentual = db.Column(db.Float, default=0.0)
    custo_total = db.Column(db.Float, nullable=True)
    preco_a_vista = db.Column(db.Float, nullable=True)
    lucro_liquido_real = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Produto {self.nome}>'

class TaxaPagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metodo = db.Column(db.String(80), unique=True, nullable=False)
    taxa_percentual = db.Column(db.Float, nullable=False)
    coeficiente = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<TaxaPagamento {self.metodo}>'

# Embora nosso usuário seja fixo por enquanto, criar um modelo ajuda na estrutura
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # Em um app real, a senha seria um hash, não texto puro
    # password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'