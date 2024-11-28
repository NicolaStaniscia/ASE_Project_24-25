from flask import Flask, request, jsonify, make_response
import mysql.connector
from mysql.connector import Error
import hashlib
import json

app = Flask(__name__)

# Configurazione del database MySQL
db_config = {
    'host': 'users_db',
    #'port': '3306',
    'user': 'user',          # Nome utente MySQL
    'password': 'ase2425',  # Password MySQL
    'database': 'account_management'    # Nome del database
}
# Connessione al database
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        raise Exception(f"Error connecting to MySQL: {e}")

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    salt = data.get('salt')
    password = data.get('password')

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # Verifica se l'utente esiste già
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "User already exists"}), 409


        # Esecuzione della query
        cursor.execute("INSERT INTO users (username, salt, password) VALUES (%s, %s, %s)", (username, salt, password))

        # Commit per salvare la modifica nel database
        connection.commit()

        return jsonify({"message": f"User {username} created successfully"}), 201

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/check_credentials', methods=['POST'])
def check_credentials():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if user_type == 'normal':
            # Verifica se l'utente esiste già
            cursor.execute("SELECT salt,password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result is None:
                return jsonify({"status": False}), 401
            
            #computo l'hash della password e verifico che sia corretta
            hashed_password = hashlib.sha256((result[0] + password).encode('utf-8')).hexdigest()

            if result[1] == hashed_password:
                # Aggiorno il campo last_access
                cursor.execute("UPDATE users SET last_access = NOW() WHERE username = %s", (username,))
                # Salva le modifiche
                connection.commit()
                return jsonify({"status": True}), 200
            else:
                return jsonify({"status": False}), 401
        
        if user_type == 'admin':
            # Verifica se l'utente esiste già
            cursor.execute("SELECT salt,password FROM users_admin WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result is None:
                return jsonify({"status": False}), 401
            
            #computo l'hash della password e verifico che sia corretta
            hashed_password = hashlib.sha256((result[0] + password).encode('utf-8')).hexdigest()

            if result[1] == hashed_password:
                return jsonify({"status": True}), 200
            else:
                return jsonify({"status": False}), 401


    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/get_id/<username>/<user_type>', methods=['GET'])
def get_id(username,user_type):

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if user_type == 'normal':
            # Verifica se l'utente esiste già
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result is None:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({"id": result[0]}), 200
        
        if user_type == 'admin':
            # Verifica se l'utente esiste già
            cursor.execute("SELECT id FROM users_admin WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result is None:
                return jsonify({"error": "Admin not found"}), 404
            
            return jsonify({"id": result[0]}), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/modify_user', methods=['PATCH'])
def modify_user():
    data = request.get_json()
    username = data.get('username')
    salt = data.get('salt')
    password = data.get('password')

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # Esecuzione della query
        cursor.execute("UPDATE users SET salt = %s, password = %s WHERE username = %s", (salt, password, username))
        # Commit per salvare la modifica nel database
        connection.commit()

        return jsonify({"message": f"User:{username}. Password modified successfully, you need to log in again."}), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/remove_user/<username>', methods=['DELETE'])
def remove_user(username):

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Esecuzione della query
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        # Commit per salvare la modifica nel database
        connection.commit()

        return jsonify({"message": f"User:{username} eliminated successfully."}), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/increase_user_currency', methods=['POST'])
def increase_user_currency():
    data = request.get_json()
    username = data.get('username')
    pack = data.get("pack")
    currency = 0
    amount_spent = 0

    if pack == 1:
        currency = 200
        amount_spent = 10
    if pack == 2:
        currency = 500
        amount_spent = 20
    if pack == 3:
        currency = 1000
        amount_spent = 40

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # Ottieni l'id dell'utente
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        user_id = result[0]  # Otteniamo l'id dell'utente

        # Aggiungi in-game currency all'utente
        cursor.execute("UPDATE users SET in_game_currency = in_game_currency + %s WHERE id = %s", (currency, user_id))
        connection.commit()  # Commit per salvare le modifiche nel database

        cursor.execute("INSERT INTO payments (user_id, amount_spent, in_game_currency_purchased) VALUES (%s, %s, %s)", (user_id, amount_spent, currency))
        connection.commit()  # Commit per salvare la transazione

        return jsonify({"message": "Transaction successfull, currency updated."}), 201

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

# Used to roll a gacha
@app.route('/get_user_currency/<int:user_id>', methods=['GET'])
def get_user_currency(user_id):

    try:
        connection = get_db_connection()
        if not connection:
            raise Exception('Failed to connect to the DB')
        
        # Query
        query = "SELECT in_game_currency FROM users WHERE id = %s"
        cursor = connection.cursor()

        # Execute query
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        return make_response(jsonify(result), 200)
        
    except Exception as e:
        return make_response(jsonify(error=str(e)), 500)
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

# After roll a gacha
@app.route('/edit/currency', methods=['PATCH'])
def decrease_currency():
    data = request.get_json()

    try:
        if not data or ('user_id' not in data) or ('currency' not in data):
            return make_response(jsonify(error="Bad request"), 400)
        
        connection = get_db_connection()
        if not connection:
            raise Exception('Failed to connect to the DB')
        
        new_currency = data['currency']
        user_id = data['user_id']
        
        # Query
        query = 'UPDATE users SET in_game_currency = %s WHERE id = %s'
        cursor = connection.cursor()

        # Execute query
        cursor.execute(query, (new_currency, user_id))
        connection.commit()

        return make_response(jsonify(message="Currency updated"), 200)

    except Exception as e:
        if connection:
            connection.rollback()
        return make_response(jsonify(error=str(e)), 500)
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

#ADMIN SERVICE

# Used by see_gacha_collection microservice
@app.route('/usernames', methods=['GET'])
def usernames():
    data = request.get_json()
    ids = data.get('ids', [])
    print(ids)

    try:
        connection = get_db_connection()
        if not connection:
            raise Exception('Failed to connect to the DB')
        
        # Query
        query = "SELECT username FROM users WHERE id = %s"
        cursor = connection.cursor()

        # List
        usernames = []

        # Execute query
        for user_id in ids:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            usernames.append(
                {"id": user_id, "username": result[0]}
            )

        if not usernames: return make_response(jsonify(error='No users'), 400)

        # Create a json array
        jsonArray = json.dumps(usernames, indent=4)

        return make_response(jsonify(usernames), 200)
        
    except Exception as e:
        return make_response(jsonify(error=str(e)), 500)
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route('/get_all_users/<username>', methods=['GET'])
def get_all_users(username):
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if username == "all":
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()

        # Restituisci i risultati in JSON
        return jsonify(result), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/modify_user_by_admin', methods=['PATCH'])
def modify_user_by_admin():
    data = request.get_json()
    username = data.get('username')
    new_currency = data.get('new_currency')

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # Esecuzione della query
        cursor.execute("UPDATE users SET in_game_currency = %s WHERE username = %s", (new_currency, username))
        # Commit per salvare la modifica nel database
        connection.commit()

        return jsonify({"message": f"User:{username}. Currency modified successfully, new currency : {new_currency}."}), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/check_payments/<username>', methods=['GET'])
def check_payments(username):

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result is None:
            return jsonify({"error": f"User {username} not found."}), 404
        user_id = result[0]
        cursor.execute("SELECT * FROM payments WHERE user_id = %s", (user_id,))
        payments_result = cursor.fetchall()
        if not payments_result:
            return jsonify({"message": f"No transactions found for user {username}."}), 404
        
        return jsonify(payments_result), 200

    except Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


if __name__ == '__main__':
    app.run(debug=True)