from .models import db, AuctionTransactions, UserTransactionHistory, Auctions, Bids
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask import Blueprint, current_app, request, jsonify
import requests

db_manager = Blueprint('db_manager', __name__)

# Endpoint: GET /admin/market/specific_auction
@db_manager.route('/admin/market/specific_auction', methods=['GET'])
def get_specific_auction_dbm():
    data = request.get_json()
    auction_id = data.get("auction_id")

    # Recupera i dettagli di un'asta specifica dal database.
    try:
        # Query per ottenere i dettagli dell'asta
        auction = db.session.query(Auctions).filter_by(id=auction_id).first()

        if not auction:
            return jsonify({"error": "Auction not found"}), 404

        # Convertiamo l'oggetto in un dizionario
        auction_details = {
            "id": auction.id,
            "gacha_id": auction.gacha_id,
            "seller_id": auction.seller_id,
            "starting_price": auction.starting_price,
            "current_price": auction.current_price,
            "auction_end": auction.auction_end,
            "status": auction.status
        }

        return jsonify({"auction": auction_details}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching auction: {str(e)}"}), 500

@db_manager.route('/admin/market/specific_gacha_auction', methods=['GET'])
def get_specific_gacha_auction_dbm():
    data = request.get_json()
    gacha_id = data.get("gacha_id")

    # Recupera i dettagli di un'asta specifica dal database.
    try:
        # Query per ottenere i dettagli dell'asta
        auction = db.session.query(Auctions).filter_by(gacha_id=gacha_id, status='active').first()

        if not auction:
            return jsonify({"active_auction": False}), 200

        # Se l'asta esiste, ritorna True
        return jsonify({"active_auction": True}), 200
    except Exception as e:
        return jsonify({"error": f"Error checking active auction: {str(e)}"}), 500
    
# Endpoint: PATCH /admin/market/specific_auction
@db_manager.route('/admin/market/specific_auction', methods=['PATCH'])
def modify_auction_status_dbm():
    data = request.get_json()
    new_status = data.get("new_status")
    auction_id = data.get("auction_id")

    # Aggiorna lo stato di un'asta nel db
    try:
        # Trova l'asta specifica
        auction = db.session.query(Auctions).filter_by(id=auction_id).first()

        if not auction:
            return jsonify({"error": "Auction not found"}), 404

        # Aggiorna lo stato
        auction.status = new_status
        db.session.commit()
        return jsonify({"message": "Auction status updated successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Annulla in caso di errore
        return jsonify({"error": f"Error updating auction status: {str(e)}"}), 500

# Endpoint: DELETE /admin/market/specific_auction
@db_manager.route('/admin/market/specific_auction', methods=['DELETE'])
def delete_auction_dbm():
    data = request.get_json()
    auction_id = data.get("auction_id")

    # Elimina un'asta dal database.
    try:
        # Trova l'asta specifica
        auction = db.session.query(Auctions).filter_by(id=auction_id).first()

        if not auction:
            return jsonify({"error": "Auction not found"}), 404

        # Elimina l'asta
        db.session.delete(auction)
        db.session.commit()
        return jsonify({"message": "Auction deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Annulla in caso di errore
        return jsonify({"error": f"Error deleting auction: {str(e)}"}), 500

# Endpoint: GET /admin/market/history
@db_manager.route('/admin/market/history', methods=['GET'])
def get_all_auctions():
    # Recupera tutte le aste dal database.
    try:
        # Query per recuperare tutte le aste
        auctions = db.session.query(Auctions).all()

        # Converti il risultato in un elenco di dizionari
        return jsonify([
            {
                "id": auction.id,
                "gacha_id": auction.gacha_id,
                "seller_id": auction.seller_id,
                "starting_price": auction.starting_price,
                "current_price": auction.current_price,
                "auction_end": auction.auction_end.isoformat(),
                "status": auction.status
            }
            for auction in auctions
        ]), 200

    except Exception as e:
        return jsonify({"error": f"Error retrieving auction history: {str(e)}"}), 500
    
# Endpoint: POST /market
@db_manager.route('/market', methods=['POST'])
def create_new_auction():
    data = request.get_json()
    gacha_id = data.get("gacha_id")
    seller_id = data.get("seller_id")
    starting_price = data.get("starting_price")
    auction_end = data.get("auction_end")

    # Crea una nuova asta e la salva nel database.
    new_auction = Auctions(
        gacha_id=gacha_id,
        seller_id=seller_id,
        starting_price=starting_price,
        current_price=starting_price,
        auction_end=auction_end,
        status='active'
    )

    try:
        db.session.add(new_auction)
        db.session.commit()
        return jsonify({"auction_id": new_auction.id, "message": "Auction created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create auction", "message": str(e)}), 500

# Endpoint: POST /market/bid
@db_manager.route('/market/bid', methods=['POST'])
def place_bid_dbm():
    #Gestisce la logica di piazzamento di un'offerta su un'asta.
    data = request.get_json()
    auction_id = data.get("auction_id")
    bidder_id = data.get("bidder_id")
    bid_amount = data.get("bid_amount")
    # Controllo se l'asta esiste
    auction = Auctions.query.filter_by(id=auction_id).first()
    if not auction:
        return jsonify({"error": "Auction not found"}), 404
    if auction.status != 'active':
        return jsonify({"error": "Auction is not active"}), 400
    if auction.seller_id == bidder_id:
        return jsonify({"error": "Bidding on your own auction"}), 400

    # Controllo che l'importo dell'offerta sia valido
    if bid_amount <= auction.current_price:
        return jsonify({"error": "Bid amount must be higher than the current price"}), 400

    try:
        # Creazione dell'offerta
        bid = Bids(
            auction_id=auction_id,
            bidder_id=bidder_id,
            bid_amount=bid_amount,
            bid_time=datetime.utcnow()
        )
        db.session.add(bid)

        # Aggiornamento del prezzo corrente nell'asta
        auction.current_price = bid_amount

        # Salvataggio delle modifiche
        db.session.commit()
        return jsonify({"bid_id": bid.id, "message": "Bid placed successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error placing bid: {str(e)}"}), 500
    
# Endpoint: GET /market + # Endpoint: GET /admin/market
@db_manager.route('/market', methods=['GET'])
def get_active_auctions():

    # Recupera tutte le aste attive dal database.
    try:
        # Query per ottenere le aste attive
        active_auctions = Auctions.query.filter(
            Auctions.status == 'active',
            Auctions.auction_end > datetime.utcnow()
        ).all()

        # Serializzazione dei dati delle aste
        auctions_list = [{
            'id': auction.id,
            'gacha_id': auction.gacha_id,
            'seller_id': auction.seller_id,
            'starting_price': auction.starting_price,
            'current_price': auction.current_price,
            'auction_end': auction.auction_end.isoformat(),
            'status': auction.status
        } for auction in active_auctions]

        return jsonify(auctions_list), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving active auctions: {str(e)}"}), 500
    
# Endpoint: POST /market/auction_win
@db_manager.route('/market/auction_win', methods=['POST'])
def get_auction_winner():
    # - Recupera il vincitore dell'asta chiusa e i dettagli del gacha.
    # - Verifica che l'asta esista e sia chiusa.
    # - Recupera l'offerta più alta associata all'asta.
    data = request.get_json()
    auction_id = data.get("auction_id")

    try:
        # Recupera l'asta chiusa
        auction = Auctions.query.filter_by(id=auction_id, status='closed').first()
        if not auction:
            return jsonify({"auction_found": False, "highest_bid_found": False}), 404

        # Recupera l'offerta più alta
        highest_bid = Bids.query.filter_by(auction_id=auction_id).order_by(Bids.bid_amount.desc()).first()
        if not highest_bid:
            return jsonify({"auction_found": True, "highest_bid_found": False}), 404
        # Ritorna i dettagli necessari
        return jsonify({
            "auction_found": True,
            "highest_bid_found": True,
            "gacha_id": auction.gacha_id,
            "highest_bid": {
                "bidder_id": highest_bid.bidder_id,
                "bid_amount": highest_bid.bid_amount
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving auction winner: {str(e)}"}), 500

# Endpoint: POST /market/auction_complete
@db_manager.route('/market/auction_complete', methods=['POST'])
def check_auction_winner():
    # - Recupera i dettagli di un'asta chiusa e del bid vincente.
    # - Verifica che l'asta esista e sia chiusa.
    # - Recupera il bid vincente associato all'asta.
    data = request.get_json()
    auction_id = data.get("auction_id")

    try:
        # Recupera l'asta chiusa
        auction = Auctions.query.filter_by(id=auction_id, status='closed').first()
        if not auction:
            return jsonify({"error": "Auction not found or not closed"}), 404

        # Recupera il bid vincente
        highest_bid = Bids.query.filter_by(auction_id=auction_id).order_by(Bids.bid_amount.desc()).first()
        if not highest_bid:
            return jsonify({"error": "No bids found for this auction"}), 404

        # Ritorna i dettagli necessari
        return jsonify({
            "auction_found": True,
            "highest_bid_found": True,
            "seller_id": auction.seller_id,
            "highest_bid": {
                "bidder_id": highest_bid.bidder_id,
                "bid_amount": highest_bid.bid_amount
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error checking auction completion: {str(e)}"}), 500

# Endpoint POST /market/transaction
@db_manager.route('/market/transaction', methods=['POST'])
def record_auction_transaction():
    # Registra una transazione di asta.
    # Crea la transazione principale, aggiorna la cronologia degli utenti
    data = request.get_json()
    auction_id = data.get("auction_id")
    buyer_id = data.get("buyer_id")
    seller_id = data.get("seller_id")
    final_price = data.get("final_price")

    try:
        # Crea la transazione principale
        transaction = AuctionTransactions(
            auction_id=auction_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            final_price=final_price
        )
        db.session.add(transaction)
        db.session.flush()  # Ottiene l'ID della transazione

        # Crea la cronologia per l'acquirente
        buyer_history = UserTransactionHistory(
            user_id=buyer_id, auction_id=auction_id,
            transaction_type='buy', amount=-final_price
        )

        # Crea la cronologia per il venditore
        seller_history = UserTransactionHistory(
            user_id=seller_id, auction_id=auction_id,
            transaction_type='sell', amount=final_price
        )

        db.session.add_all([buyer_history, seller_history])
        db.session.commit()

        return jsonify({"message": "Transaction recorded successfully", "transaction_id": transaction.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error recording transaction: {str(e)}"}), 500

# Endpoint: POST /market/auction_refund
@db_manager.route('/market/auction_refund', methods=['POST'])
def process_auction_refund():

    # Elabora i rimborsi per gli offerenti non vincenti in un'asta chiusa.
    data = request.get_json()
    auction_id = data.get("auction_id")
    try:
        # Trova l'asta chiusa
        auction = Auctions.query.filter_by(id=auction_id, status='closed').first()
        if not auction:
            return jsonify({"error": "Auction not found or not closed"}), 404

        # Trova l'offerta più alta (vincente)
        highest_bid = Bids.query.filter_by(auction_id=auction_id).order_by(Bids.bid_amount.desc()).first()
        if not highest_bid:
            return jsonify({"error": "No bids found for this auction"}), 404

        # Trova tutte le offerte perdenti
        losing_bids = Bids.query.filter(Bids.auction_id == auction_id, Bids.id != highest_bid.id).all()

        refund_failed = False
        for bid in losing_bids:
            try:
                # Invia richiesta di rimborso al microservizio TRADING_HISTORY
                trading_url = current_app.config['TRADING_HISTORY_URL'] + "/market/refund"
                response = requests.post(trading_url, json={
                    "user_id": bid.bidder_id,
                    "auction_id": auction_id,
                    "amount": bid.bid_amount
                }, timeout=5,verify=False)
                
                # Se la richiesta di rimborso non ha successo, segna il fallimento
                if response.status_code not in [200,409]:
                    refund_failed = True
            except Exception as e:
                refund_failed = True

        if refund_failed:
            return jsonify({"success": False, "message": "Refund failed for one or more bidders"}), 500

        return jsonify({"success": True, "message": "Refunds processed successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": f"Error processing refund: {str(e)}"}), 500

# Endpoint: GET /market/transaction_history
@db_manager.route('/market/transaction_history', methods=['GET'])
def get_transaction_history_dbm():
    user_id = request.args.get("user_id")

    try:
        # Recupera la cronologia delle transazioni
        transactions = UserTransactionHistory.query.filter_by(user_id=user_id).all()
        if not transactions:
            return jsonify({"transactions": [], "message": "No transactions found for this user"}), 404

        result = [
            {
                "auction_id": t.auction_id,
                "transaction_type": t.transaction_type,
                "amount": t.amount,
                "transaction_time": t.transaction_time
            }
            for t in transactions
        ]
        return jsonify({"transactions": result}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching transaction history: {str(e)}"}), 500
    
# Endpoint GET /market/check_refund
@db_manager.route('/market/check_refund', methods=['GET'])
def check_existing_refund():
    user_id = request.args.get("user_id")
    auction_id = request.args.get("auction_id")

    try:
        existing_refund = UserTransactionHistory.query.filter_by(
            user_id=user_id, auction_id=auction_id, transaction_type="refund"
        ).first()
        if existing_refund:
            return jsonify({"error": "Refund already processed"}), 409

        return jsonify({"message": "No existing refund found"}), 200
    except Exception as e:
        return jsonify({"error": f"Error checking refund: {str(e)}"}), 500
    
# Endpoint GET /market/expired_auctions
@db_manager.route('/market/expired_auctions', methods=['GET'])
def get_expired_auctions():
    # Recupera tutte le aste scadute e attive rispetto a una data specificata.
    current_time = datetime.utcnow()

    try:
        # Recupera aste scadute e attive
        expired_auctions = Auctions.query.filter(
            Auctions.auction_end <= current_time,
            Auctions.status == 'active'
        ).all()

        # Prepara i dati per la risposta
        result = [
            {
                "id": auction.id,
                "gacha_id": auction.gacha_id,
                "seller_id": auction.seller_id,
                "auction_end": auction.auction_end,
                "current_price": auction.current_price,
                "starting_price": auction.starting_price,
                "status": auction.status
            }
            for auction in expired_auctions
        ]

        return jsonify({"expired_auctions": result}), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving expired auctions: {str(e)}"}), 500
    
@db_manager.route("/market/losing_bids/<int:auction_id>", methods=["GET"])
def get_losing_bids(auction_id):
    try:
        # Trova l'offerta più alta per l'asta
        highest_bid = (
            db.session.query(Bids)
            .filter_by(auction_id=auction_id)
            .order_by(Bids.bid_amount.desc())
            .first()
        )

        # Trova tutte le offerte perdenti non ancora rimborsate
        losing_bids = (
            db.session.query(Bids)
            .filter(
                Bids.auction_id == auction_id,
                Bids.id != (highest_bid.id if highest_bid else None),  # Ignora l'offerta vincente
                Bids.refunded == False  # Solo offerte non ancora rimborsate
            )
            .all()
        )

        # Trasforma le offerte perdenti in un formato JSON serializzabile
        losing_bids_json = [
            {
                "id": bid.id,
                "auction_id": bid.auction_id,
                "bidder_id": bid.bidder_id,
                "bid_amount": bid.bid_amount
            }
            for bid in losing_bids
        ]

        return jsonify({"losing_bids": losing_bids_json}), 200

    except Exception as e:
        return jsonify({
            "error": "Error fetching losing bids for auction",
            "auction_id": auction_id,
            "details": str(e)
        }), 500
    
@db_manager.route('/market/update_auction_status/<int:auction_id>', methods=['PATCH'])
def update_auction_status(auction_id):
    # Recupera il nuovo stato dall'input JSON
    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "New status is required"}), 400

    try:
        # Trova l'asta specifica
        auction = db.session.query(Auctions).filter_by(id=auction_id).first()

        if not auction:
            return jsonify({"error": "Auction not found"}), 404

        # Aggiorna lo stato dell'asta
        auction.status = new_status
        db.session.commit()

        return jsonify({"message": "Auction status updated successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Annulla la transazione in caso di errore
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
@db_manager.route('/market/update_bid_status/<int:bid_id>', methods=['PATCH'])
def update_bid_status(bid_id):
    try:
        # Recupera lo stato aggiornato dall'input JSON
        data = request.get_json()
        new_status = data.get("refunded")

        if new_status is None:
            return jsonify({"error": "Refunded status is required"}), 400

        # Trova l'offerta specifica
        bid = db.session.query(Bids).filter_by(id=bid_id).first()

        if not bid:
            return jsonify({"error": "Bid not found"}), 404

        # Aggiorna lo stato del rimborso
        bid.refunded = new_status
        db.session.commit()

        return jsonify({"message": "Bid status updated successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
@db_manager.route('/market/add_refund', methods=['POST'])
def add_refund():
    data = request.get_json()
    user_id = data.get("user_id")
    auction_id = data.get("auction_id")
    transaction_type = data.get("transaction_type")
    amount = data.get("amount")

    if not all([user_id, auction_id, transaction_type, amount]):
        return jsonify({"error": "Invalid data"}), 400
    
    try:
        user_id = int(user_id)
        auction_id = int(auction_id)
        amount = int(amount)
        if amount <= 0 or transaction_type != "refund":
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid input format"}), 400

    # Salva la transazione nel database
    try:
        refund_transaction = UserTransactionHistory(
            user_id=user_id,
            auction_id=auction_id,
            transaction_type=transaction_type,
            amount=amount
        )
        db.session.add(refund_transaction)
        db.session.commit()
        return jsonify({"message": "Transaction added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add transaction: {str(e)}"}), 500







