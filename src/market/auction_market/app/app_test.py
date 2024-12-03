import random
from datetime import datetime, timedelta
import app as main_app
from flask import request
from flask_jwt_extended import get_jwt_identity

flask_app = main_app.create_app()

# ROUTES
# Mock per simulare il comportamento del dbm in GET /market
def mock_dbm_get_market():
    # Simula due aste attive come risposta del DB Manager
    return MockResponse(
        status_code=200,
        json_data=[
            {
                "id": 1,
                "gacha_id": 101,
                "seller_id": 501,
                "starting_price": 100,
                "current_price": 150,
                "auction_end": "2025-12-01T12:00:00Z",
                "status": "active"
            },
            {
                "id": 2,
                "gacha_id": 102,
                "seller_id": 502,
                "starting_price": 200,
                "current_price": 250,
                "auction_end": "2025-12-02T18:00:00Z",
                "status": "active"
            }
        ]
    )

# Mock per simulare il comportamento del dbm in GET /admin/market/specific_auction
def mock_dbm_get_auction(auction_id):
    # Simula una risposta per un'asta specifica
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found"}
        )
    
    return MockResponse(
        status_code=200,
        json_data={
            "auction": {
                "id": 1,
                "gacha_id": 101,
                "seller_id": 501,
                "starting_price": 100,
                "current_price": 150,
                "auction_end": "2025-12-01T12:00:00Z",
                "status": "active"
            }
        }
    )

# Mock per simulare il comportamento del dbm in PATCH /admin/market/specific_auction
def mock_dbm_patch_auction(auction_id):
    # Simula una risposta di successo
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found"}
        )

    return MockResponse(
        status_code=200,
        json_data={"message": "Auction status updated successfully"}
    )

# Mock per simulare il comportamento del dbm in DELETE /admin/market/specific_auction
def mock_dbm_delete_auction(auction_id):
    # Simulazione dell'errore 404 se l'ID dell'asta è 404
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found"}
        )

    # Simulazione di successo per altri ID
    return MockResponse(
        status_code=200,
        json_data={"message": "Auction deleted successfully"}
    )

# Mock per simulare il comportamento del dbm in GET /admin/market/history
def mock_dbm_market_history():
    # Caso predefinito: Ritorna una lista di aste
    return MockResponse(
        status_code=200,
        json_data=[
            {
                "id": 1,
                "gacha_id": 10,
                "seller_id": 10,
                "starting_price": 50,
                "current_price": 75,
                "auction_end": "2024-12-01T15:30:00",
                "status": "closed"
            },
            {
                "id": 2,
                "gacha_id": 11,
                "seller_id": 11,
                "starting_price": 100,
                "current_price": 150,
                "auction_end": "2025-12-05T18:45:00",
                "status": "active"
            }
        ]
    )

# Mock per simulare il comportamento del dbm in POST /market
def mock_dbm_post_market(gacha_id):
    # Caso: asta attiva per il gacha_id (non posso creare l'asta)
    if gacha_id == "active_gacha":
        return MockResponse(
            status_code=200,
            json_data={"active_auction": True}
        )

    # Caso: nessuna asta attiva per il gacha_id
    return MockResponse(
        status_code=200,
        json_data={"active_auction": False}
    )



# Mock per simulare il comportamento del servizio collection in POST /market
def mock_collection_post_market(user_id):
    # Simula la collezione dell'utente in base all'user_id
    if user_id == "user_with_gacha":
        return MockResponse(
            status_code=200,
            json_data=[
                {"idOwn": 1, "name": "Gacha_One"},
                {"idOwn": 2, "name": "Gacha_Two"},
            ]
        )

    if user_id == "user_without_gacha":
        return MockResponse(
            status_code=200,
            json_data=[]
        )
    
    # Caso predefinito: utente non trovato
    return MockResponse(
        status_code=404,
        json_data={"error": "Failed to retrieve user collection"}
    )


# Mock per simulare il comportamento del dbm alla creazione in POST /market
def mock_dbm_post_market_create(gacha_id):
    # Caso: errore simulato durante la creazione dell'asta
    # Valore da implementare in POSTMAN come stringa
    if gacha_id == "simulate_error":
        return MockResponse(
            status_code=500,
            json_data={"error": "Failed to create auction", "message": "Simulated database error"}
        )
    # Risposta di successo
    return MockResponse(
        status_code=201,
        json_data={
            "auction_id": (random.randint(100,500)),
            "message": "Auction created successfully"
        }
    )

# Mock per simulare il comportamento del servizio users in POST /market/bid
def mock_users_market_bid(user_id):
    if not user_id:
        return MockResponse(
            status_code=403,
            json_data={"error": "Forbidden"}
        )
    else:
        # Simula un utente con credito disponibile
        return MockResponse(
            status_code=200,
            json_data={"points": [1500]}  # Credito utente simulato
        )

# Mock per simulare il comportamento del dbm in POST /market/bid
def mock_dbm_market_bid(auction_id,bid_amount):
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found"}
        )
    elif auction_id == 400:
        return MockResponse(
            status_code=400,
            json_data={"error": "Auction is not active"}
        )
    elif bid_amount == 1:
        return MockResponse(
            status_code=400,
            json_data={"error": "Bid amount must be higher than the current price"}
        )
    else:
        # Simula una risposta di successo per l'offerta
        return MockResponse(
            status_code=201,
            json_data={"message": "Bid placed successfully"}
        )


# Mock per simulare il comportamento del servizio users che aggiorna il saldo in POST /market/bid
def mock_users_bid_update(currency):
    if not currency:
        return MockResponse(
            status_code=400,
            json_data={"error": "Bad request"}
        )
    else:
        # Simula una risposta di successo
        return MockResponse(
            status_code=200,
            json_data={"message": "Currency updated"}
        )

# Mock per simulare il comportamento del dbm in POST /market/auction_win
def mock_dbm_auction_win(auction_id):
    if not auction_id:
        return MockResponse(
            status_code=404,
            json_data={"auction_found": False, "highest_bid_found": False}
        )
    elif auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"auction_found": True, "highest_bid_found": False}
        )
    else:
        # Caso di successo: asta trovata e vincitore presente
        return MockResponse(
            status_code=200,
            json_data={
                "auction_found": True,
                "highest_bid_found": True,
                "gacha_id": 11,  # ID del gacha simulato
                "highest_bid": {
                    "bidder_id": 22,  # ID del vincitore simulato
                    "bid_amount": 150  # Offerta più alta simulata
                }
            }
        )

# Mock per simulare il comportamento del servizio collection in POST /market/auction_win
def mock_collection_auction_win(gacha_id,user_id):
    # Simula i casi specifici
    if not user_id or not gacha_id:
        return MockResponse(
            status_code=400,
            json_data={"error": "Bad request"}
        )
    else:
        # Caso di successo: trasferimento completato
        return MockResponse(
            status_code=200,
            json_data={"result":f"Gacha {gacha_id} added to user (id: {user_id}) collection"}
        )



# Mock per simulare il comportamento del dbm in POST /market/auction_complete
def mock_dbm_auction_complete(auction_id):
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found or not closed"}
        )
    elif auction_id == 4044:
        return MockResponse(
            status_code=404,
            json_data={"error": "No bids found for this auction"}
        )
    else:
        # Caso di successo: asta trovata e vincitore presente
        return MockResponse(
            status_code=200,
            json_data={
                "auction_found": True,
                "highest_bid_found": True,
                "seller_id": 11,  # ID del venditore simulato
                "highest_bid": {
                    "bidder_id": 22,  # ID del vincitore simulato
                    "bid_amount": 150  # Offerta più alta simulata
                }
            }
        )

# Mock per simulare il comportamento del servizio trading in POST /market/auction_complete
def mock_trading_auction_complete(auction_id, buyer_id, seller_id, final_price):
    if not all([auction_id, buyer_id, seller_id, final_price]):
        return MockResponse(
            status_code=400,
            json_data={"error": "All fields are required"}
        )
    else:
        # Caso di successo: transazione registrata
        return MockResponse(
            status_code=200,
            json_data={"message": "Transaction recorded successfully"}
        )

# Mock per simulare il comportamento del dbm in POST /market/auction_refund
def mock_dbm_auction_refund(auction_id):
    if auction_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "Auction not found or not closed"}
        )
    elif auction_id == 4044:
        return MockResponse(
            status_code=404,
            json_data={"error": "No bids found for this auction"}
        )
    else:
        # Caso di successo: transazione registrata
        return MockResponse(
            status_code=200,
            json_data={"success": True, "message": "Refunds processed successfully"}
        )

##APSCHEDULER
# Mock per simulare il comportamento del servizio trading in POST /market/refund
def mock_trading_market_refund(auction_id,user_id,amount):
    if not all([auction_id, user_id, amount]):
        return MockResponse(
            status_code=400,
            json_data={"error": "Invalid data"}
        )
    
    if user_id == 404:
        return MockResponse(
            status_code=404,
            json_data={"error": "User not found"}
        )
    
    return MockResponse(
            status_code=200,
            json_data={"message": "Refund processed successfully"}
        )

def mock_dbm_get_auctions():
    # Mock di aste scadute
        current_time = datetime.utcnow()
        expired_auctions = [
            {
                "id": 5,
                "gacha_id": 101,
                "seller_id": 4,
                "auction_end": (current_time - timedelta(days=1)),
                "starting_price": 100,
                "current_price": 120,
                "status": "active"
            },
            {
                "id": 6,
                "gacha_id": 102,
                "seller_id": 3,
                "auction_end": (current_time - timedelta(hours=2)),
                "starting_price": 100,
                "current_price": 150,
                "status": "active"
            }
        ]

        # Genera risposta di successo
        return MockResponse(
            status_code=200,
            json_data={"expired_auctions": expired_auctions}
        )

def mock_dbm_update_status(auction_id,status):
    if not status:
        # Simula un errore quando i parametri obbligatori mancano
        return MockResponse(
            status_code=400,
            json_data={"error": "New status is required"}
        )
    
    if auction_id == 404:
        return MockResponse(
                status_code=404,
                json_data={"error": "Auction not found"}
            )

    # Simula un aggiornamento di stato riuscito
    return MockResponse(
        status_code=200,
        json_data={"message": "Auction status updated successfully"}
    )

def mock_dbm_losing_bids(auction_id):
    if auction_id == 2000:  # Simula un'asta senza offerte
            return MockResponse(
                status_code=200,
                json_data={"losing_bids": []}
            )
    losing_bids = [
            {"id": 1, "auction_id": auction_id, "bidder_id": 3, "bid_amount": 101},
            {"id": 2, "auction_id": auction_id, "bidder_id": 4, "bid_amount": 102},
        ]
    
    return MockResponse(
            status_code=200,
            json_data={"losing_bids": losing_bids}
        )
    
def mock_dbm_update_bid(new_status,bid_id):
    if not new_status:
        # Simula un errore quando i parametri obbligatori mancano
        return MockResponse(
            status_code=400,
            json_data={"error": "Refunded status is required"}
        )
    if bid_id == 404:
        # Simula un errore quando i parametri obbligatori mancano
        return MockResponse(
            status_code=404,
            json_data={"error": "Bid not found"}
        )
    return MockResponse(
            status_code=200,
            json_data={"message": "Bid status updated successfully"}
        )

# Classe per simulare una risposta HTTP
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

# Inietta il mock nel modulo delle routes.py
main_app.routes.mock_dbm_get_market = mock_dbm_get_market
main_app.routes.mock_dbm_get_auction = mock_dbm_get_auction
main_app.routes.mock_dbm_patch_auction = mock_dbm_patch_auction
main_app.routes.mock_dbm_delete_auction = mock_dbm_delete_auction
main_app.routes.mock_dbm_market_history = mock_dbm_market_history
main_app.routes.mock_dbm_post_market = mock_dbm_post_market
main_app.routes.mock_collection_post_market = mock_collection_post_market
main_app.routes.mock_dbm_post_market_create = mock_dbm_post_market_create
main_app.routes.mock_users_market_bid = mock_users_market_bid
main_app.routes.mock_dbm_market_bid = mock_dbm_market_bid
main_app.routes.mock_users_bid_update = mock_users_bid_update
main_app.routes.mock_dbm_auction_win = mock_dbm_auction_win
main_app.routes.mock_collection_auction_win = mock_collection_auction_win
main_app.routes.mock_dbm_auction_complete = mock_dbm_auction_complete
main_app.routes.mock_trading_auction_complete = mock_trading_auction_complete
main_app.routes.mock_dbm_auction_find = mock_dbm_get_auction
main_app.routes.mock_dbm_auction_refund = mock_dbm_auction_refund

# Inietta il mock nel modulo dell'apscheduler.py
main_app.apscheduler.mock_dbm_get_market = mock_dbm_get_market
main_app.apscheduler.mock_trading_market_refund = mock_trading_market_refund
main_app.apscheduler.mock_dbm_get_auctions = mock_dbm_get_auctions
main_app.apscheduler.mock_dbm_update_status = mock_dbm_update_status
main_app.apscheduler.mock_dbm_losing_bids = mock_dbm_losing_bids
main_app.apscheduler.mock_dbm_update_bid = mock_dbm_update_bid