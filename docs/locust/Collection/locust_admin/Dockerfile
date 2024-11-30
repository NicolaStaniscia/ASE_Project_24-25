FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY locustfile.py /app/locustfile.py

RUN python3 -m pip install -r requirements.txt

EXPOSE 8090

CMD locust -f locustfile.py --host=http://localhost --web-port 8090