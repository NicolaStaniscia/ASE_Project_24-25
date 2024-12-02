FROM python:3.12-slim

WORKDIR /account_management

COPY app.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0 --port=5000 --cert=/run/secrets/account_management_cert --key=/run/secrets/account_management_key
