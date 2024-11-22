FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["flask", "run", "--host=0.0.0.0","--cert=./certs/cert.pem","--key=./certs/key.pem"]

