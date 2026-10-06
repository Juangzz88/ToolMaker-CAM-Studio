# -*- coding: utf-8 -*-
"""
Endpoints de la API de ToolMaker CAM Studio
"""
import os
import secrets
import string
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from engineering.physics_engine import calcular_parametros_rectificado
from engineering.geometry_engine import calculate_tool_geometry
from engineering.tribologia import estimar_desgaste_recubrimiento
from core.database import get_db_connection, init_db

try:
    from core.security.hwid import get_hwid
except ImportError:
    import platform, uuid
    def get_hwid():
        return f"HWID-{platform.node()}-{uuid.getnode()}"

# Inicializar Base de Datos SQLite
init_db()

api_bp = Blueprint("api", __name__, url_prefix="/api")

def generar_clave_corta():
    chars = string.ascii_uppercase + string.digits
    bloques = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return f"TMCS-{''.join(bloques)}"

# ==============================================================================
# ENDPOINTS ADMINISTRATIVOS DE LICENCIAS
# ==============================================================================

@api_bp.route("/admin/registrar-usuario", methods=["POST"])
@api_bp.route("/admin/registrar-usuario/", methods=["POST"])
def admin_registrar_usuario():
    try:
        data = request.get_json(force=True) or {}
        cliente = data.get("client_name", "").strip()
        hwid = data.get("hwid", "").strip()
        email = data.get("email", "").strip()
        dias = int(data.get("days", 30))
        
        if not cliente or not hwid:
            return jsonify({"success": False, "message": "El nombre del Cliente y el HWID son obligatorios."}), 400

        license_key = generar_clave_corta()
        fecha_exp = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO licenses (client_name, hwid, email, license_key, days, created_at, exp_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
        ''', (cliente, hwid, email, license_key, dias, datetime.now().strftime("%Y-%m-%d %H:%M"), fecha_exp))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Licencia generada con éxito para {cliente}",
            "license_key": license_key,
            "exp_date": fecha_exp
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error registrando usuario: {str(e)}"}), 500

@api_bp.route("/admin/listar-usuarios", methods=["GET"])
@api_bp.route("/admin/listar-usuarios/", methods=["GET"])
def admin_listar_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        usuarios = []
        for r in rows:
            usuarios.append({
                "id": r["id"],
                "client_name": r["client_name"],
                "hwid": r["hwid"] if "hwid" in r.keys() else "UNKNOWN",
                "email": r["email"],
                "license_key": r["license_key"],
                "days": r["days"],
                "created_at": r["created_at"],
                "exp_date": r["exp_date"],
                "status": r["status"]
            })

        return jsonify({"success": True, "data": usuarios, "current_hwid": get_hwid()}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route("/admin/cambiar-estado", methods=["POST"])
@api_bp.route("/admin/cambiar-estado/", methods=["POST"])
def admin_cambiar_estado():
    try:
        data = request.get_json(force=True) or {}
        lic_id = data.get("id")
        nuevo_estado = data.get("status")

        if not lic_id or not nuevo_estado:
            return jsonify({"success": False, "message": "ID y nuevo estado son obligatorios."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE licenses SET status = ? WHERE id = ?", (nuevo_estado, lic_id))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Estado de la licencia #{lic_id} cambiado a {nuevo_estado}."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route("/admin/eliminar-usuario", methods=["POST", "DELETE"])
@api_bp.route("/admin/eliminar-usuario/", methods=["POST", "DELETE"])
def admin_eliminar_usuario():
    try:
        data = request.get_json(force=True) or {}
        lic_id = data.get("id")

        if not lic_id:
            return jsonify({"success": False, "message": "El ID de la licencia es obligatorio."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM licenses WHERE id = ?", (lic_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Licencia #{lic_id} eliminada permanentemente."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================================================================
# ENDPOINTS DE VALIDACIÓN EN CLIENTE
# ==============================================================================

@api_bp.route("/licencia/status", methods=["POST", "GET"])
@api_bp.route("/licencia/status/", methods=["POST", "GET"])
def get_license_status():
    current_hwid = get_hwid()
    try:
        data = request.get_json(silent=True) or {}
        code = data.get("code", "").strip()
        
        if not code:
            return jsonify({"status": "unlicensed", "hwid": current_hwid, "message": "Sin licencia activa."}), 200
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (code,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"status": "invalid", "hwid": current_hwid, "message": "Clave no encontrada."}), 200

        if row["status"] == "PAUSED":
            return jsonify({"status": "paused", "hwid": current_hwid, "message": "Licencia Pausada."}), 200
        elif row["status"] == "REVOKED":
            return jsonify({"status": "revoked", "hwid": current_hwid, "message": "Licencia Revocada."}), 200

        if row["hwid"] != current_hwid:
            return jsonify({"status": "hwid_mismatch", "hwid": current_hwid, "message": "HWID no coincide."}), 200

        exp_date = datetime.strptime(row["exp_date"], "%Y-%m-%d")
        days_left = (exp_date - datetime.now()).days

        if days_left < 0:
            return jsonify({"status": "expired", "hwid": current_hwid, "message": "Licencia expirada."}), 200

        return jsonify({
            "status": "active",
            "hwid": current_hwid,
            "details": {
                "client": row["client_name"],
                "exp_date": row["exp_date"],
                "days_left": max(0, days_left)
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "hwid": current_hwid, "message": str(e)}), 500

@api_bp.route("/licencia/activar-codigo", methods=["POST"])
@api_bp.route("/licencia/activar-codigo/", methods=["POST"])
def activar_codigo_licencia():
    current_hwid = get_hwid()
    try:
        data = request.get_json(force=True) or {}
        code = data.get("code", "").strip()
        
        if not code:
            return jsonify({"success": False, "message": "Ingresa una clave válida."}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (code,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"success": False, "message": "La clave ingresada no existe."}), 400

        if row["status"] == "PAUSED":
            return jsonify({"success": False, "message": "Esta licencia se encuentra Pausada."}), 400
        elif row["status"] == "REVOKED":
            return jsonify({"success": False, "message": "Esta licencia ha sido Revocada."}), 400

        if row["hwid"] != current_hwid:
            return jsonify({"success": False, "message": "Esta clave está vinculada a otro equipo (HWID no coincide)."}), 400

        exp_date = datetime.strptime(row["exp_date"], "%Y-%m-%d")
        days_left = (exp_date - datetime.now()).days

        if days_left < 0:
            return jsonify({"success": False, "message": "Esta licencia ha expirado."}), 400

        return jsonify({
            "success": True,
            "message": f"¡Licencia activada con éxito para {row['client_name']}!",
            "details": {
                "client": row["client_name"],
                "exp_date": row["exp_date"],
                "days_left": max(0, days_left)
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================================================================
# ENDPOINTS DE CÁLCULO E INGENIERÍA
# ==============================================================================

@api_bp.route("/auto-evaluar", methods=["POST", "GET"])
def auto_evaluar():
    return jsonify({"status": "ok", "provider": "Motor Fisico Local", "alerta_critica": False, "diagnostico": "✅ Parámetros nominales."}), 200

@api_bp.route("/estimar-recubrimiento", methods=["POST"])
def api_estimar_recubrimiento():
    try:
        data = request.get_json(force=True) or {}
        res = estimar_desgaste_recubrimiento(data)
        return jsonify({"success": True, "status": "success", "data": res, **res}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/rectificado/calcular", methods=["POST"])
def api_calcular_rectificado():
    try:
        payload = request.get_json(force=True) or {}
        return jsonify(calcular_parametros_rectificado(payload)), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/calcular-geometria", methods=["POST"])
def api_calcular_geometria():
    try:
        data = request.get_json(force=True) or {}
        return jsonify({"success": True, "status": "success", **calculate_tool_geometry(data)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500