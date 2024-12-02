import app as main_app
import json

flask_app = main_app.app

# Variables
points = 1000
values = [('Common', 0.5445), ('Rare', 0.4), ('Super Rare', 0.05), ('Ultra Rare', 0.005), ('Super Ultra Rare', 0.0005)]

def mock_request(endpoint: str, **kwargs):
    match endpoint:
    
        case "get_currency":
            return {"points": points}
        
        case 'get_system_gacha':
            array = []
            for i, value in enumerate(values):
                response = {
                    "extractionProb": value[1],
                    "id": i,
                    "image": "path/to/image",
                    "name": f"Example{i}",
                    "rarity": value[0]
                }
                array.append(response)

            return json.dumps(array, indent=4)
        
        case 'currency':
            updated = kwargs['currency']
            if not updated:
                return {"error": "Bad request"} 
            return {"success": "Currency updated"}
        
        case 'add_gacha_to_collection':
            gacha_id = kwargs['gacha_id']
            user_id = kwargs['user_id']
            return {"success": f"Gacha {gacha_id} added to user (id: {user_id}) collection"}
        
        case _:
            return {"error": "Invalid option"}
        

main_app.mock_request = mock_request