import app as main_app
from flask_jwt_extended import get_jwt_identity

flask_app = main_app.create_app()

# ROUTES
def mock_dbm_transaction_history(user_id):
    
    # Non ci sono transazioni
    if user_id == "no_history":
        return MockResponse(
            status_code=404,
            json_data={"transactions": [], "message": "No transactions found for this user"}
        )
    else:
        # Caso di successo: trasferimento completato
        return MockResponse(
            status_code=200,
            json_data={"transactions": [
                    {
                        "auction_id": 101,
                        "transaction_type": "bid",
                        "amount": 50,
                        "transaction_time": "2024-11-26T14:00:00"
                    },
                    {
                        "auction_id": 102,
                        "transaction_type": "refund",
                        "amount": 30,
                        "transaction_time": "2024-11-26T15:00:00"
                    }
                ]}
        )

def mock_dbm_market_transaction():
    # Risposta simulata di successo
    return MockResponse(
        status_code=201,
        json_data={
            "message": "Transaction recorded successfully",
            "transaction_id": 12345
        }
    )

def mock_users_market_transaction(user_id):

    if not user_id:
        # Risposta in caso di errore di autorizzazione
        return MockResponse(
            status_code=403,
            json_data={"error": "Unauthorized"}
        )
    # Simula una risposta con il credito utente
    return MockResponse(
        status_code=200,
        json_data={"points": [1000]}  # Credito corrente simulato
    )

def mock_users_market_currency(data):
    currency = data.get("currency")

    if not currency:
        # Risposta in caso di richiesta malformata
        return MockResponse(
            status_code=400,
            json_data={"error": "Bad request"}
        )
    
    # Risposta simulata di successo
    return MockResponse(
        status_code=200,
        json_data={"message": "Currency updated"}
    )

def mock_dbm_market_refund(user_id):
    # Simulazione dei casi possibili   
    if user_id == "existing_refund":
        # Caso in cui un rimborso esiste già
        return MockResponse(
            status_code=409,
            json_data={"error": "Refund already processed"}
        )

    # Caso in cui non esiste alcun rimborso
    return MockResponse(
        status_code=200,
        json_data={"message": "No existing refund found"}
    )

# Classe per simulare una risposta HTTP
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data
    
# Inietta il mock nel modulo delle routes.py
main_app.routes.mock_dbm_transaction_history = mock_dbm_transaction_history
main_app.routes.mock_dbm_market_transaction = mock_dbm_market_transaction
main_app.routes.mock_users_market_transaction = mock_users_market_transaction
main_app.routes.mock_users_market_currency = mock_users_market_currency
main_app.routes.mock_users_market_refund = mock_users_market_transaction
main_app.routes.mock_users_refund_currency = mock_users_market_currency
main_app.routes.mock_dbm_market_refund = mock_dbm_market_refund
