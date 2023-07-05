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

COPY requirements/production/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim@sha256:030ead045da5758362ae198e9025671f22490467312dbad9af6b29a6d6bc029b

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq-dev \
      make

RUN groupadd -g 999 app && \
    useradd -r -u 999 -g app app
USER 999

WORKDIR /home/app

COPY --chown=999:999 --from=build /home/app/venv ./venv
COPY --chown=999:999 consent_api/ consent_api/
COPY --chown=999:999 migrations/ migrations/
COPY --chown=999:999 Makefile pytest.ini .

ENV APP_NAME="consent_api"
ENV DATABASE_URL="postgresql+asyncpg://postgres@host.docker.internal:5432/$APP_NAME"
ENV PATH="/home/app/venv/bin:$PATH"
ENV PYTHONUNBUFFERED="True"

CMD alembic --config migrations/alembic.ini upgrade head && uvicorn ${APP_NAME}:app --host="0.0.0.0" --port ${PORT:-8000} --proxy-headers
HEALTHCHECK CMD python -c "import urllib.request as r; r.urlopen('http://localhost:${PORT:-8000}/health')"
