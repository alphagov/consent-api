FROM python:3.10-slim AS build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    libpq-dev

RUN pg_config --version
WORKDIR /home/app
RUN python -m venv /home/app/venv
ENV PATH="/home/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim@sha256:030ead045da5758362ae198e9025671f22490467312dbad9af6b29a6d6bc029b

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev

RUN groupadd -g 999 app && \
    useradd -r -u 999 -g app app
USER 999

WORKDIR /home/app

COPY --from=build /home/app/venv ./venv
COPY consent_api/ consent_api/
COPY migrations/ migrations/

ENV PATH="/home/app/venv/bin:$PATH"

ENTRYPOINT gunicorn consent_api:app
