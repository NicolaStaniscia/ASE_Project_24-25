FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

EXPOSE 5009

CMD flask run --host=0.0.0.0 --port=5009 --cert=/run/secrets/roll_gacha_cert --key=/run/secrets/roll_gacha_key