-include .env
export

APP_NAME ?= consent_api
DATABASE_URL ?= postgresql://localhost:5432:$(APP_NAME)
DOCKER_DB_URL ?= postgresql://host.docker.internal:5432/$(APP_NAME)
ENV ?= development
PORT ?= 8000
SELENIUM_DRIVER ?= chrome
SELENIUM_REMOTE_URL := $(shell \
		echo $${SELENIUM_REMOTE_URL:+--splinter-remote-url $${SELENIUM_REMOTE_URL}} \
)

## clean: Remove temporary files
.PHONY: clean
clean:
	find . \( -name '__pycache__' -and -not -name "venv" \) -d -prune -exec rm -r {} +

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
	flask db upgrade

## test: Run tests
.PHONY: test
test:
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning -m "not end_to_end"

## test-end-to-end: Run webdriver tests
.PHONY: test-end-to-end
test-end-to-end: migrations
	pytest \
		-W ignore::DeprecationWarning \
		-m end_to_end \
		--splinter-webdriver $(SELENIUM_DRIVER) \
		$(SELENIUM_REMOTE_URL) \
		--splinter-headless

.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term -W ignore::DeprecationWarning -m "not end_to_end"

## run: Run development server
.PHONY: run
run:
	flask --debug run --debugger --reload --host "0.0.0.0" --port $(PORT)

## docker-image: Build a Docker image
.PHONY: docker-image
docker-image: clean
	docker buildx build --platform linux/amd64 -t $(APP_NAME) .

## docker-run: Start a Docker container
.PHONY: docker-run
docker-run:
	docker run \
		-it \
		--rm \
		--env DATABASE_URL="$(DOCKER_DB_URL)" \
		--env GUNICORN_CMD_ARGS="--bind=0.0.0.0:$(PORT)" \
		-p $(PORT):$(PORT) \
		$(APP_NAME)

## help: Show this message
.PHONY: help
help: Makefile
	@sed -n 's/^##//p' $< | column -t -s ':' | sed -e 's/^/ /'
