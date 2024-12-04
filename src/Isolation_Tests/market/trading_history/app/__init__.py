from flask import Flask
from .routes import trading_history
from config import Config
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt = JWTManager(app)

    from .models import db
    db.init_app(app)
    app.register_blueprint(trading_history, url_prefix='/trading_history')

    return app

