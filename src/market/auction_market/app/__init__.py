from flask import Flask
from .routes import auction_market
from config import Config
from .apscheduler import init_scheduler
from flask_jwt_extended import JWTManager

def get_secret(secret_path):
        try:
            # Read secret
            with open(secret_path, 'r') as secret_file:
                secret = secret_file.read().strip()  # Remove spaces and newline
            return secret
        except FileNotFoundError:
            raise Exception(f"Secret file not found at {secret_path}")
        except Exception as e:
            raise Exception(f"Error reading secret: {str(e)}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = get_secret('/run/secrets/jwt_password')

    jwt = JWTManager(app)

    from .models import db
    db.init_app(app)
    app.register_blueprint(auction_market, url_prefix='/auction_market')

    with app.app_context():
        app.apscheduler = init_scheduler(app)

    

    return app
