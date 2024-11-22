FROM python:3.12-slim

WORKDIR /account_management

COPY app.py .
COPY requirements.txt .
# Copia la directory certs
COPY certs /account_management/certs

RUN pip install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0 --port=5000 --cert=/account_management/certs/cert.pem --key=/account_management/certs/key.pem
