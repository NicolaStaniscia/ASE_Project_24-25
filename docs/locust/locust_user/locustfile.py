from locust import HttpUser, task, between, events
import jwt
import matplotlib.pyplot as plt
import os, sys
import random as rnd
import datetime

user_host = 'https://localhost:8080'

#liste per conteggiare le occorrenze dei gacha per ogni rarità nei vari roll es: standard_distribution[0]= common, standard_distribution[1]= rare ecc...
standard_distribution = [0,0,0,0,0]
gold_distribution = [0,0,0,0,0]
platinum_distribution = [0,0,0,0,0]
#evento alla fine delle richieste per generare i plot delle distribuzioni di rarità delle estrazioni

def plot_roll_distribution(distribution, distribution_type):

    total_requests = 0    
    for i in range (5):
        total_requests = total_requests + distribution[i]

    
    # Etichette e dati per l'istogramma
    rarity_labels = ['Common Rare', 'Rare', 'Super Rare', 'Ultra Rare', 'Super Ultra Rare']
    occurrences = [distribution[0], distribution[1], distribution[2], distribution[3], distribution[4]]
    # Creazione dell'istogramma
    plt.figure(figsize=(10, 6))
    # Normalizza le occorrenze in base al totale delle richieste
    normalized_occurrences = [occ / total_requests for occ in occurrences]
    plt.bar(rarity_labels, normalized_occurrences, color=['blue', 'green', 'orange', 'red', 'purple'], alpha=0.7)
    # Aggiunta di titolo e label
    plt.title(f"Distribuzione delle Rarità (Totale richieste: {total_requests})", fontsize=16)
    plt.xlabel("Rarità", fontsize=14)
    plt.ylabel(f"Percentuale estrazioni roll {distribution_type}", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    # Mostra i valori sopra ogni barra (in percentuale) con un offset per evitare sovrapposizioni
    for i, value in enumerate(normalized_occurrences):
        plt.text(i, value + 0.02, f"{value*100:.2f}%", ha='center', fontsize=12)
    # Aumenta i limiti dell'asse Y per lasciare spazio alla percentuale
    plt.ylim(0, max(normalized_occurrences) + 0.1)  # Imposta l'asse Y con un margine extra
    # Aggiusta gli spazi per evitare che i valori percentuali si sovrappongano al bordo
    plt.tight_layout()
    # Salvataggio del grafico in formato JPEG
    plt.savefig(os.getcwd() + "/roll_" + distribution_type + "_distribution.jpeg", format='jpeg')
    plt.close('all')

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    # Calcolo del numero totale di richieste
    global standard_distribution
    global gold_distribution
    global platinum_distribution

    plot_roll_distribution(standard_distribution, "standard")
    plot_roll_distribution(gold_distribution, "gold")
    plot_roll_distribution(platinum_distribution, "platinum")


class User(HttpUser):
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
        user_id = rnd.randint(1, 10)
        username = "user"+str(user_id)
        payload = {
            "sub": str(user_id),
            "iat": int(current_time.timestamp()),  # Issued at
            "exp": int(expiry_time.timestamp()),  # Expiry time
            "role": "user",
            "username": username
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

    @task(1)
    def get_collection(self):
        # Get headers
        headers = self.get_headers()

        try: 
            with self.client.get(f'{user_host}/collection', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/collection', e)

    @task(1)
    def get_collection_grouped(self):
        headers = self.get_headers()

        try:
            with self.client.get(f'{user_host}/collection/grouped', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/collection/grouped', e)

    @task(1)
    def see_owned_gacha(self):
        headers = self.get_headers()

        try:
            with self.client.get(f'{user_host}/collection', headers=headers, timeout=10, verify=False,catch_response=True) as collection:

                gacha_ids = []
                if collection.status_code == 200:
                    data_list = collection.json()  # Tenta di deserializzare il JSON
                    for data in data_list:
                        gacha_ids.append(data.get('gachaId'))  # Usa `.get` per evitare KeyError

                    for gacha in gacha_ids:
                        with self.client.get(f'{user_host}/collection/{gacha}', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                            if response.status_code != 200:
                                response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', f'/collection/{gacha}', e)
        
        
    
    @task(1)
    def get_system_collection(self):
        try:
            with self.client.get(f'{user_host}/system_collection', timeout=10, verify=False,catch_response=True) as response:
                if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/system_collection', e)
    
    @task(1)
    def get_specific_system_gacha(self):
        gacha_id = [x for x in range(1, 37)]

        try:
            for gacha in gacha_id:
                with self.client.get(f'{user_host}/system_collection/{gacha}', timeout=10, verify=False,catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', f'/system_collection/{gacha}', e)
    
    @task(5)
    def roll_standard(self):
        headers = self.get_headers()
        global standard_distribution

        try:
            with self.client.post(f'{user_host}/roll/standard', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code in [200,400]:
                    # Ignora questi codici di risposta
                    response.success()
                else:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")

                #codice per ricavare la rarità del gacha estratto, al fine di plottare la distribuzione di rarità:
                try:
                    log = response.json().get("success", "")
                except Exception as e:
                    return str(e)
                if "Gacha" in log:

                    gacha_id = int(log.split("Gacha ")[1].split(" ")[0])
                    if gacha_id <= 18:
                        standard_distribution[0] += 1
                    elif 18 < gacha_id <=30:
                        standard_distribution[1] +=1
                    elif 30 < gacha_id <=33:
                        standard_distribution[2] += 1
                    elif 33 < gacha_id <= 35:
                        standard_distribution[3] += 1
                    elif gacha_id == 36:
                        standard_distribution[4] += 1
                    else:
                        print("Error, Invalid Gacha ID!!!!")
                
                else:
                    print("no gacha in log ERROR!!!")

        except Exception as e:
            self.report_failure('POST', '/roll/standard', e)
    
    @task(5)
    def roll_gold(self):
        headers = self.get_headers()
        global gold_distribution

        try:
            with self.client.post(f'{user_host}/roll/gold', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code in [200,400]:
                    # Ignora questi codici di risposta
                    response.success()
                else:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")
                
                #codice per ricavare la rarità del gacha estratto, al fine di plottare la distribuzione di rarità:
                try:
                    log = response.json().get("success", "")
                except Exception as e:
                    return str(e)
                if "Gacha" in log:

                    gacha_id = int(log.split("Gacha ")[1].split(" ")[0])
                    if gacha_id <= 18:
                        gold_distribution[0] += 1
                    elif 18 < gacha_id <=30:
                        gold_distribution[1] +=1
                    elif 30 < gacha_id <=33:
                        gold_distribution[2] += 1
                    elif 33 < gacha_id <= 35:
                        gold_distribution[3] += 1
                    elif gacha_id == 36:
                        gold_distribution[4] += 1
                    else:
                        print("Error, Invalid Gacha ID!!!!")
                
                else:
                    print("no gacha in log ERROR!!!")

        except Exception as e:
            self.report_failure('POST', '/roll/gold', e)
    
    @task(2)
    def roll_platinum(self):
        headers = self.get_headers()
        global platinum_distribution

        try:
            with self.client.post(f'{user_host}/roll/platinum', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code in [200,400]:
                    # Ignora questi codici di risposta
                    response.success()
                else:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")
                

                #codice per ricavare la rarità del gacha estratto, al fine di plottare la distribuzione di rarità:
                try:
                    log = response.json().get("success", "")
                except Exception as e:
                    return str(e)
                if "Gacha" in log:

                    gacha_id = int(log.split("Gacha ")[1].split(" ")[0])
                    if gacha_id <= 18:
                        platinum_distribution[0] += 1
                    elif 18 < gacha_id <=30:
                        platinum_distribution[1] +=1
                    elif 30 < gacha_id <=33:
                        platinum_distribution[2] += 1
                    elif 33 < gacha_id <= 35:
                        platinum_distribution[3] += 1
                    elif gacha_id == 36:
                        platinum_distribution[4] += 1
                    else:
                        print("Error, Invalid Gacha ID!!!!")
                
                else:
                    print("no gacha in log ERROR!!!")

        except Exception as e:
            self.report_failure('POST', '/roll/platinum', e)
    
    @task(1)
    def get_market(self):  
        headers = self.get_headers()
        try:
            with self.client.get(f'{user_host}/auction_market/market', headers=headers, timeout=10, verify=False,catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"GET request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            self.report_failure('GET', '/auction_market/market', e)

    @task(1)
    def create_auction(self): 
        headers = self.get_headers()
        decoded_payload = jwt.decode(self.jwt_token, self.jwt_secret, self.jwt_algorithm)
        sub = decoded_payload.get("sub")
        gacha_id = rnd.randint(1,36)
        seller_id = int(sub)
        body = {
            "gacha_id": gacha_id,
            "seller_id": seller_id,
            "starting_price": 100,
            "auction_end": "2024-12-31 12:00:00"
        } 
        try:
            with self.client.post(f'{user_host}/auction_market/market', json=body, headers=headers, timeout=10, verify=False, catch_response=True) as response:
                if response.status_code in [201, 400, 409, 404]:
                    # Ignora questi codici di risposta
                    response.success()
                else:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")
        except Exception as e:
            self.report_failure('POST', '/auction_market/market', e)


    @task(1)
    def place_bid(self):  
        headers = self.get_headers()
        decoded_payload = jwt.decode(self.jwt_token, self.jwt_secret, self.jwt_algorithm)
        sub = decoded_payload.get("sub")
        auction_id = rnd.randint(1,100)
        bidder_id = int(sub)
        bid_amount = rnd.randint(101,200)
        body = {
            "auction_id": auction_id,
            "bidder_id": bidder_id,
            "bid_amount": bid_amount
        } 
        try:
            with self.client.post(f'{user_host}/auction_market/market/bid', json=body, headers=headers, timeout=10, verify=False, catch_response=True) as response:
                if response.status_code in [201, 400, 404]:
                    # Ignora questi codici di risposta
                    response.success()
                else:
                    response.failure(f"POST request failed with status code {response.status_code}: {response.text}")
        except Exception as e:
            self.report_failure('POST', '/auction_market/market/bid', e)
    

