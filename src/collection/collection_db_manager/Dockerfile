FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN python3 -m pip install -r requirements.txt

EXPOSE 5010

CMD flask run --host=0.0.0.0 --port=5010  --cert=./https/cert.pem --key=./https/key.pem