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
    produto = None
    if produto_id:
        produto = Produto.query.get_or_404(produto_id)
            
    if request.method == 'POST':
        def to_float(value):
            if not value: return 0.0
            cleaned_value = str(value).replace('R$', '').replace('.', '').replace('%', '').strip()
            cleaned_value = cleaned_value.replace(',', '.')
            if not cleaned_value: return 0.0
            return float(cleaned_value)

        codigo = request.form['codigo']
        nome = request.form['nome']
        valor_fornecedor_real = to_float(request.form.get('valor_fornecedor_real'))
        desconto_fornecedor_percentual = to_float(request.form.get('desconto_fornecedor_percentual'))
        frete_real = to_float(request.form.get('frete_real'))
        ipi_valor = to_float(request.form.get('ipi_valor'))
        difal_percentual = to_float(request.form.get('difal_percentual'))
        metodo_precificacao = request.form['metodo_precificacao']
        valor_metodo = to_float(request.form.get('valor_metodo'))
        
        custo_base = valor_fornecedor_real * (1 - desconto_fornecedor_percentual / 100)
        custo_total = custo_base + frete_real + ipi_valor + (custo_base * difal_percentual / 100)
        preco_a_vista = 0.0
        lucro_liquido_real = 0.0
        imposto_venda_percentual = 0.0
        
        if metodo_precificacao == 'margem':
            margem_lucro_percentual = valor_metodo
            denominador = (1 - (imposto_venda_percentual / 100) - (margem_lucro_percentual / 100))
            if denominador > 0: preco_a_vista = custo_total / denominador
            lucro_liquido_real = preco_a_vista - custo_total
        elif metodo_precificacao == 'lucro_alvo':
            lucro_alvo_real = valor_metodo
            denominador = (1 - (imposto_venda_percentual / 100))
            if denominador > 0: preco_a_vista = (custo_total + lucro_alvo_real) / denominador
            lucro_liquido_real = preco_a_vista - custo_total
        elif metodo_precificacao == 'preco_final':
            preco_a_vista = valor_metodo
            lucro_liquido_real = preco_a_vista - custo_total
        
        if produto_id:
            produto.codigo = codigo
            produto.nome = nome
            produto.valor_fornecedor_real = valor_fornecedor_real
            produto.desconto_fornecedor_percentual = desconto_fornecedor_percentual
            produto.frete_real = frete_real
            produto.ipi_valor = ipi_valor
            produto.difal_percentual = difal_percentual
            produto.custo_total = custo_total
            produto.preco_a_vista = preco_a_vista
            produto.lucro_liquido_real = lucro_liquido_real
            flash('Produto atualizado com sucesso!', 'success')
        else:
            novo_produto = Produto(
                codigo=codigo, nome=nome, valor_fornecedor_real=valor_fornecedor_real,
                desconto_fornecedor_percentual=desconto_fornecedor_percentual, frete_real=frete_real,
                ipi_valor=ipi_valor, difal_percentual=difal_percentual, custo_total=custo_total,
                preco_a_vista=preco_a_vista, lucro_liquido_real=lucro_liquido_real
            )
            db.session.add(novo_produto)
            flash('Produto salvo com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('main.produtos'))

    taxas = TaxaPagamento.query.all()
    taxas_dict = {t.metodo: t for t in taxas}
    return render_template("produto_form.html", produto=produto, taxas_dict=taxas_dict)

@main.route('/produto/excluir/<int:produto_id>')
@login_required
def excluir_produto(produto_id):
    produto_para_excluir = Produto.query.get_or_404(produto_id)
    db.session.delete(produto_para_excluir)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'danger')
    return redirect(url_for('main.produtos'))

@main.route("/exportar/produtos_csv")
@login_required
def exportar_produtos_csv():
    produtos = Produto.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["SKU", "Nome do Produto", "Custo Total (R$)", "Preço à Vista (R$)", "Lucro Líquido (R$)"])
    for produto in produtos:
        cw.writerow([
            produto.codigo, produto.nome,
            "%.2f" % produto.custo_total if produto.custo_total is not None else "N/A",
            "%.2f" % produto.preco_a_vista if produto.preco_a_vista is not None else "N/A",
            "%.2f" % produto.lucro_liquido_real if produto.lucro_liquido_real is not None else "N/A"
        ])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=produtos.csv"
    output.headers["Content-type"] = "text/csv"
    return output