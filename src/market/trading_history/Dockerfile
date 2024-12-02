FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["flask", "run", "--host=0.0.0.0","--cert=/run/secrets/trading_history_cert","--key=/run/secrets/trading_history_key"]
