from flask import Blueprint, render_template

# =============================================================================
# DEFINICIÓN DEL BLUEPRINT DE VISTAS
# =============================================================================
# Objeto views_bp requerido por app.py para registrar las vistas locales
views_bp = Blueprint('views', __name__)

# =============================================================================
# RUTAS DE LOS 5 MÓDULOS DE TOOLMAKER CAM STUDIO
# =============================================================================

@views_bp.route('/')
@views_bp.route('/calculadora-muelas')
def muelas():
    """Módulo 1: Calculadora de Operaciones y Muelas de Rectificado FEPA."""
    return render_template('muelas.html', active_module=1)

@views_bp.route('/geometria-herramienta')
def geometria():
    """Módulo 2: Geometría de Fresas y Cálculo de Rigidez."""
    return render_template('geometria.html', active_module=2)

@views_bp.route('/geometria-brocas')
def brocas():
    """Módulo 3: Brocas de Carburo Sólido DIN 1412-C."""
    return render_template('brocas.html', active_module=3)

@views_bp.route('/catalogo-abrasivos')
def abrasivos():
    """Módulo 4: Biblioteca de Abrasivos FEPA."""
    return render_template('abrasivos.html', active_module=4)

@views_bp.route('/recubrimientos')
def recubrimientos():
    """Módulo 5: Estimación de Recubrimientos PVD/CVD."""
    return render_template('recubrimientos.html', active_module=5)