ENV ?= development

-include .env
export

PORT ?= 8000

.PHONY: clean
clean:
	find . \( -name '__pycache__' -and -not -name "venv" \) -d -prune -exec rm -r {} +

.PHONY: deps
deps:
	python -m pip install -U pip
	python -m pip install -r requirements.txt
	[ -f requirements-$(ENV).txt ] && python -m pip install -r requirements-$(ENV).txt

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
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning

.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term -W ignore::DeprecationWarning

.PHONY: run
run:
	flask --debug run --debugger --reload

.PHONY: docker-image
docker-image: clean
	docker buildx build --platform linux/amd64 -t $(APP_NAME) .

.PHONY: docker-run
docker-run:
	docker run -d --rm --env DATABASE_URL="$(DATABASE_URL)" --env GUNICORN_CMD_ARGS="--bind=0.0.0.0:$(PORT)" -p 8000:$(PORT) $(APP_NAME)
