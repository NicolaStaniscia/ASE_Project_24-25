from flask import Flask, request, jsonify, make_response
import requests
import os
import hashlib
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from datetime import timedelta


app = Flask(__name__)

# Configurazione della chiave segreta per JWT
app.config["JWT_SECRET_KEY"] = "JwtGACHA2425"  # Cambia con una chiave sicura
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers']

jwt = JWTManager(app)

# Set per i token revocati
revoked_tokens = set()

#MOCK tests
mock_request = None
def send_request(endpoint: str, **kwargs):
    if mock_request:
        response = mock_request(endpoint, **kwargs)
        if not isinstance(response, dict):
            raise ValueError("Invalid response format")
        return response
    else:
        raise NotImplementedError('mock_request not implemented')

# Callback per verificare se un token è stato revocato
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]  # Ottieni il "jti" (JWT ID), che è un identificatore unico del token
    return jti in revoked_tokens  # Controlla se il "jti" è nella blacklist

@app.route('/account_management/create_user_account', methods=['POST'])
def create_user_account():
    # Estrarre i dati dal corpo della richiesta
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return make_response(jsonify({"error": 'username and password are required'}), 400)
    
    # a questo punto si genera il salt casuale e l'hash della password
    salt = os.urandom(16).hex()
    hashed_password = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    params = {
            "username": username,
            "salt": salt,
            "password": hashed_password
        }

    response = send_request('create_user', **params)
    return make_response(jsonify(response), 201)

@app.route('/account_management/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_response(jsonify({"error": 'username and password are required'}), 400)
    
    params = {
            "username": username,
            "password": password
        }

    response = send_request('check_credentials', **params)
    access_token = create_access_token(
                identity=str(id),
                additional_claims={
                    "username": username,
                    "role": 'user'
                }
            )
    return make_response(jsonify({"access_token": access_token, "message" : response.get("message")}), 200)

@app.route('/account_management/logout', methods=['POST'])
@jwt_required()  # Richiede un token valido
def logout():
    data = request.get_json()
    username = data.get('username')
    # Controllare che i campi siano forniti
    if not username:
        return jsonify({"error": "username is required"}), 400
    
    current_user = get_jwt()["username"]

    if username == current_user:
        jti = get_jwt()["jti"]  # Ottieni il "jti" dal payload del token corrente
        revoked_tokens.add(jti)  # Aggiungi il "jti" alla blacklist (revoca il token)
        return jsonify({"message": f"{current_user} logged out, token revoked."}), 200
    else:
        return jsonify({"error": "Unauthorized"}), 403

@app.route('/account_management/modify_user_account', methods=['PATCH'])
@jwt_required()  # Richiede un token JWT valido
def modify_user_account():
    current_user = get_jwt()["username"]  # Ottieni l'utente dal token
    role = get_jwt()["role"]  # Ottieni il ruolo dal token
    jti = get_jwt()["jti"]  # Ottieni il "jti" dal payload del token corrente, serve per eseguire il logout
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')

    if not username or not new_password:
        return make_response(jsonify({"error": 'username and password are required'}), 400)

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)
    
    else:
        #creo il salt e l'hash della nuova password
        salt = os.urandom(16).hex()
        hashed_password = hashlib.sha256((salt + new_password).encode('utf-8')).hexdigest()

        params = {
            "username": username,
            "salt": salt,
            "password": hashed_password
        }

        response = send_request('modify_user', **params)
        revoked_tokens.add(jti)  # Aggiungi il "jti" alla blacklist (revoca il token)
        return make_response(jsonify(response), 200)
    
@app.route('/account_management/delete_user_account/<username>', methods=['DELETE'])
@jwt_required()  # Richiede un token JWT valido
def delete_user_account(username):
    
    if not username:
        return make_response(jsonify({"error": 'username is required'}), 400)
    
    current_user = get_jwt()["username"]  # Ottieni l'utente dal token
    role = get_jwt()["role"]  # Ottieni il ruolo dal token
    jti = get_jwt()["jti"]  # Ottieni il "jti" dal payload del token corrente, serve per eseguire il logout

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)
    else:

        params = {
            "username": username
        }

        response = send_request('remove_user', **params)
        revoked_tokens.add(jti)  # Aggiungi il "jti" alla blacklist (revoca il token)
        return make_response(jsonify(response), 200)

@app.route('/account_management/buy_in_game_currency', methods=['POST'])
@jwt_required()  # Richiede un token JWT valido
def buy_in_game_currency():
    current_user = get_jwt()["username"]  # Ottieni l'utente dal token
    role = get_jwt()["role"]  # Ottieni il ruolo dal token
    data = request.get_json()
    username = data.get('username')
    pack = data.get('pack')

    if not username or pack not in [1, 2, 3]:
        return make_response(jsonify({"error": 'username and pack are required'}), 400)

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)
    else:

        params = {
            "username": username,
            "pack": pack
        }

        response = send_request('increase_user_currency', **params)
        return make_response(jsonify(response), 201)
        
# Used to roll a gacha and make bids
@app.route('/account_management/get_currency', methods=['GET'])
@jwt_required()
def get_currency():

    user_id = get_jwt_identity()

    if not user_id:
        return make_response(jsonify(error= "Forbidden"), 403)
    
    params = {
        "id": user_id
    }
    response = send_request('get_user_currency', **params)
    return make_response(jsonify(response), 200)

# Use after rolled a gacha   
@app.route('/currency', methods=['PATCH'])
@jwt_required()
def set_currency():

    user_id = get_jwt_identity()
    if not user_id:
        return make_response(jsonify(error= "Forbidden"), 403)
    
    data = request.get_json()
    if not data['currency']:
         return make_response(jsonify(error="Bad request"), 400)
    
    params = {
        "id": user_id,
        "currency": data['currency']
    }
    response = send_request('set_user_currency', **params)
    return make_response(jsonify(response), 200)


#ADMIN SERVICES

# Used for admin collection operations
@app.route('/account_management/admin/get_username', methods=['GET'])
@jwt_required()
def get_username():
    jwtPayload = get_jwt()
    role = jwtPayload.get('role', 'unknown')
    data = request.get_json()

    try:
        if role != 'admin':
            return make_response(jsonify(error='Forbidden'), 403)
        
        if not data or ('ids' not in data):
            return make_response(jsonify(error='Data missing'), 400)

        response = requests.get('https://users_db_manager:5000/usernames', json=data, verify=False)
        if response.status_code != 200:
            return make_response(jsonify(response.json()), response.status_code)
        
        return make_response(jsonify(success=response.json()), 200)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify(error=f'Request failed: {str(e)}'), 500)
    except Exception as e:
        return make_response(jsonify(error=f'Internal server error: {str(e)}'), 500)

@app.route('/account_management/admin/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_response(jsonify({"error": 'username and password are required'}), 400)
    
    params = {
            "username": username,
            "password": password
        }

    response = send_request('check_credentials', **params)
    
    access_token = create_access_token(
                identity=str(id),
                additional_claims={
                    "username": username,
                    "role": 'admin'
                }
            )
    return make_response(jsonify({"access_token": access_token, "message" : response.get("message")}), 200)

@app.route('/account_management/admin/view_users', methods=['GET'])
@jwt_required()  # Richiede un token valido
def view_users():

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)


    # Ottieni lo username dalla query string, se presente
    username = request.args.get('username', "all")  # Usa 'default_user' se non c'è
    
    params = {
            "username": username
        }
    response = send_request('get_all_users', **params)
    return make_response(jsonify(response), 200)

@app.route('/account_management/admin/modify_user', methods=['PATCH'])
@jwt_required()  # Richiede un token JWT valido
def modify_user():

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)

    data = request.get_json()
    username = data.get('username')
    new_currency = data.get('new_currency')

    if not username or not new_currency:
        return make_response(jsonify({"error": 'username and new_currency are required'}), 400)
    try:
        new_currency = int(new_currency)  # Prova a convertirlo in intero
    except ValueError:
        return make_response(jsonify({"error": "'new_currency' must be an integer"}), 400)


    params = {
            "username": username,
            "new_currency": new_currency
        }
    response = send_request('modify_user_by_admin', **params)
    return make_response(jsonify(response), 200)
    
@app.route('/account_management/admin/check_payments_history/<username>', methods=['GET'])
@jwt_required()  # Richiede un token valido
def check_payments_history(username):

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return make_response(jsonify({"error": 'Unauthorized'}), 403)

    # Ottieni lo username dalla query string, se presente
    if not username:
        return make_response(jsonify({"error": 'username is required'}), 400)
    
    params = {
            "username": username
        }
    response = send_request('check_payments', **params)
    return make_response(jsonify(response), 200)

if __name__ == '__main__':
    app.run(debug=True)