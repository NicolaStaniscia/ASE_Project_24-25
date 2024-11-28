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
        
        # Send data (user_id, gacha_id)
        response = requests.post('https://collection_db_manager:5010/edit/user_collection', json=data, verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['result']), 200)

        return make_response(response.json(), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
# * Add a gacha to a user collection (chiamata dal sistema)
@app.route('/edit/collection', methods=['POST'])
def add_gacha_to_collection_win():
    # Retrieve json from GUI (JS)
    data = request.get_json()

    try:
        if not data or ('user_id' not in data) or ('gacha_id' not in data):
            return make_response(jsonify(error='Bad request'), 400)
        
        # Send data (user_id, gacha_id)
        response = requests.post('https://collection_db_manager:5010/edit/user_collection', json=data, verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['result']), 200)

        return make_response(response.json(), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


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
        
        # data = (id, user_id, gacha_id)
        response = requests.patch('https://collection_db_manager:5010/edit/user_collection', json=data, verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['result']), 200)
        
        return make_response(response.json(), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


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
        
        # data (id)
        response = requests.delete(f'https://collection_db_manager:5010/edit/user_collection/{id_own}', verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['result']), 200)
        
        return make_response(response.json(), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


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

    try:
        if role != 'admin':
            return make_response(jsonify(error='Access denied'), 403)
        
        if not data:
            return make_response(jsonify(error='Bad request'), 400)
        
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict) or not all(field in item for field in required_fields):
                    return make_response(jsonify(error='Bad request'), 400)
                
        elif isinstance(data, dict):
            if not all(field in data for field in required_fields):
                return make_response(jsonify(error='Bad request'), 400)
        
        # data[n] (name, extractionProb, rarity, image, damage, speed, critical, accuracy)
        insert_response = requests.post('https://collection_db_manager:5010/edit_gacha', json=data, verify=False)
        if insert_response.status_code == 200:
            return make_response(jsonify(success=insert_response.json()['result']), 200)
        
        return make_response(insert_response.json(), insert_response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


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
        
        # data (id, name, extractionProb, image, class, damage, speed, critical, accuracy)
        response = requests.patch('https://collection_db_manager:5010/edit_gacha', json=data, verify=False)
        if response.status_code == 200:
            return make_response(jsonify(success=response.json()['result']), 200)
        
        return make_response(response.json(), response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

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
        
        delete_response = requests.delete(f'https://collection_db_manager:5010/edit_gacha/{gacha_id}', verify=False)
        if delete_response.status_code == 200:
            return make_response(jsonify(success=delete_response.json()['result']), 200)
        
        return make_response(delete_response.json(), delete_response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    