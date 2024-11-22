from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AuctionTransactions(db.Model):
    __tablename__ = 'AuctionTransactions'
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('Auctions.id'),nullable=False)
    buyer_id = db.Column(db.Integer,)
    seller_id = db.Column(db.Integer, nullable=False)
    final_price = db.Column(db.Integer, nullable=False)
    transaction_time = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    status = db.Column(db.Enum('completed', 'failed'), default='completed')

class UserTransactionHistory(db.Model):
    __tablename__ = 'UserTransactionHistory'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    auction_id = db.Column(db.Integer, db.ForeignKey('Auctions.id'), nullable=False)
    transaction_type = db.Column(db.Enum('buy', 'sell', 'refund'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_time = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

class Auctions(db.Model):
    __tablename__ = 'Auctions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gacha_id = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.Integer, nullable=False)
    starting_price = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Integer, nullable=False)
    auction_end = db.Column(db.TIMESTAMP, nullable=False)
    status = db.Column(db.Enum('active', 'closed', 'canceled', 'suspended'), default='active')
