import app as main_app
import random as rnd
import json

flask_app = main_app.app

allowed_rarity_levels = ['Common', 'Rare', 'Super Rare', 'Ultra Rare', 'Super Ultra Rare']

def mock_request(endpoint, **kwargs):
    if endpoint == 'get_user_collection':
        n = kwargs['n']
        array = []
        for i in range(1, n + 1):
            index = rnd.randint(0, len(allowed_rarity_levels) - 1)
            response = {
                "gachaId": i,
                "idOwn": rnd.randint(0, 31),
                "image": "path/to/image",
                "name": f"Example{i}",
                "rarity": allowed_rarity_levels[index]
            }
            array.append(response)

        return json.dumps(array, indent=4)
    
    elif endpoint == 'see_gacha_info':
        gacha_id = kwargs['gacha_id']
        index = rnd.randint(0, len(allowed_rarity_levels) - 1)
        return {
            "accuracy": rnd.randint(50, 100),
            "critical": rnd.random(),
            "damage": rnd.randint(50, 100),
            "extractionProb": rnd.random(),
            "id": gacha_id,
            "image": "path/to/image",
            "name": f"Gacha_{gacha_id}",
            "rarity": allowed_rarity_levels[index],
            "speed": rnd.randint(30, 100)
        }
    
    elif endpoint == 'get_system_gacha':
        n = kwargs['n']
        index = rnd.randint(0, len(allowed_rarity_levels) - 1)
        array = []
        for i in range(1, n + 1):
            response = {
                "extractionProb": rnd.random(),
                "id": i,
                "image": "path/to/image",
                "name": f"Example{i}",
                "rarity": allowed_rarity_levels[index]
            }
            array.append(response)

        return json.dumps(array, indent=4)
    
    elif endpoint == 'get_all_owners':
        n = kwargs['n']
        users = []
        for i in range(0, n):
            users.append({"user": i})
        
        return json.dumps(users)
    
    elif endpoint == 'get_username':
        users = kwargs['ids']
        jsonUsers = json.loads(users)
        usernames = []

        for item in jsonUsers:
            usernames.append({"id": item['user'], "username": f"user{item['user']}"})
        
        return json.dumps(usernames)
    
    elif endpoint == 'get_grouped_collection':
        n = kwargs['n']
        array = []
        for i in range(1, n + 1):
            index = rnd.randint(0, len(allowed_rarity_levels) - 1)
            response = {
                "id": rnd.randint(1, 31),
                "image": "path/to/image",
                "name": f"Example{i}",
                "quantity": rnd.randint(1, 4),
                "rarity": allowed_rarity_levels[index]
            }
            array.append(response)

        return json.dumps(array, indent=4)
    
    else:
        return {"error": "Invalid option"}
    

main_app.mock_request = mock_request