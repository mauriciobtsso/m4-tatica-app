from flask import render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, login_user, logout_user, current_user
from . import main
from .. import db
from ..models import Produto, User, TaxaPagamento
import io
import csv

# --- ROTAS DE AUTENTICAÇÃO E DASHBOARD ---

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            user = User.query.get(1)
            if not user:
                 admin_user = User(id=1, username='admin')
                 db.session.add(admin_user)
                 db.session.commit()
                 user = admin_user
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("main.login"))

@main.route("/")
@login_required
def dashboard():
    produtos = Produto.query.all()
    total_lucro = 0.0
    total_preco_venda = 0.0
    produto_mais_lucrativo = None

    for produto in produtos:
        if produto.lucro_liquido_real is not None and produto.preco_a_vista is not None:
            total_lucro += produto.lucro_liquido_real
            total_preco_venda += produto.preco_a_vista
            if produto_mais_lucrativo is None or produto.lucro_liquido_real > produto_mais_lucrativo.lucro_liquido_real:
                produto_mais_lucrativo = produto

    media_margem_lucro = 0.0
    if total_preco_venda > 0:
        media_margem_lucro = (total_lucro / total_preco_venda) * 100

    return render_template("dashboard.html", media_margem_lucro=media_margem_lucro, produto_mais_lucrativo=produto_mais_lucrativo)

# --- ROTAS DE PRODUTOS ---

@main.route("/produtos")
@login_required
def produtos():
    lista_produtos = Produto.query.all()
    return render_template('produtos.html', produtos=lista_produtos)

@main.route("/produto/novo", methods=["GET", "POST"])
@main.route("/produto/editar/<int:produto_id>", methods=["GET", "POST"])
@login_required
def gerenciar_produto(produto_id=None):
    # (código completo de gerenciar_produto que já implementamos)
    produto = None
    if produto_id:
        produto = Produto.query.get_or_404(produto_id)
    # ... (restante do código)

@main.route('/produto/excluir/<int:produto_id>')
@login_required
def excluir_produto(produto_id):
    # (código completo de excluir_produto que já implementamos)
    produto_para_excluir = Produto.query.get_or_404(produto_id)
    # ... (restante do código)

@main.route("/exportar/produtos_csv")
@login_required
def exportar_produtos_csv():
    # (código completo de exportar_produtos_csv que já implementamos)
    produtos = Produto.query.all()
    # ... (restante do código)

# --- ROTAS DE TAXAS (AGORA COMPLETAS) ---

@main.route("/taxas")
@login_required
def taxas():
    lista_taxas = TaxaPagamento.query.order_by(TaxaPagamento.id).all()
    return render_template('taxas.html', taxas=lista_taxas)

@main.route('/taxa/nova', methods=['GET', 'POST'])
@main.route('/taxa/editar/<int:taxa_id>', methods=['GET', 'POST'])
@login_required
def gerenciar_taxa(taxa_id=None):
    taxa = None
    if taxa_id:
        taxa = TaxaPagamento.query.get_or_404(taxa_id)

    if request.method == 'POST':
        def to_float(value):
            if not value: return 0.0
            cleaned_value = str(value).replace(',', '.').strip()
            if not cleaned_value: return 0.0
            return float(cleaned_value)

        metodo = request.form.get('metodo')
        taxa_percentual = to_float(request.form.get('taxa_percentual'))
        coeficiente = to_float(request.form.get('coeficiente'))

        if taxa_id:
            taxa.metodo = metodo
            taxa.taxa_percentual = taxa_percentual
            taxa.coeficiente = coeficiente
            flash('Taxa atualizada com sucesso!', 'success')
        else:
            nova_taxa = TaxaPagamento(
                metodo=metodo,
                taxa_percentual=taxa_percentual,
                coeficiente=coeficiente
            )
            db.session.add(nova_taxa)
            flash('Taxa adicionada com sucesso!', 'success')

        db.session.commit()
        return redirect(url_for('main.taxas'))

    return render_template('taxa_form.html', taxa=taxa)

@main.route('/taxa/excluir/<int:taxa_id>')
@login_required
def excluir_taxa(taxa_id):
    taxa_para_excluir = TaxaPagamento.query.get_or_404(taxa_id)
    db.session.delete(taxa_para_excluir)
    db.session.commit()
    flash('Taxa excluída com sucesso!', 'danger')
    return redirect(url_for('main.taxas'))