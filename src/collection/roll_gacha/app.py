from flask import Flask, request, make_response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, get_jwt_identity
from os import getenv
import random as rnd
import requests

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
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization':auth_headers}

    # Variables for rollback
    updated_currency = 0
    bullet_p = 0
    assigned = False

    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        # Retrieve bullet points
        bullet_response = requests.get('https://account_management:5000/account_management/get_currency', headers=new_header, verify=False, timeout=5)
        if bullet_response.status_code != 200:
            raise requests.exceptions.RequestException('Something gone wrong')
        
        bullet_p = bullet_response.json()['points'][0]
        
        if bullet_p < standard_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)
        
        gacha_response = requests.get('https://collection_db_manager:5010/gacha', verify=False, timeout=5)
        if gacha_response.status_code != 200:
            return make_response(jsonify(error='Request failed'), gacha_response.status_code)
        
        # Retrieve response data
        sys_gacha = gacha_response.json()
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities = [item['rarity'] for item in sys_gacha]
        
        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'standard')

        # Extract a card
        card = rnd.choices(ids, weights=new_probs)[0]
        
        # Create a dict
        assign = dict()
        assign['user_id'] = user_id
        assign['gacha_id'] = card
        
        # Edit currency 
        updated_currency = bullet_p - standard_price
        data_update = {'currency': updated_currency}
        update_resp = requests.patch('https://account_management:5000/currency', json=data_update, headers=new_header, verify=False, timeout=5)
        if update_resp.status_code != 200:
            return make_response(jsonify(update_resp.json()), update_resp.status_code)
        
        # Send assignment request
        assign_response = requests.post('https://collection_db_manager:5010/edit/user_collection', json=assign, verify=False, timeout=5)
        if assign_response.status_code == 200:
            assigned = True
            return make_response(jsonify(success=assign_response.json()['result']), 200)

        return make_response(jsonify(assign_response.json()), assign_response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
    finally:
        rollback = {'currency': bullet_p}
        if updated_currency != 0 and assigned == False:
            requests.patch('https://account_management:5000/currency', json=rollback, headers=new_header, verify=False, timeout=5)
    
    
@app.route('/roll/gold', methods=['POST'])
@jwt_required()
def roll_gold():
    # Retrieve token and info
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    user_id = get_jwt_identity()
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization': auth_headers}

    # Variables for rollback
    updated_currency = 0
    bullet_p = 0
    assigned = False

    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        # Retrieve bullet points
        bullet_response = requests.get('https://account_management:5000/account_management/get_currency', headers=new_header, verify=False, timeout=5)
        if bullet_response.status_code != 200:
            raise requests.exceptions.RequestException('Something gone wrong')
        
        bullet_p = bullet_response.json()['points'][0]
        
        if bullet_p < gold_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)
        
        # Retrieve gachas
        gacha_response = requests.get('https://collection_db_manager:5010/gacha', verify=False, timeout=5)
        if gacha_response.status_code != 200:
            return make_response(jsonify(error=f'Request failed: {gacha_response.json()}'), gacha_response.status_code)
        
        # Retrieve response data and set config
        sys_gacha = gacha_response.json()
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities= [item['rarity'] for item in sys_gacha]

        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'gold')

        # Assign card
        card = rnd.choices(ids, weights=new_probs)[0]
        
        # Create a dict
        assign = dict()
        assign['user_id'] = user_id
        assign['gacha_id'] = card

        # Edit currency 
        updated_currency = bullet_p - gold_price
        data_update = {'currency': updated_currency}
        update_resp = requests.patch('https://account_management:5000/currency', json=data_update, headers=new_header, verify=False, timeout=5)
        if update_resp.status_code != 200:
            return make_response(jsonify(update_resp.json()), update_resp.status_code)
        
        # Send assignment request
        assign_response = requests.post('https://collection_db_manager:5010/edit/user_collection', json=assign, verify=False, timeout=5)
        if assign_response.status_code == 200:
            assigned = True
            return make_response(jsonify(success=assign_response.json()['result']), 200)

        return make_response(jsonify(assign_response.json()), assign_response.status_code)

    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error=f"Internal server error: {str(e)}"), 500)
    
    finally:
        rollback = {'currency': bullet_p}
        if updated_currency != 0 and assigned == False:
            requests.patch('https://account_management:5000/currency', json=rollback, headers=new_header, verify=False, timeout=5)


@app.route('/roll/platinum', methods=['POST'])
@jwt_required()
def roll_platinum():
    # Retrieve token and info
    jwt_payload = get_jwt()
    role = jwt_payload.get('role', 'unknown')
    user_id = get_jwt_identity()
    auth_headers = request.headers.get('Authorization')
    new_header = {'Authorization':auth_headers}
    
    # Variables for rollback
    updated_currency = 0
    bullet_p = 0
    assigned = False

    try:
        if role != 'user':
            return make_response(jsonify(error='Only users can roll a gacha'), 403)
        
        # Retrieve bullet points
        bullet_response = requests.get('https://account_management:5000/account_management/get_currency', headers=new_header, verify=False, timeout=5)
        if bullet_response.status_code != 200:
            raise requests.exceptions.RequestException('Something gone wrong')
        
        bullet_p = bullet_response.json()['points'][0]

        if bullet_p < platinum_price:
            return make_response(jsonify(error='You don\'t have enough points'), 400)

        # Retrieve gachas
        gacha_response = requests.get('https://collection_db_manager:5010/gacha', verify=False, timeout=5)
        if gacha_response.status_code != 200:
            return make_response(jsonify(error='Request failed'), gacha_response.status_code)

         # Retrieve response data and set config
        sys_gacha = gacha_response.json()
        ids = [item['id'] for item in sys_gacha]
        extractionProbs = [item['extractionProb'] for item in sys_gacha]
        rarities= [item['rarity'] for item in sys_gacha]

        # Compute modified probs
        new_probs = compute_probs(extractionProbs, rarities, 'platinum')

        # Assign cards
        card = rnd.choices(ids, weights=new_probs)[0]
        
        # Create a dict
        assign = dict()
        assign['user_id'] = user_id
        assign['gacha_id'] = card

        # Edit currency 
        updated_currency = bullet_p - platinum_price
        data_update = {'currency': updated_currency}
        update_resp = requests.patch('https://account_management:5000/currency', json=data_update, headers=new_header, verify=False, timeout=5)
        if update_resp.status_code != 200:
            return make_response(jsonify(update_resp.json()), update_resp.status_code)
        
        # Send assignment request
        assign_response = requests.post('https://collection_db_manager:5010/edit/user_collection', json=assign, verify=False, timeout=5)
        if assign_response.status_code == 200:
            assigned = True
            return make_response(jsonify(success=assign_response.json()['result']), 200)
        

        return make_response(jsonify(assign_response.json()), assign_response.status_code)

    except requests.exceptions.RequestException as e:
        # Manage request exception
        return make_response(jsonify(error=f"Request failed: {str(e)}"), 500)
    
    except Exception as e:
        return make_response(jsonify(error="Internal server error"), 500)
    
    finally:
        rollback = {'currency': bullet_p}
        if updated_currency != 0 and assigned == False:
            requests.patch('https://account_management:5000/currency', json=rollback, headers=new_header, verify=False, timeout=5)


if __name__ == '__main__':
    app.run(threaded=True)
    