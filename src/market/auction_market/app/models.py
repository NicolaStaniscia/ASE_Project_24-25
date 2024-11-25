from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Auctions(db.Model):
    __tablename__ = 'Auctions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gacha_id = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.Integer, nullable=False)
    starting_price = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Integer, nullable=False)
    auction_end = db.Column(db.TIMESTAMP, nullable=False)
    status = db.Column(db.Enum('active', 'closed', 'canceled', 'suspended'), default='active')

class Bids(db.Model):
    __tablename__ = 'Bids'
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('Auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, nullable=False)
    bid_amount = db.Column(db.Integer, nullable=False)
    bid_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    refunded = db.Column(db.Boolean, default=False)
