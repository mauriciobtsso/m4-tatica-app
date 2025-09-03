from app import create_app, db
from app.models import Produto, TaxaPagamento

# Cria a instância da aplicação usando nossa "fábrica"
app = create_app()

# Permite usar o terminal 'flask shell' com acesso fácil ao app e db
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Produto': Produto, 'TaxaPagamento': TaxaPagamento}

if __name__ == '__main__':
    app.run(debug=True)