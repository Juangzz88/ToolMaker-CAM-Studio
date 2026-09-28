from flask import Blueprint, request, jsonify
from engineering.physics_engine import ejecutar_motor_fisico_local
from engineering.grinding_model import calcular_parametros_rectificado
from engineering.geometry_model import calcular_geometria_fresa
from engineering.coating_model import estimar_recubrimiento_pvd
from validation.inputs import validar_entrada_rectificado, validar_entrada_geometria

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/auto-evaluar', methods=['POST'])
def auto_evaluar():
    try:
        data = request.get_json() or {}
        modulo_actual = data.get('modulo', 'General')
        ctx = data.get('contexto_cruzado', {})
        return jsonify(ejecutar_motor_fisico_local(modulo_actual, ctx))
    except Exception as e:
        return jsonify({
            "status": "error",
            "provider": "Motor Físico Local",
            "alerta_critica": True,
            "diagnostico": f"⚠️ Fallo interno en Motor Físico: {str(e)}"
        }), 500

@api_bp.route('/calcular-rectificado', methods=['POST'])
def calcular_rectificado_route():
    data = request.json or {}

    # 1. Validación de Envolvente
    es_valido, errores = validar_entrada_rectificado(data)
    if not es_valido:
        return jsonify({
            'success': False,
            'error': "Violación de Envolvente Física",
            'detalles': errores
        }), 200

    try:
        res = calcular_parametros_rectificado(data)
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en cálculo: {str(e)}"}), 500

@api_bp.route('/calcular-geometria', methods=['POST'])
def calcular_geometria_route():
    data = request.json or {}

    es_valido, errores = validar_entrada_geometria(data)
    if not es_valido:
        return jsonify({
            'success': False,
            'error': "Violación de Envolvente Física",
            'detalles': errores
        }), 200

    try:
        res = calcular_geometria_fresa(data)
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': f"Error geométrico: {str(e)}"}), 500

@api_bp.route('/estimar-recubrimiento', methods=['POST'])
def estimar_recubrimiento_route():
    try:
        data = request.get_json() or {}
        res = estimar_recubrimiento_pvd(data)
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en recubrimientos: {str(e)}"}), 500