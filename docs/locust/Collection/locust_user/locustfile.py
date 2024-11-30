from locust import HttpUser, task, between, events
import jwt, random as rnd, datetime
from os import getenv

user_host = 'http://user_gateway'

class User(HttpUser):
    wait_time = between(1, 3)
    jwt_secret = getenv('JWT_PASSWORD')  # Chiave segreta per firmare il token
    jwt_algorithm = "HS256"  # Algoritmo di firma
    jwt_token = None  # Token JWT generato
    token_expiry = 0  # Timestamp di scadenza del token

    def generate_jwt_token(self):
        """
        Genera un token JWT firmato localmente.
        """
        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(minutes=60)
        user_id = rnd.randint(1, 100)
        payload = {
            "sub": str(user_id),
            "iat": int(current_time.timestamp()),  # Issued at
            "exp": int(expiry_time.timestamp()),  # Expiry time
            "role": "user" 
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
    def get_collection(self):
        # Get headers
        headers = self.get_headers()

        try: 
            with self.client.get(f'{user_host}/collection', headers=headers, timeout=5, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/collection', e)

    @task(2)
    def get_collection_grouped(self):
        headers = self.get_headers()

        try:
            with self.client.get(f'{user_host}/collection/grouped', headers=headers, timeout=5, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/collection/grouped', e)

    @task(1)
    def see_owned_gacha(self):
        headers = self.get_headers()

        try:
            with self.client.get(f'{user_host}/collection', headers=headers, timeout=5, catch_response=True) as collection:

                gacha_ids = []
                if collection.status_code == 200:
                    data_list = collection.json()  # Tenta di deserializzare il JSON
                    for data in data_list:
                        gacha_ids.append(data.get('gachaId'))  # Usa `.get` per evitare KeyError

                    for gacha in gacha_ids:
                        with self.client.get(f'{user_host}/collection/{gacha}', headers=headers, timeout=5, catch_response=True) as response:
                            if response.status_code != 200:
                                response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', f'/collection/{gacha}', e)
        
        
    
    @task(3)
    def get_system_collection(self):
        try:
            with self.client.get(f'{user_host}/system_collection', timeout=5, catch_response=True) as response:
                if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/system_collection', e)
    
    @task(3)
    def get_specific_system_gacha(self):
        gacha_id = [x for x in range(1, 37)]

        try:
            for gacha in gacha_id:
                with self.client.get(f'{user_host}/system_collection/{gacha}', timeout=10, catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', f'/system_collection/{gacha}', e)
    
    @task(2)
    def roll_standard(self):
        headers = self.get_headers()

        try:
            with self.client.post(f'{user_host}/roll/standard', headers=headers, timeout=10, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('POST', '/roll/standard', e)
    
    @task(3)
    def roll_gold(self):
        headers = self.get_headers()

        try:
            with self.client.post(f'{user_host}/roll/gold', headers=headers, timeout=10, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('POST', '/roll/gold', e)
    
    @task(1)
    def roll_platinum(self):
        headers = self.get_headers()

        try:
            with self.client.post(f'{user_host}/roll/platinum', headers=headers, timeout=10, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('POST', '/roll/platinum', e)

