# -*- coding: utf-8 -*-
"""
Entry Point Principal - ToolMaker CAM Studio
"""
import os
import sys
import logging
from flask import Flask, jsonify, request, send_from_directory, render_template

# Asegurar que el directorio raíz esté en la ruta del sistema para resolver 'validation'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToolMakerApp")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'toolmaker_cam_studio_dev_key_2026'
    app.config['DEV_MODE'] = True

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
            logger.info("ℹ️ Archivo validation/license_guard.py no presente. Modo Desarrollo activo.")
    except Exception as e:
        app.config['LICENSE_VALID'] = False
        logger.warning(f"⚠️ Chequeo de licencia en modo Dev/Recovery: {e}")

    # 2. Registrar Blueprints
    from routes.api import api_bp
    from routes.views import views_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # 3. Favicon anti 404
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    # 4. Handlers de error JSON para llamadas AJAX
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'Endpoint no encontrado'}), 404
        return render_template('base.html', error_msg="Página no encontrada"), 404

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)