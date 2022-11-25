ENV ?= development

-include .env
export

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
	flake8 --max-line-length=88 --extend-ignore=E203
	mypy --namespace-packages .

.PHONY: lint-fix
lint-fix:
	pre-commit run --all-files

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
