from flask import Flask, make_response, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from os import getenv
import requests, json

app = Flask(__name__)

def get_secret(secret_path):
        try:
            # Read secret
            with open(secret_path, 'r') as secret_file:
                secret = secret_file.read().strip()  # Remove spaces and newline
            return secret
        except FileNotFoundError:
            raise Exception(f"Secret file not found at {secret_path}")
        except Exception as e:
            raise Exception(f"Error reading secret: {str(e)}")

# Set jwt config
app.config['JWT_SECRET_KEY'] = get_secret('/run/secrets/jwt_password')
app.config['JWT_TOKEN_LOCATION'] = [getenv('JWT_LOCATION')]
jwt = JWTManager(app)

# ! USER ENDPOINTS

# * See user collection
@app.route('/collection', methods=['GET']) 
@jwt_required()
def get_user_collection():
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        # Check role (ATTENTION: admin can't own a collection)
        if role != 'user':
            return make_response(jsonify(error='Access forbidden: only users can own a collection'), 403)
           
        # Retrieve user_id from jwt token 
        user_id = get_jwt_identity()
        
        # Send a request
        response = requests.get(f"https://collection_db_manager:5010/user_collection/{user_id}", verify=False, timeout=5)
        
        # If response is not null, return the body
        if response.status_code == 200:
            return make_response(response.json(), 200)

        return make_response(jsonify(error='Failed to retrieve user collection'), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

# * Retrieve info about an owned gacha of the user
@app.route('/collection/<int:gacha_id>', methods=['GET']) 
@jwt_required()
def see_gacha_info(gacha_id):
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'user':
            return make_response(jsonify(error='Access forbidden: only users can own a collection'), 403)
        
        # Retrieve user_id from jwt token 
        user_id = get_jwt_identity()

        # Check if user owns the requested gacha
        response = requests.get(f"https://collection_db_manager:5010/user_collection/{user_id}", verify=False, timeout=5)
        if response.status_code != 200:
            return make_response(jsonify(error='Failed to retrieve user collection'), response.status_code)
        
        data = response.json()
        ids = [item['gachaId'] for item in data]

        owned = False
        if gacha_id in ids: owned = True
        
        if owned:
            info = requests.get(f'https://collection_db_manager:5010/gacha/{gacha_id}', verify=False, timeout=5)
            if info.status_code == 200:
                return make_response(info.json(), 200)
            else: return make_response(jsonify(error='Failed to retrieve gacha info'), info.status_code)

        return make_response(jsonify(error="Gacha not owned"), 404)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


# ! COMMON ENDPOINTS

# * See the system gacha collection
@app.route('/system_collection', methods=['GET']) 
def get_system_collection():
    try:
        response = requests.get('https://collection_db_manager:5010/gacha', verify=False, timeout=5)
        if response.status_code == 200:
            return make_response(response.json(), 200)
        
        return make_response(jsonify(error='Failed to retrieve system gachas'), 500)
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

# * See the info of a system gacha
@app.route('/system_collection/<int:gacha_id>', methods=['GET']) 
def get_info_about_system_gacha(gacha_id):
    try: 
        response = requests.get(f'https://collection_db_manager:5010/gacha/{gacha_id}', verify=False, timeout=5)
        if response.status_code == 200:
            return make_response(response.json(), 200)
        
        return make_response(jsonify(error='Gacha not found'), 404)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

# ! ADMIN ENDPOINTS

# * Check all collections
@app.route('/admin/collections', methods=['GET'])
@jwt_required()
def check_all_user_collections():
    # Retrieve token and role
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization': auth_headers}

    try:
        if role != 'admin':
            return make_response(jsonify(error='Forbidden'), 403)
        
        # Retrieve all users
        response_users = requests.get('https://collection_db_manager:5010/users', verify=False, timeout=5)
        if response_users.status_code != 200:
            return make_response(jsonify(error='Failed to retrieve users'), response_users.status_code)
        
        # IDs
        users = [item['user'] for item in response_users.json()]
        users_ids = {"ids": users}

        # Retrieve all usernames
        users_response = requests.get('https://account_management:5000/account_management/admin/get_username', json=users_ids, headers=new_header, verify=False, timeout=5)
        if users_response.status_code != 200:
            return make_response(jsonify(users_response.json()), users_response.status_code)

        # Retrieve all gachas for each user
        user_list = []
        for user in users_response.json()['success']:
            # Make a request for each user
            response_gacha = requests.get(f'https://collection_db_manager:5010/user_collection/{user['id']}', verify=False, timeout=5)
            if response_gacha.status_code != 200:
                return make_response(jsonify(error='Failed to retrieve users collection'), response_gacha.status_code)
            
            # Retrieve gachas of the current user 
            user_gachas = response_gacha.json()
            user_data = {
                'user_id': user['id'],
                'username': user['username'],
                'gachas': user_gachas if user_gachas else []
            }
            user_list.append(user_data)

        # Check if data is filled
        if user_list:
            return make_response(jsonify(user_list), 200)
        
        return make_response(jsonify(error='Failed to retrieve gachas'), 500)

    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
    
@app.route('/admin/collections/<int:user_id>', methods=['GET'])
@jwt_required()
def check_specific_user_collection(user_id: int):
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization': auth_headers}

    try:
        if role != 'admin':
            return make_response(jsonify(error='Forbidden'), 403)
        
        if not user_id:
            return make_response(jsonify(error="User ID missing"), 400)
        
        # Check username
        id = {"ids": [user_id]}
        username = requests.get("https://account_management:5000/account_management/admin/get_username", json=id, headers=new_header, verify=False, timeout=5)
        if username.status_code != 200:
            return make_response(jsonify(username.json()), username.status_code)
        
        response = requests.get(f'https://collection_db_manager:5010/user_collection/{user_id}', verify=False, timeout=5)
        if response.status_code == 200:
            return make_response(response.json(), 200)
        
        return make_response(jsonify(error='User not found'), 404)
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

# ! ADDITIONAL FEATURES

# * Retrieve user collection grouped by quantity
@app.route('/collection/grouped', methods=['GET']) 
@jwt_required()
def get_grouped_collection():
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'user':
            return make_response(jsonify(error='Access forbidden: only users can own a collection'), 403)
        
        # Retrieve user_id from jwt token
        user_id = get_jwt_identity()

        response = requests.get(f'https://collection_db_manager:5010/user_collection/{user_id}/grouped', verify=False, timeout=5)
        if response.status_code == 200:
            return make_response(response.json(), 200)
        
        return make_response(jsonify(error='Failed to retrieve collection'), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


if __name__ == '__main__':
    app.run(threaded=True)
