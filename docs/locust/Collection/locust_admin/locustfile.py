from locust import HttpUser, task, between, events
import jwt, random as rnd, datetime
from os import getenv

host = 'https://localhost:8081'

class Admin(HttpUser):
    wait_time = between(1, 3)
    jwt_secret = "JwtGACHA2425"  # Chiave segreta per firmare il token
    jwt_algorithm = "HS256"  # Algoritmo di firma
    jwt_token = None  # Token JWT generato
    token_expiry = 0  # Timestamp di scadenza del token

    def generate_jwt_token(self):
        """
        Genera un token JWT firmato localmente.
        """
        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(minutes=60)
        user_id = 1
        payload = {
            "sub": str(user_id),
            "iat": int(current_time.timestamp()),  # Issued at
            "exp": int(expiry_time.timestamp()),  # Expiry time
            "role": "admin" ,
            "username": "admin1"
        }
        # Firma il token con la chiave segreta e l'algoritmo scelto
        self.jwt_token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        self.token_expiry = expiry_time.timestamp()

    def get_headers(self):
        """
        Restituisce gli header con il token JWT incluso.
        """
        current_time = datetime.datetime.now().timestamp()
        if not self.jwt_token or current_time >= self.token_expiry:
            self.generate_jwt_token()  # Genera un nuovo token se è scaduto
        return {
            "Authorization": f"Bearer {self.jwt_token}"
        }

    def on_start(self):
        """Metodo eseguito all'inizio di ogni utente per inizializzare lo stato."""
        self.generate_jwt_token()  # Genera i token all'inizio di ogni utente

    def report_failure(self, request_type: str, endpoint: str, exception: Exception,response_time=0, response_length=0):
        events.request.fire(
            request_type=request_type,
            name=endpoint,
            response_time=response_time,
            response_length=response_length,
            exception=exception
        )
    
    @task(2)
    def see_users_collection(self):
        headers = self.get_headers()

        try:
            with self.client.get(f'{host}/admin/collections', headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")
        except Exception as e:
            self.report_failure('GET', '/system_collection', e)
    
    @task(2)
    def see_specific_user_colleciton(self):
        headers = self.get_headers()
        n_users = 20
        try:
            for n in range(1, n_users + 1):
                with self.client.get(f'{host}/admin/collections/{n}', headers=headers, catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")
        
        except Exception as e:
            self.report_failure('GET', f'/admin/collections/<id>', e)

    @task(1)
    def get_system_collection(self):
        try:
            with self.client.get(f'{host}/system_collection', catch_response=True) as response:
                if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/system_collection', e)
    
    @task(2)
    def get_specific_system_gacha(self):
        gacha_id = [x for x in range(1, 37)]

        try:
            for gacha in gacha_id:
                with self.client.get(f'{host}/system_collection/{gacha}', catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', f'/system_collection/{gacha}', e)

    @task(3)
    def add_gacha_to_collection(self):
        headers = self.get_headers()
        body = {
            "user_id": rnd.randint(1, 30),
            "gacha_id": rnd.randint(1, 36) 
        }
        
        try:
            with self.client.post(f'{host}/admin/edit/collection', json=body, headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('POST', '/admin/edit/collection', e)

    @task(3)
    def edit_gacha_of_collection(self):
        headers = self.get_headers()
        body = {
            "id": rnd.randint(1, 30),
            "user_id": rnd.randint(1, 30),
            "gacha_id": rnd.randint(1, 36),
            "in_auction": rnd.randint(0, 1)
        }
        
        try:
            with self.client.patch(f'{host}/admin/edit/collection', json=body, headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"PATCH request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('PATCH', '/admin/edit/collection', e)
    
    @task(3)
    def delete_gacha_of_collection(self):
        headers = self.get_headers()
        id_own = rnd.randint(100, 200)
        
        try:
            with self.client.delete(f'{host}/admin/edit/collection/{id_own}', headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"DELETE request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('DELETE', '/admin/edit/collection', e)

    @task(3)
    def add_system_gacha(self):
        headers = self.get_headers()
        body = {
            "name": f"try{rnd.randint(0, 100)}", 
            "extractionProb": 0.4, 
            "rarity": "Rare", 
            "image": "path/to/image", 
            "damage": 68, 
            "speed": 64, 
            "critical": 0.1, 
            "accuracy": 74
        }
        
        try:
            with self.client.post(f'{host}/admin/edit/gacha', json=body, headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('POST', '/admin/edit/gacha', e)
    
    @task(3)
    def edit_system_gacha(self):
        headers = self.get_headers()
        body = {
            "id": rnd.randint(39, 47),  # Actually these are for test (check the existence of these gacha)
            "damage": rnd.randint(50, 70),
            "accuracy": rnd.randint(70, 80),
            "critical": rnd.random()
        }
        
        try:
            with self.client.patch(f'{host}/admin/edit/gacha', json=body, headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"PATCH request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('PATCH', '/admin/edit/gacha', e)

    @task(1)
    def delete_system_gacha(self):

        headers = self.get_headers()
        gacha_id = rnd.randint(39, 200) 
        
        try:
            with self.client.delete(f'{host}/admin/edit/gacha/{gacha_id}', headers=headers, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"DELETE request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('DELETE', '/admin/edit/gacha', e)
