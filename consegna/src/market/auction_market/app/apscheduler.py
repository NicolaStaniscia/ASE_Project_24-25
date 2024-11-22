from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import current_app
from .models import Auctions, Bids, db
import requests

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    
    # Aggiungi i job, passando esplicitamente l'applicazione
    scheduler.add_job(
        func=lambda: process_expired_auctions(app),
        trigger='interval',
        minutes=1,
        id='process_expired_auctions',
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: refund_non_winning_bids(app),
        trigger='interval',
        seconds=30,
        id='refund_non_winning_bids',
        replace_existing=True
    )

    scheduler.start()

    return scheduler

def process_expired_auctions(app):
    with app.app_context():
        now = datetime.utcnow()

        # Recupera aste scadute e attive
        expired_auctions = Auctions.query.filter(
            Auctions.auction_end <= now,
            Auctions.status == 'active'
        ).all()

        for auction in expired_auctions:
            try:
                with db.session.begin():
                    # Aggiorna lo stato dell'asta a "closed"
                    auction.status = 'closed'
                    db.session.commit()

                    # Triggera l'endpoint per trasferire il gacha
                    auction_win_url = "https://localhost:5000/auction_market/market/auction_win"  # Aggiorna con l'URL reale
                    response_win = requests.post(auction_win_url, json={
                        "auction_id": auction.id
                    }, verify=False)

                    if response_win.status_code != 200:
                        raise Exception("Failed to transfer gacha ownership")

                    # Triggera l'endpoint per trasferire il denaro al venditore
                    auction_complete_url = "https://localhost:5000/auction_market/market/auction_complete"  # Aggiorna con l'URL reale
                    response_complete = requests.post(auction_complete_url, json={
                        "auction_id": auction.id
                    }, verify=False)

                    if response_complete.status_code != 200:
                        raise Exception("Failed to transfer final price to seller")

                    # Triggera l'endpoint per i rimborsi nell'auction_market
                    auction_refund_url = "https://localhost:5000/auction_market/market/auction_refund"  # Aggiorna con l'URL reale
                    response_refund = requests.post(auction_refund_url, json={
                        "auction_id": auction.id
                    }, verify=False)

                    if response_refund.status_code != 200:
                        raise Exception("Failed to process refunds for losing bidders")

            except Exception as e:
                db.session.rollback()
                # Log dell'errore senza interrompere il processo per altre aste
                print(f"Error processing auction {auction.id}: {str(e)}")

def refund_non_winning_bids(app):
    with app.app_context():
        with db.session.no_autoflush:  # Evita conflitti con altre transazioni
            active_auctions = Auctions.query.filter(Auctions.status == 'active').all()

            for auction in active_auctions:
                # Trova l'offerta più alta per l'asta
                highest_bid = Bids.query.filter_by(auction_id=auction.id).order_by(Bids.bid_amount.desc()).first()

                # Trova tutte le offerte perdenti non ancora rimborsate
                losing_bids = Bids.query.filter(
                    Bids.auction_id == auction.id,
                    Bids.id != highest_bid.id if highest_bid else True,  # Ignora l'offerta vincente
                    Bids.refunded == False  # Solo offerte non ancora rimborsate
                ).all()

                for bid in losing_bids:
                    try:
                        # Effettua il rimborso tramite il servizio di trading
                        trading_url = current_app.config['TRADING_HISTORY_URL'] + "/market/refund"
                        response = requests.post(trading_url, json={
                            "user_id": bid.bidder_id,
                            "auction_id": auction.id,
                            "amount": bid.bid_amount
                        }, verify=False)

                        if response.status_code == 200:
                            # Segna l'offerta come rimborsata
                            bid.refunded = True
                            db.session.commit()
                        else:
                            db.session.rollback()
                            print(f"Refund failed for bid {bid.id} in auction {auction.id}")
                    except requests.exceptions.RequestException as e:
                        db.session.rollback()
                        print(f"Error processing refund for bid {bid.id} in auction {auction.id}: {str(e)}")
