import requests
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from .models import Auctions
from datetime import datetime

auction_market = Blueprint('auction_market', __name__)

# Funzione d'appoggio per il path del db_manager
def dbm_url(path):
    return current_app.config['DBM_URL'] + path

# Funzione d'appoggio per verifica admin
def is_admin():
    jwt_payload = get_jwt()
    return jwt_payload.get("role") == "admin"

# Funzione d'appoggio per verifica autenticazione JWT
def is_user_authenticated(user_id):
    return get_jwt_identity() == str(user_id)

# Funzione per recuperare le aste attive, condivisa tra user e admin
def fetch_active_auctions():
    try:
        response = requests.get(dbm_url("/market"), timeout=5, verify=False)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch active auctions'}), response.status_code

        auctions = response.json()
        return jsonify(auctions), 200
    except requests.RequestException as e:
        return jsonify({'error': f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint: GET /market
@auction_market.route('/market', methods=['GET'])
@jwt_required()
def get_market():
    return fetch_active_auctions()
    
# Endpoint: GET /admin/market
@auction_market.route("/admin/market", methods=["GET"])
@jwt_required()
def get_market_admin():
    if not is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
    return fetch_active_auctions()

# Endpoint: GET /admin/market/specific_auction
@auction_market.route("/admin/market/specific_auction", methods=["GET"])
@jwt_required()
def get_specific_auction():
    if not is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
    
    auction_id = request.args.get("auctionID")

    # Verifica che l'ID dell'asta sia stato fornito
    if not auction_id or not auction_id.isdigit():
        return jsonify({"error": "ID dell'asta non fornito"}), 400

    try:
        response = requests.get(dbm_url("/admin/market/specific_auction"), json={"auction_id":auction_id},timeout=5, verify=False)
        if response.status_code == 404:
            return jsonify({"error": "Auction not found"}), 404
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch auction details"}), response.status_code

        return jsonify(response.json()), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint: PATCH /admin/market/specific_auction
@auction_market.route('/admin/market/specific_auction', methods=['PATCH'])
@jwt_required()
def modify_auction_status():
    if not is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
    
    # Ottieni l'ID dell'asta dai parametri della query
    auction_id = request.args.get('auctionID')

    if not auction_id or not auction_id.isdigit():
        return jsonify({"error": "Valid auctionID is required"}), 400

    # Ottieni il nuovo stato dell'asta dal corpo della richiesta
    new_status = request.json.get("status")  # es. "canceled", "closed", "active", "suspended"

    if new_status not in ["canceled", "closed", "active", "suspended"]:
        return jsonify({"error": "Valid 'status' is required in request body"}), 400

    try:
        response = requests.patch(dbm_url("/admin/market/specific_auction"), 
                                  json={"auction_id":auction_id, "new_status": new_status}, timeout=5, verify=False)
        if response.status_code == 404:
            return jsonify({"error": "Auction not found"}), 404
        if response.status_code != 200:
            return jsonify({"error": "Failed to update auction status"}), response.status_code

        return jsonify({"message": "Auction status updated successfully"}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint: DELETE /admin/market/specific_auction
@auction_market.route('/admin/market/specific_auction', methods=['DELETE'])
@jwt_required()
def delete_auction():
    if not is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
    
    # Ottieni l'ID dell'asta dai parametri della query
    auction_id = request.args.get('auctionID')

    if not auction_id or not auction_id.isdigit():
        return jsonify({"error": "Valid auctionID is required"}), 400
    
    try:
        response = requests.delete(dbm_url("/admin/market/specific_auction"), json={"auction_id":auction_id}, timeout=5, verify=False)
        if response.status_code == 404:
            return jsonify({"error": "Auction not found"}), 404
        if response.status_code != 200:
            return jsonify({"error": "Failed to delete auction"}), response.status_code

        return jsonify({"message": "Auction deleted successfully"}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint: GET /admin/market/history
@auction_market.route('/admin/market/history', methods=['GET'])
@jwt_required()
def get_market_history():
    if not is_admin():
        return jsonify({"error": "Admin privileges required"}), 403

    try:
        response = requests.get(dbm_url("/admin/market/history"), timeout=5, verify=False)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch market history'}), response.status_code

        return jsonify({"market_history": response.json()}), 200
    except requests.RequestException as e:
        return jsonify({'error': f"Error communicating with DBM: {str(e)}"}), 500
    
# Endpoint: POST /market
@auction_market.route('/market', methods=['POST'])
@jwt_required()
def create_auction():
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization':auth_headers}
    data = request.get_json()

    # Recupero dei campi POST
    gacha_id = data.get('gacha_id')
    seller_id = data.get('seller_id')
    starting_price = data.get('starting_price')
    auction_end_str = data.get('auction_end')

    # Verifica che i campi richiesti siano presenti
    if not all([gacha_id, seller_id, starting_price, auction_end_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    if not is_user_authenticated(seller_id):
        return jsonify({"error": "User not authorized to create auction for this seller"}), 403

    try:
        auction_end = datetime.fromisoformat(auction_end_str).replace(tzinfo=None)  # Converte l'ISO string a datetime
    except ValueError:
        return jsonify({'error': 'Invalid auction_end format. Expected ISO 8601.'}), 400

    if auction_end <= datetime.utcnow():
        return jsonify({'error': 'auction_end must be a future date'}), 400

    # Verifica che il gacha non sia già in asta attiva
    try:
        # Chiamata al DBM per verificare se esiste un'asta attiva per il gacha_id
        dbm_response = requests.get(
            dbm_url("/admin/market/specific_gacha_auction"),
            json={"gacha_id": gacha_id},
            timeout=5,
            verify=False
        )

        if dbm_response.status_code != 200:
            return jsonify({'error': 'Failed to check active auction status'}), dbm_response.status_code

        active_auction_info = dbm_response.json()
        if active_auction_info.get("active_auction"):
            return jsonify({'error': 'Gacha is already listed in an active auction'}), 409

    except requests.RequestException as e:
        return jsonify({'error': f"Error communicating with DBM: {str(e)}"}), 500

    
    # Verifica che il gacha appartenga all'user, prendo la collezione intera
    # Header per la richiesta con il token JWT
    try:
        collection_response = requests.get(
            f"{current_app.config['COLLECTION_SEE_URL']}/collection",
            headers=new_header,
            timeout=5,
            verify=False
        )
        if collection_response.status_code != 200:
            return jsonify({'error': 'Error retrieving user collection'}), collection_response.status_code
        

        collection = collection_response.json()
        if not any(item['idOwn'] == gacha_id for item in collection):
            return jsonify({'error': 'Gacha not found in user collection'}), 404

    except requests.RequestException as e:
        return jsonify({'error': f"Error communicating with COLLECTION service: {str(e)}"}), 500

    # Chiamata al db-manager per creare l'asta
    try:
        response = requests.post(dbm_url("/market"), json={
            "gacha_id": gacha_id,
            "seller_id": seller_id,
            "starting_price": starting_price,
            "auction_end": auction_end_str
        }, timeout=5, verify=False)

        if response.status_code != 201:
            return jsonify({"error": "Failed to create auction"}), response.status_code

        return jsonify({"message": "Auction created successfully", "auction_id": response.json().get("auction_id")}), 201
    except requests.RequestException as e:
        return jsonify({'error': f"Error communicating with DBM: {str(e)}"}), 500

# Endpoint: POST /market/bid
@auction_market.route('/market/bid', methods=['POST'])
@jwt_required()
def place_bid():
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization':auth_headers}
    data = request.get_json()
    auction_id = data.get('auction_id')
    bidder_id = data.get('bidder_id')
    bid_amount = data.get('bid_amount')

    # Controllo se i dati obbligatori sono presenti
    if not all([auction_id, bidder_id, bid_amount]):
        return jsonify({"error": "auction_id, bidder_id, and bid_amount are required"}), 400
    
    # Verifica che l'utente autenticato corrisponda al bidder_id
    if not is_user_authenticated(bidder_id):
        return jsonify({"error": "User not authorized to place bid on behalf of this bidder"}), 403

    # Verifica tipi
    try:
        bid_amount = int(bid_amount)
        auction_id = int(auction_id)
        bidder_id = int(bidder_id)
    except ValueError:
        return jsonify({"error": "Invalid input format"}), 400
    
    if bid_amount <= 0:
        return jsonify({"error": "Bid amount must be greater than zero"}), 400
    
    # Verifica del credito disponibile per il bidder (CONTROLLA SE SERVE L'USERD ID NELL'HEADER)
    
    response = requests.get(f"{current_app.config['USERS_URL']}/account_management/get_currency", headers=new_header,verify=False)
    if response.status_code == 404:
        return jsonify({"error": "Not found"}), 404
    user_credit = response.json()['points'][0]
    # Controllo se l'utente ha abbastanza credito per l'offerta
    if user_credit < bid_amount:
        return jsonify({"error": "Insufficient credit for this bid"}), 400

    try:
        response = requests.post(dbm_url("/market/bid"), json={
            "auction_id": auction_id,
            "bidder_id": bidder_id,
            "bid_amount": bid_amount
        }, verify=False)

        if response.status_code != 201:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code
        
        # Fai chiamata al servizio di account_management per scalare la currency
        new_balance = user_credit - bid_amount
        response = requests.patch('https://account_management:5000/account_management/currency', json={
            "currency": new_balance
        }, headers=new_header,verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Failed to update user balance")}), response.status_code
        
        return jsonify(response.json()), 201
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to communicate with db_manager: {str(e)}"}), 500

# Endpoint: POST /market/auction_win
@auction_market.route('/market/auction_win', methods=['POST'])
def receive_gacha():
    data = request.get_json()
    auction_id = data.get("auction_id")

    if not auction_id or not auction_id.isdigit():
       return jsonify({"error": "Valid auction_id is required"}), 400 

    try:
        # Chiamata al db-manager per verificare l'asta e il vincitore
        response = requests.post(dbm_url("/market/auction_win"), json={"auction_id":auction_id},timeout=5, verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

        result = response.json()

        if not result["auction_found"]:
            return jsonify({"error": "Auction not found or not closed"}), 404
        if not result["highest_bid_found"]:
            return jsonify({"error": "Winner does not match highest bid"}), 400

    # Trasferimento del gacha al vincitore tramite il servizio COLLECTION
        collection_url = f"{current_app.config['COLLECTION_EDIT_URL']}/edit/collection"
        response = requests.post(collection_url, json={
            "gacha_id": result["gacha_id"],
            "user_id": result["highest_bid"]["bidder_id"]
        }, timeout=5, verify=False)

        if response.status_code != 200:
            return jsonify({"error": "Failed to transfer gacha ownership"}), 500
    
        # Successo
        winner_id = result["highest_bid"]["bidder_id"]
        return jsonify({"message": f"Gacha successfully transferred to winner {winner_id}"}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to communicate with db_manager: {str(e)}"}), 500


# Endpoint: POST /market/auction_complete
@auction_market.route('/market/auction_complete', methods=['POST'])
def complete_auction():
    data = request.get_json()
    auction_id = data.get("auction_id")

    if not auction_id or not auction_id.isdigit():
       return jsonify({"error": "Valid auction_id is required"}), 400 

    try:
        # Chiamata al db-manager per recuperare i dettagli dell'asta e del vincitore
        response = requests.post(dbm_url("/market/auction_complete"), json={"auction_id":auction_id},timeout=5, verify=False)

        if response.status_code != 200:
            return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

        result = response.json()
        if not result["auction_found"]:
            return jsonify({"error": "Auction not found or not closed"}), 404
        if not result["highest_bid_found"]:
            return jsonify({"error": "Bid not found"}), 400

        # Dettagli necessari per la transazione
        buyer_id = result["highest_bid"]["bidder_id"]
        seller_id = result["seller_id"]
        final_price = result["highest_bid"]["bid_amount"]

        # Chiamata al microservizio TRADING_HISTORY per registrare la vendita
        trading_url = current_app.config['TRADING_HISTORY_URL'] + "/market/transaction"
        response = requests.post(trading_url, json={
            "auction_id": auction_id,
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "final_price": final_price
        }, verify=False)

        if response.status_code != 200:
            return jsonify({"error": "Failed to record transaction in trading history"}), 500
        
        # Successo
        return jsonify({"message": "Currency transferred to seller successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Endpoint: POST /market/auction_refund
@auction_market.route('/market/auction_refund', methods=['POST'])
def refund_bid():
    # Chiamato dal job di asta closed, farà i rimborsi mancanti
    
    data = request.get_json()
    auction_id = data.get("auction_id")

    # Trovare l'asta specifica
    try:
        response = requests.get(dbm_url("/admin/market/specific_auction"), json={"auction_id":auction_id},timeout=5, verify=False)
        response_data = response.json()
        if response_data["auction"]["status"] != "closed" or response.status_code == 404:
            return jsonify({"error": "Auction not found or not closed"}), 404
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch auction details"}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": f"Error communicating with DBM: {str(e)}"}), 500

    # Chiama il db-manager per processare i rimborsi
    response = requests.post(dbm_url("/market/auction_refund"), json={"auction_id":auction_id},timeout=5, verify=False)

    if response.status_code != 200:
        return jsonify({"error": response.json().get("error", "Unknown error")}), response.status_code

    result = response.json()
    if not result["success"]:
        return jsonify({"error": result["message"]}), 500

    return jsonify({"message": "Refund processed for all losing bidders"}), 200




