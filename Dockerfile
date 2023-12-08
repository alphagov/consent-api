FROM python:3.11-slim@sha256:1591aa8c01b5b37ab31dbe5662c5bdcf40c2f1bce4ef1c1fd24802dae3d01052 as build

WORKDIR /home/app

COPY pyproject.toml ./
COPY poetry.lock ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        python3-dev \
        libpq-dev \
    && pg_config --version \
    && pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry install --only main --no-ansi

COPY --chown=999:999 client/ client/


FROM node:20-slim as node-build

WORKDIR /home/client

COPY client/ /home/client

RUN npm install @rollup/rollup-linux-x64-gnu \
    && npm run build


FROM python:3.11-slim@sha256:1591aa8c01b5b37ab31dbe5662c5bdcf40c2f1bce4ef1c1fd24802dae3d01052

WORKDIR /home/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        make && \
    groupadd -g 999 app && \
    useradd -r -u 999 -g app app

USER 999

COPY --chown=999:999 --from=build /home/app/.venv ./.venv
COPY --chown=999:999 --from=node-build /home/client/dist/ ./client/dist/
COPY --chown=999:999 --from=node-build /home/client/examples/ ./client/examples/
COPY --chown=999:999 consent_api/ consent_api/
COPY --chown=999:999 migrations/ migrations/
COPY --chown=999:999 Makefile pytest.ini .

ENV APP_NAME="consent_api" \
    DATABASE_URL="postgresql+asyncpg://postgres@host.docker.internal:5432/$APP_NAME" \
    PATH="/home/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED="True"

CMD ["make", "migrations", "run"]

HEALTHCHECK CMD python -c "import urllib.request as r; r.urlopen('http://localhost:${PORT:-8000}/health')"
