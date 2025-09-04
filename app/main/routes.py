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
    lista_produtos = Produto.query.order_by(Produto.id).all()
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

        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        valor_fornecedor_real = to_float(request.form.get('valor_fornecedor_real'))
        desconto_fornecedor_percentual = to_float(request.form.get('desconto_fornecedor_percentual'))
        frete_real = to_float(request.form.get('frete_real'))
        ipi_tipo = request.form.get('ipi_tipo')
        ipi_valor_form = to_float(request.form.get('ipi_valor'))
        difal_percentual = to_float(request.form.get('difal_percentual'))
        imposto_venda_percentual = to_float(request.form.get('imposto_venda_percentual'))
        metodo_precificacao = request.form.get('metodo_precificacao')
        valor_metodo = to_float(request.form.get('valor_metodo'))
        
        valor_compra_desconto = valor_fornecedor_real * (1 - (desconto_fornecedor_percentual / 100))
        
        valor_ipi = 0.0
        if ipi_tipo == 'percentual':
            if ipi_valor_form > 0:
                valor_ipi = valor_compra_desconto - (valor_compra_desconto / (1 + (ipi_valor_form / 100)))
        else:
            valor_ipi = ipi_valor_form

        base_calculo_difal = (valor_compra_desconto - valor_ipi) + frete_real
        valor_difal = base_calculo_difal * (difal_percentual / 100)
        custo_total = valor_compra_desconto + frete_real + valor_difal

        preco_a_vista = 0.0
        if metodo_precificacao == 'margem':
            margem_lucro_percentual = valor_metodo
            denominador = (1 - (imposto_venda_percentual / 100) - (margem_lucro_percentual / 100))
            if denominador > 0: preco_a_vista = custo_total / denominador
        elif metodo_precificacao == 'lucro_alvo':
            lucro_alvo_real = valor_metodo
            denominador = (1 - (imposto_venda_percentual / 100))
            if denominador > 0: preco_a_vista = (custo_total + lucro_alvo_real) / denominador
        elif metodo_precificacao == 'preco_final':
            preco_a_vista = valor_metodo

        valor_imposto_venda = preco_a_vista * (imposto_venda_percentual / 100)
        lucro_liquido_real = preco_a_vista - custo_total - valor_imposto_venda
        
        if produto_id:
            produto.codigo = codigo
            produto.nome = nome
            produto.valor_fornecedor_real = valor_fornecedor_real
            produto.desconto_fornecedor_percentual = desconto_fornecedor_percentual
            produto.frete_real = frete_real
            produto.ipi_valor = ipi_valor_form
            produto.ipi_tipo = ipi_tipo
            produto.difal_percentual = difal_percentual
            produto.imposto_venda_percentual = imposto_venda_percentual
            produto.metodo_precificacao = metodo_precificacao
            produto.valor_metodo = valor_metodo
            produto.custo_total = custo_total
            produto.preco_a_vista = preco_a_vista
            produto.lucro_liquido_real = lucro_liquido_real
            flash('Produto atualizado com sucesso!', 'success')
        else:
            novo_produto = Produto(
                codigo=codigo, nome=nome, valor_fornecedor_real=valor_fornecedor_real,
                desconto_fornecedor_percentual=desconto_fornecedor_percentual, frete_real=frete_real,
                ipi_valor=ipi_valor_form, ipi_tipo=ipi_tipo, difal_percentual=difal_percentual, 
                imposto_venda_percentual=imposto_venda_percentual, metodo_precificacao=metodo_precificacao,
                valor_metodo=valor_metodo, custo_total=custo_total,
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

# --- ROTAS DE TAXAS ---

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
        
        coeficiente = 0.0
        if taxa_percentual >= 0 and taxa_percentual < 100:
            coeficiente = 1 - (taxa_percentual / 100)

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