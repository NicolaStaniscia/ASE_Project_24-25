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
                return jsonify({"error": "username and password are required"}), 400

    # a questo punto si genera il salt casuale e l'hash della password
    salt = os.urandom(16).hex()
    hashed_password = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    db_manager_url = "https://users_db_manager:5000/create_user"  # URL del servizio DB Manager
    try:
        # Inoltrare i dati al DB Manager
        response = requests.post(db_manager_url, json={
            "username": username,
            "salt": salt,
            "password": hashed_password},
            verify=False
        )
        
        # Restituire la risposta del DB Manager
        return jsonify({
            "status": response.json(),
            }), response.status_code
    
    except requests.exceptions.RequestException as e:

        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

@app.route('/account_management/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = "normal"

    if not username or not password:
                return jsonify({"error": "username and password are required"}), 400

    #inoltro le credenziali al db_manager per verificare se sono corrette:
    db_manager_url = "https://users_db_manager:5000/check_credentials"
    try:

        response = requests.post(db_manager_url, json={
                "username": username,
                "password": password,
                "user_type": user_type},
                verify=False
            )
        
        if response.status_code == 200:#credentials ok
            url = f"https://db_manager:5000/get_id/{username}/{user_type}"
            response = requests.get(url,verify=False)
            id = data.get('id')
            access_token = create_access_token(
                identity=str(id),
                additional_claims={
                    "username": username,
                    "role": 'user'
                }
            )
            return jsonify({"access_token": access_token, "status": "Login completed successfully"}), 200
        
        elif response.status_code == 401:#invalid credentials
            return jsonify({"error": "Invalid credentials"}), 401
        else:
            return jsonify({"error": "Database Error"}), 500
        

    except requests.exceptions.RequestException as e:

        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

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
        return jsonify({"error": f"{username} isn't logged in."}), 401

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
                return jsonify({"error": "username and new_password are required"}), 400

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return jsonify({"error": "Unauthorized"}), 403
    else:
        db_manager_url = "https://users_db_manager:5000/modify_user"  # URL del servizio DB Manager
        #creo il salt e l'hash della nuova password
        salt = os.urandom(16).hex()
        hashed_password = hashlib.sha256((salt + new_password).encode('utf-8')).hexdigest()
        try:
            # Inoltrare i dati al DB Manager
            response = requests.patch(db_manager_url, json={
                "username": username,
                "salt": salt,
                "password": hashed_password},
                verify=False
            )
            
            # Restituire la risposta del DB Manager, se la password dell'utente è stato modificato con successo ,allora eseguo anche il logout
            if response.status_code == 200:
                revoked_tokens.add(jti)  # Aggiungi il "jti" alla blacklist (revoca il token)
            return jsonify({
                "status": response.json(),
                }), response.status_code
    
        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500
    
@app.route('/account_management/delete_user_account/<username>', methods=['DELETE'])
@jwt_required()  # Richiede un token JWT valido
def delete_user_account(username):
    
    if not username:
        return jsonify({"error": "username is required"}), 400
    
    current_user = get_jwt()["username"]  # Ottieni l'utente dal token
    role = get_jwt()["role"]  # Ottieni il ruolo dal token
    jti = get_jwt()["jti"]  # Ottieni il "jti" dal payload del token corrente, serve per eseguire il logout

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return jsonify({"error": "Unauthorized"}), 403
    else:

        db_manager_url = f"https://users_db_manager:5000/remove_user/{username}"  # URL del servizio DB Manager
        
        try:
            # Inoltrare i dati al DB Manager
            response = requests.delete(db_manager_url, verify=False)
            
            # Restituire la risposta del DB Manager, se l'utente è stato eliminato con successo, allora eseguo anche il logout
            if response.status_code == 200:
                revoked_tokens.add(jti)  # Aggiungi il "jti" alla blacklist (revoca il token)
            return jsonify({
                "status": response.json(),
                }), response.status_code
    
        except requests.exceptions.RequestException as e:

            return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

@app.route('/account_management/buy_in_game_currency', methods=['POST'])
@jwt_required()  # Richiede un token JWT valido
def buy_in_game_currency():
    current_user = get_jwt()["username"]  # Ottieni l'utente dal token
    role = get_jwt()["role"]  # Ottieni il ruolo dal token
    data = request.get_json()
    username = data.get('username')
    pack = data.get('pack')

    if not username or pack not in [1, 2, 3]:
                    return jsonify({"error": "username and pack are required"}), 400

    # Controlla che l'utente stia modificando il proprio account
    if username != current_user or role != 'user':
        return jsonify({"error": "Unauthorized"}), 403
    else:
        db_manager_url = "https://users_db_manager:5000/increase_user_currency"  # URL del servizio DB Manager
        try:
            # Inoltrare i dati al DB Manager
            response = requests.post(db_manager_url, json={
                "username": username,
                "pack": pack},
                verify=False
            )
            
            # Restituire la risposta del DB Manager
            return jsonify({
                "status": response.json(),
                }), response.status_code
    
        except requests.exceptions.RequestException as e:

            return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500
        
# Used to roll a gacha and make bids
@app.route('/account_management/get_currency', methods=['GET'])
@jwt_required()
def get_currency():

    user_id = get_jwt_identity()
    try:
        if not user_id:
            return make_response(jsonify(error="Forbidden"), 403)

        response = requests.get(f'https://users_db_manager:5000/get_user_currency/{user_id}', verify=False)
        if response.status_code == 200:
            return make_response(jsonify(points=response.json()), 200)

        return make_response(jsonify(response.json()), response.status_code)
     
    except requests.exceptions.RequestException as e:
        return make_response(jsonify(error='Request failed'), 500)
    except Exception as e:
        return make_response(jsonify(error='Internal server error'), 500)

# Use after rolled a gacha   
@app.route('/account_management/currency', methods=['PATCH'])
@jwt_required()
def set_currency():
    user_id = get_jwt_identity()
    if not user_id:
        return make_response(jsonify(error="Forbidden"), 403)
    data = request.get_json()
    if not data['currency']:
         return make_response(jsonify(error="Bad request"), 400)
    
    new_data = {'user_id': int(user_id), 'currency': data['currency']}

    try:
        # data (user_id, currency)
        response = requests.patch(f'https://users_db_manager:5000/edit/currency', json=new_data, verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['message']), 200)

        return make_response(jsonify(response.json()), response.status_code)
     
    except requests.exceptions.RequestException as e:
        return make_response(jsonify(error='Request failed'), 500)
    except Exception as e:
        return make_response(jsonify(error='Internal server error'), 500)

#ADMIN SERVICES

# Used for admin collection operations
@app.route('/account_management/get_username', methods=['GET'])
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
    user_type = "admin"

    if not username or not password:
                return jsonify({"error": "username and password are required"}), 400

    #inoltro le credenziali al db_manager per verificare se sono corrette:
    db_manager_url = "https://users_db_manager:5000/check_credentials"
    try:

        response = requests.post(db_manager_url, json={
                "username": username,
                "password": password,
                "user_type": user_type},
                verify=False
            )
        
        if response.status_code == 200:#credentials ok
            url = f"https://db_manager:5000/get_id/{username}/{user_type}"
            response = requests.get(url,verify=False)
            id = data.get('id')
            access_token = create_access_token(
                identity=str(id),
                additional_claims={
                    "username": username,
                    "role": 'admin'
                }
            )
            return jsonify({"access_token": access_token, "status": "Login completed successfully"}), 200
        
        elif response.status_code == 401:#invalid credentials
            return jsonify({"error": "Invalid credentials"}), 401
        else:
            return jsonify({"error": "Database Error"}), 500
        

    except requests.exceptions.RequestException as e:

        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

@app.route('/account_management/admin/view_users', methods=['GET'])
@jwt_required()  # Richiede un token valido
def view_users():

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403


    # Ottieni lo username dalla query string, se presente
    username = request.args.get('username', "all")  # Usa 'default_user' se non c'è
    db_manager_url = f"https://users_db_manager:5000/get_all_users/{username}"  # URL del servizio DB Manager
    try:
        # Inoltrare i dati al DB Manager
        response = requests.get(db_manager_url,verify=False)

        return jsonify({
            "status": response.json(),
            }), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

@app.route('/account_management/admin/modify_user', methods=['PATCH'])
@jwt_required()  # Richiede un token JWT valido
def modify_user():

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    username = data.get('username')
    new_currency = data.get('new_currency')

    if not username or not new_currency:
        return jsonify({"error": "username and new_currency are required"}), 400
    try:
        new_currency = int(new_currency)  # Prova a convertirlo in intero
    except ValueError:
        return jsonify({"error": "'new_currency' must be an integer"}), 400

    db_manager_url = "https://users_db_manager:5000/modify_user_by_admin"  # URL del servizio DB Manager
    try:
        # Inoltrare i dati al DB Manager
        response = requests.patch(db_manager_url, json={
            "username": username,
            "new_currency": new_currency},
            verify=False
        )
        
        # Restituire la risposta del DB Manager, se la password dell'utente è stato modificato con successo ,allora eseguo anche il logout
        if response.status_code == 200:
            return jsonify({
                "status": response.json(),
                }), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500
    
@app.route('/account_management/admin/check_payments_history/<username>', methods=['GET'])
@jwt_required()  # Richiede un token valido
def check_payments_history(username):

    role = get_jwt()["role"]  # Ottieni l'utente dal token
    # Controlla che l'utente stia modificando il proprio account
    if role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    # Ottieni lo username dalla query string, se presente
    if not username:
        return jsonify({"error": "Username is required"}), 400
    db_manager_url = f"https://users_db_manager:5000/check_payments/{username}"  # URL del servizio DB Manager
    try:
        # Inoltrare i dati al DB Manager
        response = requests.get(db_manager_url,verify=False)

        return jsonify({
            "status": response.json(),
            }), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to DB Manager", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)