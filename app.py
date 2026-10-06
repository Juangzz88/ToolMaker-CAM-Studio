# -*- coding: utf-8 -*-
"""
Entry Point Principal - ToolMaker CAM Studio
"""
import os
import sys
import logging
from flask import Flask, jsonify, request, send_from_directory, render_template
from jinja2 import TemplateNotFound
from routes.api import api_bp

# Asegurar que el directorio raíz esté en la ruta del sistema
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToolMakerApp")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'toolmaker_cam_studio_dev_key_2026'
    app.config['DEV_MODE'] = True
    
    # Permitir URLs con o sin '/' al final globalmente
    app.url_map.strict_slashes = False

    # 1. Validación de Licencia Segura
    try:
        import importlib.util
        license_module_path = os.path.join(app.root_path, 'validation', 'license_guard.py')
        
        if os.path.exists(license_module_path):
            spec = importlib.util.spec_from_file_location("license_guard", license_module_path)
            if spec and spec.loader:
                license_guard = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(license_guard)
                license_status = license_guard.run_license_check() # type: ignore
                app.config['LICENSE_VALID'] = license_status.get('valid', False)
        else:
            app.config['LICENSE_VALID'] = False
            logger.info("ℹ️️ Archivo validation/license_guard.py no presente. Modo Desarrollo activo.")
    except Exception as e:
        app.config['LICENSE_VALID'] = False
        logger.warning(f"⚠️ Chequeo de licencia en modo Dev/Recovery: {e}")

    # 2. Registrar Blueprint de API
    app.register_blueprint(api_bp)

    # 3. Rutas de Vistas Principales
    @app.route('/')
    @app.route('/calculadora-muelas')
    def modulo1():
        return render_template('muelas.html', active_module=1)

    @app.route('/geometria-herramienta')
    def modulo2():
        return render_template('geometria.html', active_module=2)

    @app.route('/geometria-brocas')
    def modulo3():
        return render_template('brocas.html', active_module=3)

    @app.route('/catalogo-abrasivos')
    def modulo4():
        return render_template('abrasivos.html', active_module=4)

    @app.route('/recubrimientos')
    def modulo5():
        return render_template('recubrimientos.html', active_module=5)

    # 4. Favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # 5. Handlers de error detallados
    @app.errorhandler(404)
    def not_found(e):
        logger.error(f"❌ Error 404 en la ruta: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': f'Endpoint no encontrado: {request.path}'}), 404
        return render_template('base.html', error_msg="Página no encontrada"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"❌ Error 500 Interno en la ruta {request.path}: {e}")
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'Error interno del servidor'}), 500
        return f"<h3>Error 500: Verifica que la plantilla del módulo exista en /templates/</h3><p>{e}</p>", 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)