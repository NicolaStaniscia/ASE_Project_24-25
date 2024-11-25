FROM python:3.12-slim

WORKDIR /db_manager

COPY app.py .
COPY requirements.txt .
# Copia la directory certs
COPY certs /db_manager/certs

RUN pip install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0 --port=5000 --cert=/db_manager/certs/cert.pem --key=/db_manager/certs/key.pem
