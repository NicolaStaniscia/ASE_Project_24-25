FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["flask", "run", "--host=0.0.0.0","--cert=/run/secrets/auction_market_cert","--key=/run/secrets/auction_market_key"]

