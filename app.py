import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

def create_app():
    """Factoría de aplicación Flask para ToolMaker CAM Studio."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configuración de producción / desarrollo
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'toolmaker_local_secret_key_2026_industrial_cam')
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Registrar Blueprints de Rutas
    from routes.views import views_bp
    from routes.api import api_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)

    return app

app = create_app()

if __name__ == '__main__':
    # Usar puerto 5001 local sin exposición a red
    app.run(debug=True, host='127.0.0.1', port=5001)