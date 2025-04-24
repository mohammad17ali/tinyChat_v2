import os
from flask import Flask
from app.routes import main as main_blueprint

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # Create necessary folders
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    # Register routes
    app.register_blueprint(main_blueprint)

    return app
