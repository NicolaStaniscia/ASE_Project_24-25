import app as main_app

flask_app = main_app.app

def mock_request(endpoint, **kwargs):
    if endpoint == 'add_gacha_to_collection':
        gacha_id = kwargs['gacha_id']
        user_id = kwargs['user_id']
        return {"success": f"Gacha {gacha_id} added to user (id: {user_id}) collection"}
    
    elif endpoint == 'edit_gacha_to_collection':
        id = kwargs['id']
        user_id = kwargs.get('user_id', None)
        gacha_id = kwargs.get('gacha_id', None)
        return {"success": f"Row n. {id} updated"}
    
    elif endpoint == 'delete_gacha_from_collection':
        id = kwargs['id']
        return {"success": f"Row (id: {id}) deleted"}
    
    elif endpoint == 'add_system_gacha':
        n_gachas = kwargs['n']
        return {"success": f"Added {n_gachas} new gachas"}
    
    elif endpoint == 'edit_system_gacha':
        id = kwargs['id']
        return {'success': f"Gacha (id: {id}) updated"}
    
    elif endpoint == 'delete_system_gacha':
        id = kwargs['id']
        return {'success': f"Gacha (id: {id}) deleted from the system"}
    
    else:
        return {"error": "Invalid option"}

main_app.mock_request = mock_request