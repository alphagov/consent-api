-include .envrc

DOCKER_IMAGE ?= gcr.io/sde-consent-api/consent-api
TAG ?= latest
ENV ?= development


# ---------------------------------------------------------------------------------
# STARTUP COMMANDS
# ---------------------------------------------------------------------------------
# Commands that start the project in different modes

.PHONY: docker-run docker-e2e docker-e2e-ui docker-e2e-debug

docker-run:
	docker-compose --profile local up

docker-e2e:
	docker-compose --profile test up

docker-e2e-ui:
	docker-compose --profile test-ui up

docker-e2e-debug:
	docker-compose --profile debug up

docker-e2e-codegen:
	docker-compose --profile codegen up playwright-codegen



# ---------------------------------------------------------------------------------
# PROJECT SETUP COMMANDS
# ---------------------------------------------------------------------------------
# Use this section for commands that help set up the project, like installing dependencies, setting up databases, etc.

.PHONY: install migrations new-migration

## install: Install dependencies
install: install-consent-api install-client install-e2e-tests

install-consent-api:
	@command -v poetry >/dev/null 2>&1 || { echo >&2 "Poetry is not installed. Please install it by following the instructions at https://python-poetry.org/docs/#installation"; exit 1; }
	poetry install

install-client:
	cd client && npm install && npm run build

install-e2e-tests:
	cd e2e-tests && npm install



# ---------------------------------------------------------------------------------
# DB COMMANDS
# ---------------------------------------------------------------------------------
# Commands for managing the database

## migrations: Run all database migrations
migrations:
	alembic --config migrations/alembic.ini upgrade head

## new-migration: Generate a new database migration from model code
new-migration:
	alembic --config migrations/alembic.ini revision --autogenerate



# ---------------------------------------------------------------------------------
# INFRA COMMANDS
# ---------------------------------------------------------------------------------
# Infrastructure-related commands, like IaC, Pulumi setups & deployments, etc.

.PHONY: infra infra-destroy deploy destroy-deployment

## infra: Create/update a deployment environment
infra:
	python infra/setup_env.py -e $(ENV) $(PREVIEW)

## infra-destroy: Destroy a deployment environment
infra-destroy:
	python infra/setup_env.py --destroy -e $(ENV) $(PREVIEW)

## deploy: Deploy the service to an environment
deploy:
	python infra/deploy.py -e $(ENV) $(PREVIEW) -b main

destroy-deployment:
	python infra/deploy.py --destroy -e $(ENV) $(PREVIEW) -b main



# ---------------------------------------------------------------------------------
# Linting / Formatting
# ---------------------------------------------------------------------------------
# Commands for linting and formatting code

.PHONY: fix check

fix:
	pre-commit run --all-files

check:
	black --check .
	ruff check .


# ---------------------------------------------------------------------------------
# OTHER
# ---------------------------------------------------------------------------------
# Use this section for miscellaneous commands that don't fit into the above categories.

.PHONY: clean test

## clean: Remove temporary files
clean:
	find . \( -name '__pycache__' -and -not -name ".venv" \) -depth -prune -exec rm -r {} +


test:
	pytest -x -n=auto --dist=loadfile -W ignore::DeprecationWarning -m "not end_to_end"


.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term -W ignore::DeprecationWarning -m "not end_to_end"

## run: Run server
.PHONY: run
run:
ifeq ($(ENV),development)
	uvicorn consent_api:app --reload --host "0.0.0.0" --port $(PORT) --proxy-headers --forwarded-allow-ips="*"
else ifeq ($(ENV),testing)
	uvicorn consent_api:app --reload --host "0.0.0.0" --port $(PORT) --proxy-headers --forwarded-allow-ips="*"
else
	gunicorn consent_api:app --worker-class uvicorn.workers.UvicornWorker --bind "0.0.0.0:$(PORT)" --forwarded-allow-ips="*"
endif


## docker-build: Build a Docker image
.PHONY: docker-build
docker-build: clean
	docker buildx build --platform linux/amd64 --tag $(DOCKER_IMAGE):$(TAG) .


## help: Show this message
.PHONY: help
help: Makefile
	@sed -n 's/^##//p' $< | column -t -s ':' | sed -e 's/^/ /'
