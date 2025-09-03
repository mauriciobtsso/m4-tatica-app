from flask import render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, login_user, logout_user, current_user
from . import main
from .. import db
from ..models import Produto, User, TaxaPagamento
import io
import csv

# --- ROTAS DE AUTENTICAÇÃO E DASHBOARD ---
# ... (código existente sem alterações)

# --- ROTAS DE PRODUTOS ---

@main.route("/produtos")
@login_required
def produtos():
    # ... (código existente sem alterações)

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

        # Capturando TODOS os campos do novo formulário
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        valor_fornecedor_real = to_float(request.form.get('valor_fornecedor_real'))
        desconto_fornecedor_percentual = to_float(request.form.get('desconto_fornecedor_percentual'))
        frete_real = to_float(request.form.get('frete_real'))
        
        # Lógica para IPI (R$ ou %)
        ipi_tipo = request.form.get('ipi_tipo')
        ipi_valor_form = to_float(request.form.get('ipi_valor'))
        
        difal_percentual = to_float(request.form.get('difal_percentual'))
        imposto_venda_percentual = to_float(request.form.get('imposto_venda_percentual'))

        metodo_precificacao = request.form.get('metodo_precificacao')
        valor_metodo = to_float(request.form.get('valor_metodo'))
        
        # --- LÓGICA DE CÁLCULO PRECISA (BASEADA NA PLANILHA) ---
        valor_compra_desconto = valor_fornecedor_real * (1 - (desconto_fornecedor_percentual / 100))
        
        valor_ipi = 0.0
        if ipi_tipo == 'percentual':
            # IPI embutido (cálculo "por dentro")
            valor_ipi = valor_compra_desconto - (valor_compra_desconto / (1 + (ipi_valor_form / 100)))
        else: # ipi_tipo == 'fixo'
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
        
        # Salvando no banco de dados
        if produto_id:
            produto.codigo = codigo
            produto.nome = nome
            produto.valor_fornecedor_real = valor_fornecedor_real
            produto.desconto_fornecedor_percentual = desconto_fornecedor_percentual
            produto.frete_real = frete_real
            produto.ipi_valor = ipi_valor_form # Salva o valor do input, não o calculado
            produto.difal_percentual = difal_percentual
            produto.custo_total = custo_total
            produto.preco_a_vista = preco_a_vista
            produto.lucro_liquido_real = lucro_liquido_real
            flash('Produto atualizado com sucesso!', 'success')
        else:
            novo_produto = Produto(
                codigo=codigo, nome=nome, valor_fornecedor_real=valor_fornecedor_real,
                desconto_fornecedor_percentual=desconto_fornecedor_percentual, frete_real=frete_real,
                ipi_valor=ipi_valor_form, difal_percentual=difal_percentual, custo_total=custo_total,
                preco_a_vista=preco_a_vista, lucro_liquido_real=lucro_liquido_real
            )
            db.session.add(novo_produto)
            flash('Produto salvo com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('main.produtos'))

    taxas = TaxaPagamento.query.all()
    taxas_dict = {t.metodo: t for t in taxas}
    return render_template("produto_form.html", produto=produto, taxas_dict=taxas_dict)

# ... (o restante das rotas, como excluir e exportar, continua igual)