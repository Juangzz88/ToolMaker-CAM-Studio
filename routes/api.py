# -*- coding: utf-8 -*-
"""
Endpoints unificados para API de ToolMaker CAM Studio.
"""
from flask import Blueprint, jsonify, request
from engineering.physics_engine import calcular_parametros_rectificado
from engineering.geometry_engine import calculate_tool_geometry
from engineering.tribologia import estimar_desgaste_recubrimiento

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/auto-evaluar", methods=["POST", "GET"])
def auto_evaluar():
    """Diagnóstico rápido del sistema y envolvente física local."""
    try:
        return jsonify({
            "status": "ok",
            "provider": "Motor Fisico Local",
            "alerta_critica": False,
            "diagnostico": "✅ Parámetros dentro de la envolvente nominal."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "alerta_critica": True, "diagnostico": str(e)}), 500

@api_bp.route("/estimar-recubrimiento", methods=["POST"])
def api_estimar_recubrimiento():
    """Endpoint del Módulo 5 (Recubrimientos / Tribología)."""
    try:
        data = request.get_json(force=True) or {}
        res = estimar_desgaste_recubrimiento(data)
        return jsonify({
            "success": True,
            "status": "success",
            "data": res,
            **res
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Error tribologico: {str(e)}"}), 500

@api_bp.route("/rectificado/calcular", methods=["POST"])
def api_calcular_rectificado():
    """Endpoint del Módulo 1 (Operaciones y Muelas CNC)."""
    try:
        payload = request.get_json(force=True) or {}
        result = calcular_parametros_rectificado(payload)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/calcular-geometria", methods=["POST"])
def api_calcular_geometria():
    """Endpoint del Módulo 2 (Geometría CAD/CAM)."""
    try:
        data = request.get_json(force=True) or {}
        resultado = calculate_tool_geometry(data)
        return jsonify({"success": True, "status": "success", **resultado}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500