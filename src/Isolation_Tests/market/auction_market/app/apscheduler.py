from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import current_app, jsonify
from .models import Auctions, Bids, db
import requests

# Mock functions
mock_dbm_get_market = None
mock_trading_market_refund = None
mock_dbm_get_auctions = None
mock_dbm_update_status = None
mock_dbm_losing_bids = None
mock_dbm_update_bid = None



def dbm_url(path):
    return current_app.config['DBM_URL'] + path

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
        try:
            # Effettua la chiamata al DB Manager per recuperare le aste scadute
            if mock_dbm_get_auctions:
                response = mock_dbm_get_auctions()
            else:
                response = requests.get(
                    dbm_url("/market/expired_auctions"),
                    timeout=5,
                    verify=False
                )
            if response.status_code != 200:
                return jsonify({
                    "error": response.json().get("error", "Unknown error"),
                    "status_code": response.status_code
                }), response.status_code

            expired_auctions = response.json().get("expired_auctions", [])
        except requests.RequestException as e:
            return jsonify({"error": f"Failed to communicate with DB Manager: {str(e)}"}), 500

        for auction in expired_auctions:
            auction_id = auction.get("id")
            try:
                    # Chiamata al DB Manager per aggiornare lo stato dell'asta
                    update_url = dbm_url(f"/market/update_auction_status/{auction_id}")
                    if mock_dbm_update_status:
                        response_update = mock_dbm_update_status(auction_id,status="closed")
                    else:
                        response_update = requests.patch(update_url, json={"status": "closed"}, timeout=5,verify=False)

                    if response_update.status_code != 200:
                        raise Exception(f"Failed to update auction {auction_id} to closed")

                    # Triggera l'endpoint per trasferire il gacha
                    auction_win_url = "https://localhost:5000/auction_market/market/auction_win"  # Aggiorna con l'URL reale
                    response_win = requests.post(auction_win_url, json={
                        "auction_id": auction_id
                    }, timeout=5,verify=False)

                    if response_win.status_code != 200:
                        raise Exception("Failed to transfer gacha ownership")

                    # Triggera l'endpoint per trasferire il denaro al venditore
                    auction_complete_url = "https://localhost:5000/auction_market/market/auction_complete"  # Aggiorna con l'URL reale
                    response_complete = requests.post(auction_complete_url, json={
                        "auction_id": auction_id
                    }, timeout=5,verify=False)

                    if response_complete.status_code != 200:
                        raise Exception("Failed to transfer final price to seller")

                    # Triggera l'endpoint per i rimborsi nell'auction_market
                    auction_refund_url = "https://localhost:5000/auction_market/market/auction_refund"  # Aggiorna con l'URL reale
                    response_refund = requests.post(auction_refund_url, json={
                        "auction_id": auction_id
                    }, timeout=5,verify=False)

                    if response_refund.status_code != 200:
                        raise Exception("Failed to process refunds for losing bidders")

            except Exception as e:
                # Log dell'errore senza interrompere il processo per altre aste
                print(f"Error processing auction {auction_id}: {str(e)}")

def refund_non_winning_bids(app):
    with app.app_context():
            # Recupero delle aste attive
            try:
                if mock_dbm_get_market:
                    response = mock_dbm_get_market()
                else:
                    response = requests.get(dbm_url("/market"), timeout=5, verify=False)
                if response.status_code != 200:
                    return jsonify({'error': 'Failed to fetch active auctions'}), response.status_code

                active_auctions = response.json()
            except requests.RequestException as e:
                return jsonify({'error': f"Error communicating with DBM: {str(e)}"}), 500

            result = []
            for auction in active_auctions:
                auction_id = auction.get("id")

                try:
                    # Ottieni le offerte perdenti tramite il DBM
                    if mock_dbm_losing_bids:
                        response = mock_dbm_losing_bids(auction_id)
                    else:
                        response = requests.get(
                            dbm_url(f"/market/losing_bids/{auction_id}"),
                            timeout=5,
                            verify=False
                        )
                    if response.status_code != 200:
                        result.append({
                            "auction_id": auction_id,
                            "status": "failed",
                            "details": response.text
                        })
                        continue

                    losing_bids = response.json().get("losing_bids", [])
                except requests.RequestException as e:
                    result.append({
                        "auction_id": auction_id,
                        "status": "failed",
                        "details": str(e)
                    })
                    continue

                for bid in losing_bids:
                    try:
                        # Effettua il rimborso tramite il servizio di trading
                        trading_url = current_app.config['TRADING_HISTORY_URL'] + "/market/refund"
                        if mock_trading_market_refund:
                            response = mock_trading_market_refund(auction_id=auction_id,user_id=bid["bidder_id"],amount=bid["bid_amount"])
                        else:
                            response = requests.post(trading_url, json={
                                "user_id": bid["bidder_id"],
                                "auction_id": auction_id,
                                "amount": bid["bid_amount"]
                            }, timeout=5, verify=False)
                        if response.status_code == 200:
                            update_url = dbm_url(f"/market/update_bid_status/{bid['id']}")
                            if mock_dbm_update_bid:
                                update_response = mock_dbm_update_bid(new_status=True,bid_id=bid['id'])
                            else:
                                update_response = requests.patch(update_url, json={"refunded": True}, timeout=5,verify=False)

                            if update_response.status_code == 200:
                                result.append({
                                    "bid_id": bid["id"],
                                    "auction_id": auction_id,
                                    "status": "refunded"
                                })
                            else:
                                result.append({
                                    "bid_id": bid["id"],
                                    "auction_id": auction_id,
                                    "status": "refund_failed",
                                    "details": f"Failed to update refund status: {update_response.text}"
                                })
                        else:
                            result.append({
                                "bid_id": bid["id"],
                                "auction_id": auction_id,
                                "status": "refund_failed",
                                "details": response.text
                            })
                    except requests.RequestException as e:
                        result.append({
                            "bid_id": bid["id"],
                            "auction_id": auction_id,
                            "status": "refund_failed",
                            "details": str(e)
                        })

            return jsonify({"refund_results": result}), 200
