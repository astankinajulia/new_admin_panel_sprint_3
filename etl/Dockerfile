FROM python:3.10

WORKDIR /opt/etl

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y netcat

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip --no-cache-dir \
     && pip install -r requirements.txt --no-cache-dir

COPY . .

RUN ["chmod", "+x", "./deploy/entrypoint.sh"]

ENTRYPOINT ["./deploy/entrypoint.sh"]
