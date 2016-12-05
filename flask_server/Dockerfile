FROM python:3.5

RUN apt-get update -y && apt-get install -y python-psycopg2 gunicorn

RUN mkdir /app
COPY . /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

CMD cd /app/flask_server && gunicorn -b 0.0.0.0:8000 -w 4 -t 360 --log-level debug server:app
