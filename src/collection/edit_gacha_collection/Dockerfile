FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

EXPOSE 5008

CMD flask run --host=0.0.0.0 --port=5008 --cert=/run/secrets/edit_gacha_collection_cert --key=/run/secrets/edit_gacha_collection_key