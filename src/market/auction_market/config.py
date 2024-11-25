import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("MARKET_DB_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TRADING_HISTORY_URL = os.getenv("TRADING_HISTORY_URL", "https://trading_history:5000/trading_history/")
    COLLECTION_SEE_URL = os.getenv("COLLECTION_SEE_URL", "https://see_gacha_collection:5007/")
    COLLECTION_EDIT_URL = os.getenv("COLLECTION_EDIT_URL", "https://edit_gacha_collection:5008/")
    COLLECTION_ROLL_URL = os.getenv("COLLECTION_ROLL_URL", "https://roll_gacha:5009/")
    USERS_URL = os.getenv("USERS_URL", "https://account_management:5000/")
    DBM_URL = os.getenv("DBM_URL", "https://db_manager:5000/db_manager/")
