ENV ?= dev

-include .env
export

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

.PHONY: lint-fix
lint-fix:
	pre-commit run --all-files

.PHONY: mypy
mypy:
	mypy --package $(APP_NAME) --namespace-packages

.PHONY: test
test:
	pytest -x -n=auto --dist=loadfile

.PHONY: test-coverage
test-coverage:
	pytest -n=auto --cov --cov-report=xml --cov-report=term

.PHONY: run
run:
	flask --app $(APP_NAME):app --debug run --debugger --reload

.PHONY: docker-image
docker-image:
	@docker buildx build --platform linux/amd64 -t $(APP_NAME) .
	@docker tag $(APP_NAME) $(APP_NAME):$(VERSION)

.PHONY: docker-push
docker-push: docker-image
	@docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME):$(VERSION)
	@docker push $(DOCKER_REPO)/$(APP_NAME):$(VERSION)
