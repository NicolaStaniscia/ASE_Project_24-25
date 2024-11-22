import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("MARKET_DB_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DBM_URL = os.getenv("DBM_URL", "https://db_manager:5000/db_manager/")
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "JwtGACHA2425")
