from flask import Flask, make_response, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from os import getenv
import requests

app = Flask(__name__)

# Set jwt config
app.config['JWT_SECRET_KEY'] = getenv('JWT_PASSWORD')
app.config['JWT_TOKEN_LOCATION'] = [getenv('JWT_LOCATION')]
jwt = JWTManager(app)

# ! MICROSERVICE ONLY FOR ADMINS

# * Add a gacha to a user collection
@app.route('/admin/edit/collection', methods=['POST'])
@jwt_required()
def add_gacha_to_collection():
    # Retrieve json from GUI (JS)
    data = request.get_json()
    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not data or ('user_id' not in data) or ('gacha_id' not in data):
            return make_response(jsonify(error='Bad request'), 400)
            
        # ! TEST DATA
        params = {
            "user_id": data['user_id'],
            "gacha_id": data['gacha_id']
        }

        # Send data (user_id, gacha_id)
        response = send_request('add_gacha_to_collection', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)


# * Edit a gacha of a user collection
@app.route('/admin/edit/collection', methods=['PATCH'])
@jwt_required()
def edit_gacha_of_collection():
    # Retrive json file from front end
    data = request.get_json()
    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    fields = ['user_id', 'gacha_id']

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not data or ('id' not in data) or not any(field in data for field in fields):
            return make_response(jsonify(error='Bad request'), 400)
        
        # ! TEST DATA
        params = {
            "id": data['id'],
            "user_id": data['user_id'],
            "gacha_id": data['gacha_id']
        }
        
        # data = (id, user_id, gacha_id)
        response = send_request('edit_gacha_to_collection', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)


# * Remove a gacha from a user collection
@app.route('/admin/edit/collection/<int:id_own>', methods=['DELETE'])
@jwt_required()
def remove_gacha_from_collection(id_own):
    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not id_own:
            return make_response(jsonify(error='Bad request'), 400)
        
        # ! TEST DATA
        params = {"id": id_own}
        response = send_request('delete_gacha_from_collection', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)


# * Add gachas (accept json array and json object)
@app.route('/admin/edit/gacha', methods=['POST'])
@jwt_required()
def edit_system_gacha():
    # Retrieve json array
    data = request.get_json()
    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    required_fields = ['name', 'extractionProb', 'rarity', 'image', 'damage', 'speed', 'critical', 'accuracy']
    n = 0

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not data:
            return make_response(jsonify(error='Bad request'), 400)
        
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict) or not all(field in item for field in required_fields):
                    return make_response(jsonify(error='Bad request'), 400)
                n += 1
                
        elif isinstance(data, dict):
            if not all(field in data for field in required_fields):
                return make_response(jsonify(error='Bad request'), 400)
            n = 1

        params = {"n": n}
        response = send_request('add_system_gacha', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)


# * Edit a specific gacha info
@app.route('/admin/edit/gacha', methods=['PATCH'])
@jwt_required()
def edit_gacha_info():
    # Retrieve data from front end
    data = request.get_json()
    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    required_fields = ['name', 'extractionProb', 'rarity', 'image', 'damage', 'speed', 'critical', 'accuracy']

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not data or ('id' not in data) or not any(field in data for field in required_fields):
            return make_response(jsonify(error='Bad request'), 400)
        
        # ! TEST DATA
        params = {
            "id": data['id']
        }
        response = send_request('edit_system_gacha', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)
    

# * Delete a system gacha
@app.route('/admin/edit/gacha/<int:gacha_id>', methods=['DELETE'])
@jwt_required()
def delete_system_gacha(gacha_id):

    # Retrieve role of user
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not gacha_id:
            return make_response(jsonify(error='Gacha ID missing'), 400)
        
        params = {"id": gacha_id}
        
        response = send_request('delete_system_gacha', **params)
        return make_response(jsonify(response), 200)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)

mock_request = None
def send_request(endpoint: str, **kwargs):
    if mock_request:
        response = mock_request(endpoint, **kwargs)
        if not isinstance(response, dict):
            raise ValueError("Invalid response format")
        return response
    
    else:
        raise NotImplementedError('mock_request not implemented')
    
if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    