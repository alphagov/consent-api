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

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl && \
    # Install nvm
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash && \
    # This ensures that nvm is properly loaded
    export NVM_DIR="$HOME/.nvm" && \
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" && \
    # Use nvm to install Node 18
    nvm install 18 && \
    nvm use 18 && \
    # Print out the versions to verify installation
    node --version && \
    npm --version && \
    cd client && \
    npm ci && \
    # Needed for rollup minify build to run in docker
    npm i @rollup/rollup-linux-x64-gnu \
    npm run build


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
COPY --chown=999:999 --from=build /home/app/client ./client
COPY --chown=999:999 consent_api/ consent_api/
COPY --chown=999:999 migrations/ migrations/
COPY --chown=999:999 Makefile pytest.ini .

ENV APP_NAME="consent_api" \
    DATABASE_URL="postgresql+asyncpg://postgres@host.docker.internal:5432/$APP_NAME" \
    PATH="/home/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED="True"

CMD ["make", "migrations", "run"]

HEALTHCHECK CMD python -c "import urllib.request as r; r.urlopen('http://localhost:${PORT:-8000}/health')"
