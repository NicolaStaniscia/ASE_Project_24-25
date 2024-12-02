FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

EXPOSE 5007

CMD flask run --host=0.0.0.0 --port=5007 --cert=/run/secrets/see_gacha_collection_cert --key=/run/secrets/see_gacha_collection_key