from flask import Blueprint, jsonify, request, current_app
from .models import db,UserTransactionHistory
import requests
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token


trading_history = Blueprint('trading_history', __name__)

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

    #### CORREGGERE CON CHIAMATA AL DBM
    transaction_history = UserTransactionHistory.query.filter_by(user_id=user_id).all()
    if not transaction_history:
        return jsonify({"transactions": [], "message": "No transactions found for this user"}), 200

    result = [
        {
            "auction_id": t.auction_id,
            "transaction_type": t.transaction_type,
            "amount": t.amount,
            "transaction_time": t.transaction_time
        }
        for t in transaction_history
    ]

    return jsonify({"transactions": result}), 200

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
        
        # Chiamata al db-manager per registrare la transazione
        response = requests.post(dbm_url("/market/transaction"), json={
            "auction_id": auction_id,
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "final_price": final_price
        }, verify=False)

        # Recupera il credito del venditore
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{current_app.config['USERS_URL']}/account_management/get_currency", headers=headers,verify=False)
        if response.status_code == 404:
            return jsonify({"error": "Not found"}), 404
        
        user_credit = response.json()['points'][0]

        # Calcolo il nuovo saldo
        new_balance = user_credit + final_price
        # Aggiorna il saldo
        response = requests.patch('https://account_management:5000/account_management/currency', json={
            "currency": new_balance
        }, headers=headers,verify=False)

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

    #### CORREGGERE CON CHIAMATA AL DBM
    existing_refund = UserTransactionHistory.query.filter_by(
        user_id=user_id, auction_id=auction_id, transaction_type="refund"
    ).first()
    if existing_refund:
        return jsonify({"error": "Refund already processed"}), 409
    
    try:
        token = create_access_token(
            identity=str(user_id)
        )
        
        # Effettua il rimborso aggiornando il saldo dell'utente
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{current_app.config['USERS_URL']}/account_management/get_currency", headers=headers, verify=False)

        if response.status_code == 404:
            return jsonify({"error": "User not found"}), 404

        user_credit = response.json()['points'][0]

        # Calcola il nuovo saldo
        new_balance = user_credit + amount

        # Aggiorna il saldo dell'utente
        response = requests.patch(f"{current_app.config['USERS_URL']}/account_management/currency", json={
            "currency": new_balance
        }, headers=headers, verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

        result = response.json()
        if not result["success"]:
            return jsonify({"error": result["message"]}), 500


        refund_transaction = UserTransactionHistory(
            user_id=user_id,
            auction_id=auction_id,
            transaction_type="refund",
            amount=amount
        )
        db.session.add(refund_transaction)
        db.session.commit()

        return jsonify({"message": "Refund processed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Refund failed: {str(e)}"}), 500