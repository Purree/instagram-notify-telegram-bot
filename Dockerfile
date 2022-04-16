FROM python:3.9.7-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y \
    && apt-get clean \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD [ "python", "main.py"]