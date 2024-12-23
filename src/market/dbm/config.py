import os

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

class Config:
    # URI per la connessione al database MySQL
    SQLALCHEMY_DATABASE_URI = os.getenv("MARKET_DB_URI", get_secret('/run/secrets/market_db_uri'))
    TRADING_HISTORY_URL = os.getenv("TRADING_HISTORY_URL", "https://trading_history:5000/trading_history/")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disabilita la tracciabilità per ottimizzare le prestazioni
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", get_secret('/run/secrets/jwt_password'))  # Chiave segreta per la gestione delle sessioni
    SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {
        'ssl': {
            'check_hostname': False,  # Disable hostname verification
            'verify_mode': False     # Disable cert verification
        }
    }
}
