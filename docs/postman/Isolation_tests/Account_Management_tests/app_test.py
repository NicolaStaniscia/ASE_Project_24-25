import app as main_app
import random

flask_app = main_app.app

def mock_request(endpoint, **kwargs):

    if endpoint == 'create_user':
        username = kwargs['username']
        return {"message": f"User {username} created successfully"}
    
    elif endpoint == 'check_credentials':
        username = kwargs['username']
        return {"message": f"Login completed successfully for user {username}"}
    
    elif endpoint == 'modify_user':
        username = kwargs['username']
        return {"message": f"User:{username}. Password modified successfully, you need to log in again."}
    
    elif endpoint == 'remove_user':
        username = kwargs['username']
        return {"message": f"User:{username} eliminated successfully."}
    
    elif endpoint == 'increase_user_currency':
        username = kwargs['username']
        pack = kwargs['pack']
        currency = {1: 200, 2: 500, 3: 1000}.get(pack)
        return {"message": f"Transaction successfull. User: {username} successfully purchased {currency} BP."}
    
    elif endpoint == 'get_user_currency':
        id = kwargs['id']
        currency = random.randint(10, 2000)
        return {"message": f"The actual currency of the user with id: {id} is: {currency} BP."}
    
    elif endpoint == 'set_user_currency':
        id = kwargs['id']
        currency = kwargs['currency']
        return {"message": f"Currency updated for the user with id: {id}. New currency: {currency} BP."}
    
    else:
        return {"error": "Invalid operation"}

main_app.mock_request = mock_request