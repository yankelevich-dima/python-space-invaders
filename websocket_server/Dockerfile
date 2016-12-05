FROM python:3.5

RUN mkdir /app
COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y python-pygame

COPY requirements.txt ./

RUN pip install -r /app/requirements.txt

CMD cd /app/websocket_server && python server.py
