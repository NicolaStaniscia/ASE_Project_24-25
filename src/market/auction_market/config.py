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
    SQLALCHEMY_DATABASE_URI = get_secret('/run/secrets/market_db_uri')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TRADING_HISTORY_URL = os.getenv("TRADING_HISTORY_URL", "https://trading_history:5000/trading_history/")
    COLLECTION_SEE_URL = os.getenv("COLLECTION_SEE_URL", "https://see_gacha_collection:5007/")
    COLLECTION_EDIT_URL = os.getenv("COLLECTION_EDIT_URL", "https://edit_gacha_collection:5008/")
    COLLECTION_ROLL_URL = os.getenv("COLLECTION_ROLL_URL", "https://roll_gacha:5009/")
    USERS_URL = os.getenv("USERS_URL", "https://account_management:5000/")
    DBM_URL = os.getenv("DBM_URL", "https://db_manager:5000/db_manager/")
