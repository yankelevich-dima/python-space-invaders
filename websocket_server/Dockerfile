FROM python:3.5

RUN apt-get update -y && apt-get install -y python-pygame alsa-utils

RUN mkdir /app
COPY . /app
WORKDIR /app

COPY requirements.txt ./

RUN pip install -r /app/requirements.txt

CMD cd /app/websocket_server && python server.py
