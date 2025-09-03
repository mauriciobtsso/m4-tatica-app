from flask import Blueprint

main = Blueprint('main', __name__)

# Importamos as rotas no final para evitar importações circulares
from . import routes, models