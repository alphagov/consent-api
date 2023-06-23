-include .env
export

APP_NAME ?= consent_api
DATABASE_URL ?= postgresql://localhost:5432/$(APP_NAME)
DOCKER ?= docker
DOCKER_BUILD ?= docker buildx build
DOCKER_DB_URL ?= postgresql+asyncpg://postgres@host.docker.internal:5432/$(APP_NAME)
DOCKER_IMAGE ?= gcr.io/sde-consent-api/consent-api
TAG ?= latest
ENV ?= development
PORT ?= 8000
SELENIUM_DRIVER ?= chrome
SPLINTER_REMOTE_BROWSER_VERSION ?= ""
SPLINTER_REMOTE_URL := $(shell \
		echo $${SELENIUM_REMOTE_URL:+--splinter-remote-url $${SELENIUM_REMOTE_URL}} \
)

## clean: Remove temporary files
.PHONY: clean
clean:
	find . \( -name '__pycache__' -and -not -name "venv" \) -depth -prune -exec rm -r {} +

## install: Install dependencies
.PHONY: install
install:
	python -m pip install -U pip
	pip install -r requirements/production/requirements.txt
	if [ -f requirements/$(ENV)/requirements.txt ]; then pip install -r requirements/$(ENV)/requirements.txt; fi

.PHONY: check
check:
	black --check .
	isort --check-only --profile=black --force-single-line-imports .
	flake8 --max-line-length=88 --extend-ignore=E203 --exclude migrations

.PHONY: fix
fix:
	pre-commit run --all-files

.PHONY: migrations
migrations:
	alembic --config migrations/alembic.ini upgrade head

.PHONY: new-migration
new-migration:
	alembic --config migrations/alembic.ini revision --autogenerate

## test: Run tests
.PHONY: test
test:
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning -m "not end_to_end"

## test-end-to-end: Run webdriver tests
.PHONY: test-end-to-end
test-end-to-end: migrations
	python consent_api/tests/wait_for_url.py $(E2E_TEST_CONSENT_API_URL)
	python consent_api/tests/wait_for_url.py $(E2E_TEST_GOVUK_URL)
	python consent_api/tests/wait_for_url.py $(E2E_TEST_HAAS_URL)
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

## run: Run development server
.PHONY: run
run:
	uvicorn $(APP_NAME):app --reload --host "0.0.0.0" --port $(PORT)

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

## help: Show this message
.PHONY: help
help: Makefile
	@sed -n 's/^##//p' $< | column -t -s ':' | sed -e 's/^/ /'
