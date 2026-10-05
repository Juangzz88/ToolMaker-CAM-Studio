from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
@views_bp.route('/calculadora-muelas')
def calculadora_muelas():
    return render_template('muelas.html', active_module=1)

@views_bp.route('/geometria-herramienta')
def geometria_herramienta():
    return render_template('geometria.html', active_module=2)

@views_bp.route('/geometria-brocas')
def geometria_brocas():
    return render_template('brocas.html', active_module=3)

@views_bp.route('/catalogo-abrasivos')
def catalogo_abrasivos():
    return render_template('abrasivos.html', active_module=4)

@views_bp.route('/recubrimientos')
def recubrimientos():
    return render_template('recubrimientos.html', active_module=5)