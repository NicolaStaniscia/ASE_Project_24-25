FROM python:3.12-slim

WORKDIR /app

# Copia il resto dei file
COPY . .

RUN pip install -r requirements.txt

# Comando per avviare il server Flask
CMD ["flask", "run", "--host=0.0.0.0","--cert=./certs/cert.pem","--key=./certs/key.pem"]
