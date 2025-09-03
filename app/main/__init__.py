from flask import Blueprint

main = Blueprint('main', __name__)

# A linha "from . import models" foi removida daqui.
# Este arquivo só precisa importar as rotas do seu próprio módulo.
from . import routes