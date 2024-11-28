from flask import Flask, make_response, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from os import getenv
import json, random as rnd

app = Flask(__name__)

# Set jwt config
app.config['JWT_SECRET_KEY'] = getenv('JWT_PASSWORD')
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
        
        # ! TEST DATA
        params = {"n": rnd.randint(2, 6)}

        # Send a request
        response = send_request('get_user_collection', **params)
        jsonResponse = json.loads(response)
        
        return make_response(jsonify(jsonResponse), 200)
    
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
        
        if not gacha_id:
            return make_response(jsonify(error='User not set'), 400)
        
        # ! TEST DATA 1
        collection_params = {"n": 5} 
        response = send_request('get_user_collection', **collection_params)
        jsonCollection = json.loads(response)
        
        ids = [item['gachaId'] for item in jsonCollection]

        owned = False
        if gacha_id in ids: owned = True
        
        if owned:
            # ! TEST DATA 2
            params = {"gacha_id": gacha_id}
            info = send_request('see_gacha_info', **params)
            return make_response(jsonify(info), 200)

        return make_response(jsonify(error="Gacha not owned"), 404)

    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


# ! COMMON ENDPOINTS

# * See the system gacha collection
@app.route('/system_collection', methods=['GET'])  
def get_system_collection():
    try:
        # ! TEST DATA
        params = {"n": 10}
        response = send_request('get_system_gacha', **params)
        json_response = json.loads(response)

        return make_response(jsonify(json_response), 200)

    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

# * See the info of a system gacha
@app.route('/system_collection/<int:gacha_id>', methods=['GET'])  
def get_info_about_system_gacha(gacha_id):
    try: 
        # ! TEST DATA
        params = {"gacha_id": gacha_id}
        response = send_request('see_gacha_info', **params)

        return make_response(jsonify(response), 200)

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

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 401)
        
        # ! TEST DATA 1
        owners_params = {"n": rnd.randint(1, 4)}

        # Retrieve all users
        response_users = send_request('get_all_owners', **owners_params)
        
        # IDs
        users_ids = {"ids": response_users}

        # Retrieve all usernames
        username_response = send_request('get_username', **users_ids)

        # Retrieve all gachas for each user
        user_list = []
        for user in json.loads(username_response):
            # ! TEST DATA 2
            collection_params = {"n": rnd.randint(2, 5)}
            
            # Make a request for each user
            response_gacha = send_request('get_user_collection', **collection_params)
            
            # Retrieve gachas of the current user 
            user_gachas = json.loads(response_gacha)
            user_data = {
                'user_id': user['id'],
                'username': user['username'],
                'gachas': user_gachas
            }
            user_list.append(user_data)

        # Check if data is filled
        if user_list:
            return make_response(jsonify(user_list), 200)
        
        return make_response(jsonify(error='Failed to retrieve gachas'), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
    
@app.route('/admin/collections/<int:user_id>', methods=['GET'])
@jwt_required()
def check_specific_user_collection(user_id: int):
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 401)
        
        # ! TEST DATA
        params = {"n": rnd.randint(2, 5)}
        response = send_request('get_user_collection', **params)
        jsonResponse = json.loads(response)

        return make_response(jsonify(jsonResponse), 200)
    
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

        params = {"n": 3}
        response = send_request('get_grouped_collection', **params)
        jsonResponse = json.loads(response)
        
        return make_response(jsonify(jsonResponse), 200)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


mock_request = None
def send_request(endpoint: str, **kwargs):
    if mock_request:
        return mock_request(endpoint, **kwargs)    
    else:
        raise NotImplementedError('mock_request not implemented')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
