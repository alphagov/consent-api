-include .env
export

APP_NAME ?= consent_api
DATABASE_URL ?= postgresql://localhost:5432:$(APP_NAME)
DOCKER_DB_URL ?= postgresql://host.docker.internal:5432/$(APP_NAME)
ENV ?= development
PORT ?= 8000
SELENIUM_DRIVER ?= chrome

.PHONY: clean
clean:
	find . \( -name '__pycache__' -and -not -name "venv" \) -d -prune -exec rm -r {} +

.PHONY: deps
deps:
	python -m pip install -U pip
	pip install -r requirements.txt
	if [ -f requirements-$(ENV).txt ]; then pip install -r requirements-$(ENV).txt; fi

.PHONY: lint
lint:
	black --check .
	isort --check-only --profile=black --force-single-line-imports .
	flake8 --max-line-length=88 --extend-ignore=E203 --exclude migrations

.PHONY: lint-fix
lint-fix:
	pre-commit run --all-files

.PHONY: run-migrations
run-migrations:
	flask db upgrade

.PHONY: test
test:
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning -m "not end_to_end"

.PHONY: test-e2e
test-e2e:
	pytest \
		-W ignore::DeprecationWarning \
		-m end_to_end \
		--splinter-webdriver $(SELENIUM_DRIVER) \
		--splinter-headless

.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term -W ignore::DeprecationWarning -m "not end_to_end"

.PHONY: run
run:
	flask --debug run --debugger --reload --host "0.0.0.0" --port $(PORT)

.PHONY: docker-image
docker-image: clean
	docker buildx build --platform linux/amd64 -t $(APP_NAME) .

.PHONY: docker-run
docker-run:
	docker run \
		-it \
		--rm \
		--env DATABASE_URL="$(DOCKER_DB_URL)" \
		--env GUNICORN_CMD_ARGS="--bind=0.0.0.0:$(PORT)" \
		-p $(PORT):$(PORT) \
		$(APP_NAME)
