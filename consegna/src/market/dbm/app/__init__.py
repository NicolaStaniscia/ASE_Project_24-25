from flask import Flask
from .models import db
from config import Config
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt = JWTManager(app)

    db.init_app(app)

    from .routes import db_manager
    app.register_blueprint(db_manager, url_prefix='/db_manager')

    return app
