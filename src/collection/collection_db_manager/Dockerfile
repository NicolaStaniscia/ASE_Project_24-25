FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

EXPOSE 5010

CMD flask run --host=0.0.0.0 --port=5010  --cert=/run/secrets/collection_db_manager_cert --key=/run/secrets/collection_db_manager_key