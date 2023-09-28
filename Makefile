-include .env
export

APP_NAME ?= consent_api
DATABASE_URL ?= postgresql+asyncpg://localhost:5432/$(APP_NAME)
DOCKER ?= docker
DOCKER_BUILD ?= docker buildx build
DOCKER_DB_URL ?= postgresql+asyncpg://postgres@host.docker.internal:5432/$(APP_NAME)
DOCKER_IMAGE ?= gcr.io/sde-consent-api/consent-api
TAG ?= latest
ENV ?= development
PORT ?= 8000
PREVIEW := $(shell \
		echo $${PREVIEW:+--preview} \
)
SELENIUM_DRIVER ?= chrome
SPLINTER_REMOTE_BROWSER_VERSION ?= ""
SPLINTER_REMOTE_URL := $(shell \
		echo $${SELENIUM_REMOTE_URL:+--splinter-remote-url $${SELENIUM_REMOTE_URL}} \
)

## clean: Remove temporary files
.PHONY: clean
clean:
	find . \( -name '__pycache__' -and -not -name ".venv" \) -depth -prune -exec rm -r {} +

## install: Install dependencies
.PHONY: install
install:
	curl -sSL https://install.python-poetry.org | python3 -
	poetry install

.PHONY: check
check:
	black --check .
	ruff check .

.PHONY: fix
fix:
	pre-commit run --all-files

## migrations: Run all database migrations
.PHONY: migrations
migrations:
	alembic --config migrations/alembic.ini upgrade head

## new-migration: Generate a new database migration from model code
.PHONY: new-migration
new-migration:
	alembic --config migrations/alembic.ini revision --autogenerate

## test: Run tests
.PHONY: test
test:
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning -m "not end_to_end"

.PHONY: test-client
test-client:
	npm test

## test-end-to-end: Run webdriver tests
.PHONY: test-end-to-end
test-end-to-end: migrations
	python consent_api/tests/wait_for_url.py $(E2E_TEST_CONSENT_API_URL)
	python consent_api/tests/wait_for_url.py $(E2E_TEST_DUMMY_SERVICE_1_URL)
	python consent_api/tests/wait_for_url.py $(E2E_TEST_DUMMY_SERVICE_2_URL)
	pytest \
		-W ignore::DeprecationWarning \
		-m end_to_end \
		--splinter-webdriver $(SELENIUM_DRIVER) \
		$(SPLINTER_REMOTE_URL) \
		--splinter-headless

.PHONY: test-all
test-all: migrations test test-end-to-end

.PHONY: test-end-to-end-docker
test-end-to-end-docker:
	$(DOCKER) compose up --exit-code-from test

.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term -W ignore::DeprecationWarning -m "not end_to_end"

## run: Run server
.PHONY: run
run:
	gunicorn $(APP_NAME):app --worker-class uvicorn.workers.UvicornWorker --bind "0.0.0.0:$(PORT)" --forwarded-allow-ips="*"
	#uvicorn $(APP_NAME):app --reload --host "0.0.0.0" --port $(PORT) --proxy-headers --forwarded-allow-ips="*"

## docker-image: Build a Docker image
.PHONY: docker-image
docker-image: clean
	$(DOCKER_BUILD) --platform linux/amd64 --tag $(DOCKER_IMAGE):$(TAG) .

## docker-run: Start a Docker container
.PHONY: docker-run
docker-run:
	$(DOCKER) run \
		--interactive \
		--tty \
		--rm \
		--env DATABASE_URL="$(DOCKER_DB_URL)" \
		--env PORT="$(PORT)" \
		--publish $(PORT):$(PORT) \
		$(DOCKER_IMAGE)

## infra: Create/update a deployment environment
.PHONY: infra
infra:
	python infra/setup_env.py -e $(ENV) $(PREVIEW)

## infra-destroy: Destroy a deployment environment
.PHONY: infra-destroy
infra-destroy:
	python infra/setup_env.py --destroy -e $(ENV) $(PREVIEW)

## deploy: Deploy the service to an environment
.PHONY: deploy
deploy:
	python infra/deploy_service.py -e $(ENV) $(PREVIEW) -b main

.PHONY: destroy-deployment
destroy-deployment:
	python infra/deploy_service.py --destroy -e $(ENV) $(PREVIEW) -b main

## dist: Build client distribution file
.PHONY: dist
dist:
	@mkdir -p client/dist
	$(shell echo ";(function () {\n\n$$(cat client/src/singleconsent.js)\n\n})();\n" > "client/dist/singleconsent.js")
	@echo client/dist/singleconsent.js written

## help: Show this message
.PHONY: help
help: Makefile
	@sed -n 's/^##//p' $< | column -t -s ':' | sed -e 's/^/ /'
