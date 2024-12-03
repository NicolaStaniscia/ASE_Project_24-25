from flask import Flask
from .routes import auction_market
from config import Config
from .apscheduler import init_scheduler
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = "JwtGACHA2425"

    jwt = JWTManager(app)

    from .models import db
    db.init_app(app)
    app.register_blueprint(auction_market, url_prefix='/auction_market')

    with app.app_context():
        app.apscheduler = init_scheduler(app)

    

    return app
