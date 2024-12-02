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
    
    elif endpoint == 'get_all_users':
        username = kwargs['username']
        if username == 'all':
            
            return {
                    "Users Data:":[
                        [1, "user1", "01b616925ff7214e570e88de39c46bf8", "84c07ec649af29be26d28355156ae24e9dff7511bf9ff88feb33972e68264aec", 180, "Sat, 30 Nov 2024 17:27:06 GMT"],
                        [4, "user4", "01b616925ff721fjebfbfhjbfdk46bf8", "84c07ecsdfgsed6f62198466554wq21d6948gthry8e5t546rewg94r8he264aec", 1040, "Sat, 30 Nov 2024 19:51:12 GMT"], 
                        [6, "user6", "0dmfvjfnklnhbfge570e88de39c46bf8", "fs6rdg5f4rfes4d5gr6gt4rer899t4r465et4t843r965g489643972e68264aec", 670, "Sat, 30 Nov 2024 21:11:50 GMT"],
                        [10,"user10","01dfkjne0656ytrgse3213968449889w", "rtrd8ec649af2grdt64dr5fs6g4htrge84fg5£waq78ed54er186r7feg4654rfj", 2150, "Sat, 30 Nov 2024 11:12:20 GMT"]                    
                   ]}
        
        else:

            return {f"{username} Data:": [1, f"{username}", "01b616925ff7214e570e88de39c46bf8", "84c07ec649af29be26d28355156ae24e9dff7511bf9ff88feb33972e68264aec", 450, "Sat, 30 Nov 2024 17:31:42 GMT"]}

    elif endpoint == 'modify_user_by_admin':

        username = kwargs['username']
        new_currency = kwargs['new_currency']
        return {"message": f"User:{username}. Currency modified successfully, new currency : {new_currency}."}
    
    elif endpoint == 'check_payments':
        username = kwargs['username']
        return {f"{username} Payments History:":[
                    [4, 1, 20, 500, "Thu, 28 Nov 2024 17:13:25 GMT"]
                ]
            }
    else:
        return {"error": "Invalid operation"}

main_app.mock_request = mock_request