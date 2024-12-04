from flask import Flask, request, make_response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, get_jwt_identity
from os import getenv
import random as rnd, json

app = Flask(__name__)

# Set jwt config
app.config['JWT_SECRET_KEY'] = getenv('JWT_PASSWORD')
app.config['JWT_TOKEN_LOCATION'] = [getenv('JWT_LOCATION')]
jwt = JWTManager(app)

# ! THIS MICROSERVICE IS ONLY USED BY USERS

# * PRICES
standard_price = 100
gold_price = 250
platinum_price = 600

# * MULTIPLIERS
package_modifiers = {
    "standard": {
        "Common": 1.0,
        "Rare": 0.5,
        "Super Rare": 0.4,
        "Ultra Rare": 0.25,
        "Super Ultra Rare": 0.1
    },
    "gold": {
        "Common": 0.15,
        "Rare": 1.5,
        "Super Rare": 3.0,
        "Ultra Rare": 6.0, 
        "Super Ultra Rare": 5.0 
    },
    "platinum": {
        "Common": 0.0,
        "Rare": 0.5,
        "Super Rare": 3.7,
        "Ultra Rare": 11.0,
        "Super Ultra Rare": 13.0
    }
}

# ! USED FOR TEST (select for distinct rarity each new prob)
def print_probs(probs: list, rarities: list):
    res = dict()
    unique_rar = set(zip(rarities, probs))
    for rarity, prob in unique_rar:
        res[rarity] = prob

    return res

# Compute new probabilities
def compute_probs(probs: list, rarities: list, package_type: str, scale=2):
    new_probs = []

    for prob, rarity in zip(probs, rarities):
        modified_prob = prob * (package_modifiers[package_type][rarity] ** scale)
        new_probs.append(modified_prob)

    total_weight = sum(new_probs)
    if total_weight == 0:
        raise ValueError("Total weight is 0")
    
    normalized_probs = [(prob / total_weight) for prob in new_probs]

    return normalized_probs


@app.route('/roll/standard', methods=['POST'])
@jwt_required()
def roll_standard():
    # Retrieve token and info
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    user_id = get_jwt_identity()    
 
    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        user_id = get_jwt_identity()
        
        # Retrieve bullet points
        bullet_response = send_request('get_currency')
        
        bullet_p = bullet_response['points']
        
        if bullet_p < standard_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)
        
        gacha_response = send_request('get_system_gacha')
        
        # Retrieve response data
        sys_gacha = json.loads(gacha_response)
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities = [item['rarity'] for item in sys_gacha]
        
        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'standard')

        # Extract a card
        card = rnd.choices(ids, weights=new_probs)[0]
        
        # Edit currency 
        new_balance = bullet_p - standard_price
        data_update = {'currency': new_balance}
        update_resp = send_request('currency', **data_update)
        if 'success' not in update_resp:
            return make_response(jsonify(error=update_resp['error']), 400)
        
        # Send assignment request
        assign = {
            "user_id": user_id,
            "gacha_id": card
        }
        assign_response = send_request('add_gacha_to_collection', **assign)
        if 'success' in assign_response:
            return make_response(jsonify(assign_response), 200)

        return make_response(jsonify(error="Invalid parameters"), 400)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
    
@app.route('/roll/gold', methods=['POST'])
@jwt_required()
def roll_gold():
    # Retrieve token and info
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    user_id = get_jwt_identity()

    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        # Retrieve bullet points
        user_id = get_jwt_identity()
        
        # Retrieve bullet points
        bullet_response = send_request('get_currency')
        
        bullet_p = bullet_response['points']
        
        if bullet_p < gold_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)
        
        # Retrieve gachas
        gacha_response = send_request('get_system_gacha')
        
        # Retrieve response data
        sys_gacha = json.loads(gacha_response)
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities= [item['rarity'] for item in sys_gacha]

        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'gold')

        # Extract card
        card = rnd.choices(ids, weights=new_probs)[0]
        
       # Edit currency 
        new_balance = bullet_p - gold_price
        data_update = {'currency': new_balance}
        update_resp = send_request('currency', **data_update)
        if 'success' not in update_resp:
            return make_response(jsonify(error=update_resp['error']), 400)
        
        # Send assignment request
        assign = {
            "user_id": user_id,
            "gacha_id": card
        }
        assign_response = send_request('add_gacha_to_collection', **assign)
        if 'success' in assign_response:
            return make_response(jsonify(assign_response), 200)

        return make_response(jsonify(error="Invalid parameters"), 400)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)


@app.route('/roll/platinum', methods=['POST'])
@jwt_required()
def roll_platinum():
    # Retrieve token and info
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    user_id = get_jwt_identity()

    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        # Retrieve bullet points
        user_id = get_jwt_identity()
        
        # Retrieve bullet points
        bullet_response = send_request('get_currency')
        
        bullet_p = bullet_response['points']

        if bullet_p < platinum_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)

        # Retrieve gachas
        gacha_response = send_request('get_system_gacha')
        
        # Retrieve response data
        sys_gacha = json.loads(gacha_response)
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities= [item['rarity'] for item in sys_gacha]

        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'platinum')

        # Assign cards
        card = rnd.choices(ids, weights=new_probs)[0]
        
        # Edit currency 
        new_balance = bullet_p - gold_price
        data_update = {'currency': new_balance}
        update_resp = send_request('currency', **data_update)
        if 'success' not in update_resp:
            return make_response(jsonify(error=update_resp['error']), 400)
        
        # Send assignment request
        assign = {
            "user_id": user_id,
            "gacha_id": card
        }
        assign_response = send_request('add_gacha_to_collection', **assign)
        if 'success' in assign_response:
            return make_response(jsonify(assign_response), 200)

        return make_response(jsonify(error="Invalid parameters"), 400)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    

mock_request = None
def send_request(endpoint: str, **kwargs):
    if mock_request:
        response = mock_request(endpoint, **kwargs)
        return response
    
    else:
        raise NotImplementedError('mock_request not implemented')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    