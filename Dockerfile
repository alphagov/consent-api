FROM python:3.10-slim

WORKDIR /home/app

COPY consent_api/ consent_api/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT gunicorn consent_api:app
