import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@mysql:3306/market_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DBM_URL = os.getenv("DBM_URL", "https://db_manager:5000/db_manager/")
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "JwtGACHA2425")
