FROM python:3.11-slim AS build

WORKDIR /home/app

COPY requirements/production/requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        python3-dev \
        libpq-dev && \
    pg_config --version && \
    python -m venv /home/app/venv && \
    venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim@sha256:364ee1a9e029fb7b60102ae56ff52153ccc929ceab9aa387402fe738432d24cc

WORKDIR /home/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        make && \
    groupadd -g 999 app && \
    useradd -r -u 999 -g app app

USER 999

COPY --chown=999:999 --from=build /home/app/venv ./venv
COPY --chown=999:999 consent_api/ consent_api/
COPY --chown=999:999 migrations/ migrations/
COPY --chown=999:999 Makefile pytest.ini .

ENV APP_NAME="consent_api" \
    DATABASE_URL="postgresql+asyncpg://postgres@host.docker.internal:5432/$APP_NAME" \
    PATH="/home/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED="True"

CMD ["make", "migrations", "run"]

HEALTHCHECK CMD python -c "import urllib.request as r; r.urlopen('http://localhost:${PORT:-8000}/health')"
