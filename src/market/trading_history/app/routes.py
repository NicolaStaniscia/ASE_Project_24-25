from flask import Blueprint, jsonify, request, current_app
from .models import db,UserTransactionHistory
import requests
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token


trading_history = Blueprint('trading_history', __name__)

# Mock functions
mock_dbm_transaction_history = None
mock_dbm_market_transaction = None
mock_users_market_transaction = None
mock_users_market_currency = None
mock_users_market_refund = None
mock_users_refund_currency = None
mock_dbm_market_refund = None
mock_dbm_refund_transaction = None

def dbm_url(path):
    return current_app.config['DBM_URL'] + path

# Endpoint: GET /market/transaction_history
@trading_history.route('/market/transaction_history', methods=['GET'])
@jwt_required()
def get_transaction_history():

    current_user = get_jwt_identity()
    user_id = request.args.get("user_id")

    # Se l'utente non è lo stesso dell'user_id richiesto, restituisci errore
    if current_user != str(user_id):
        return jsonify({"error": "You are not authorized to access this user's transactions"}), 403

    # Valida user_id
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid User ID format"}), 400

    # Chiamata al db_manager per recuperare la cronologia delle transazioni
    try:
        if mock_dbm_transaction_history:
            response = mock_dbm_transaction_history(user_id=user_id)
        else:
            response = requests.get(
                dbm_url("/market/transaction_history"), 
                params={"user_id": user_id}, 
                timeout=5, 
                verify=False
            )
        if response.status_code == 404:
            return jsonify({"transactions": [], "message": "No transactions found for this user"}), 200
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch transaction history"}), response.status_code

        result = response.json().get("transactions", [])
        return jsonify({"transactions": result}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint POST /market/transaction
@trading_history.route('/market/transaction', methods=['POST'])
def record_transaction():
    # l'endpoint viene chiamato solo da /auction_complete
    data = request.get_json()
    auction_id = data.get('auction_id')
    buyer_id = data.get('buyer_id')
    seller_id = data.get('seller_id')
    final_price = data.get('final_price')

    if not all([auction_id, buyer_id, seller_id, final_price]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        auction_id = int(auction_id)
        buyer_id = int(buyer_id)
        seller_id = int(seller_id)
        final_price = int(final_price)
        if final_price <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid input format or negative price"}), 400

    try:
        token = create_access_token(
            identity=str(seller_id)
        )
        if mock_dbm_market_transaction:
            response = mock_dbm_market_transaction()
        else:
            # Chiamata al db-manager per registrare la transazione
            response = requests.post(dbm_url("/market/transaction"), json={
                "auction_id": auction_id,
                "buyer_id": buyer_id,
                "seller_id": seller_id,
                "final_price": final_price
            }, timeout=5,verify=False)

        # Recupera il credito del venditore
        headers = {"Authorization": f"Bearer {token}"}
        if mock_users_market_transaction:
            response = mock_users_market_transaction(user_id=seller_id)
        else:
            response = requests.get('https://account_management:5000/account_management/get_currency', headers=headers,timeout=5,verify=False)
        if response.status_code == 404:
            return jsonify({"error": "Not found"}), 404
        if response.status_code == 403:
            return jsonify({"error": "Unauthorized"}), 403
        
        user_credit = response.json()['points'][0]

        # Calcolo il nuovo saldo
        new_balance = user_credit + final_price
        # Aggiorna il saldo
        if mock_users_market_currency:
            response = mock_users_market_currency()
        else:
            response = requests.patch('https://account_management:5000/currency', json={
            "currency": new_balance
        }, headers=headers,timeout=5,verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

        result = response.json()
        if not result["success"]:
            return jsonify({"error": result["message"]}), 500

        return jsonify({"message": "Transaction recorded successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Transaction failed: {str(e)}"}), 500

# Endpoint POST /market/refund
@trading_history.route('/market/refund', methods=['POST'])
def process_refund():
    # viene chiamato dallo scheduler per i rimborsi "attivi", aste non scadute
    # e dal dbm che elabora i rimborsi "scaduti", completandone la logica

    data = request.get_json()
    user_id = data.get("user_id")
    auction_id = data.get("auction_id")
    amount = data.get("amount")

    if not all([user_id, auction_id, amount]):
        return jsonify({"error": "Invalid data"}), 400
    
    try:
        user_id = int(user_id)
        auction_id = int(auction_id)
        amount = int(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid input format or negative amount"}), 400

     # Verifica rimborsi esistenti tramite db_manager
    try:
        if mock_dbm_market_refund:
            dbm_response = mock_dbm_market_refund(user_id=user_id)
        else:
            dbm_response = requests.get(
                dbm_url("/market/check_refund"),
                params={"user_id": user_id, "auction_id": auction_id},
                timeout=5,
                verify=False
            )
        if dbm_response.status_code == 409:
            return jsonify({"error": "Refund already processed"}), 409
        if dbm_response.status_code != 200:
            return jsonify({"error": "Error checking refund status"}), dbm_response.status_code
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500
    
    try:
        token = create_access_token(
            identity=str(user_id)
        )
        
        # Effettua il rimborso aggiornando il saldo dell'utente
        headers = {"Authorization": f"Bearer {token}"}
        if mock_users_market_refund:
            response = mock_users_market_refund(user_id=user_id)
        else:
            response = requests.get('https://account_management:5000/account_management/get_currency', headers=headers, timeout=5,verify=False)
        if response.status_code == 404:
            return jsonify({"error": "User not found"}), 404

        user_credit = response.json()['points'][0]

        # Calcola il nuovo saldo
        new_balance = user_credit + amount
        # Aggiorna il saldo dell'utente
        if mock_users_refund_currency:
            response = mock_users_refund_currency()
        else:
            response = requests.patch('https://account_management:5000/currency', json={
                "currency": new_balance
            }, headers=headers, timeout=5,verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

        # Invia la richiesta al DBM per registrare la transazione
        refund_data = {
            "user_id": user_id,
            "auction_id": auction_id,
            "transaction_type": "refund",
            "amount": amount
        }
        if mock_dbm_refund_transaction:
            dbm_add_response = mock_dbm_refund_transaction()
        else:
            dbm_add_response = requests.post(
                dbm_url("/market/add_refund"),
                json=refund_data,
                timeout=5,
                verify=False
            )

        if dbm_add_response.status_code != 201:
            return jsonify({"error": "Failed to record transaction in DBM"}), dbm_add_response.status_code

        return jsonify({"message": "Refund processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Refund failed: {str(e)}"}), 500