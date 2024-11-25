import os

class Config:
    # URI per la connessione al database MySQL
    SQLALCHEMY_DATABASE_URI = os.getenv("MARKET_DB_URI", "mysql+pymysql://root:root@mysql:3306/market_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disabilita la tracciabilità per ottimizzare le prestazioni
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "JwtGACHA2425")  # Chiave segreta per la gestione delle sessioni
