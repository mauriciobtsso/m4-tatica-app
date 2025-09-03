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
# ... (código existente sem alterações)

# --- ROTAS DE TAXAS (ADICIONADAS AQUI) ---

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

        if taxa_id: # Editando
            taxa.metodo = metodo
            taxa.taxa_percentual = taxa_percentual
            taxa.coeficiente = coeficiente
            flash('Taxa atualizada com sucesso!', 'success')
        else: # Criando
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