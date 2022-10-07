APP_NAME=consent_api
DOCKER_REPO=gcr.io/govuk-bigquery-analytics
STATIC=$(APP_NAME)/static
VERSION=$(shell cat version)


run_dev_server:
	flask --app $(APP_NAME):app --debug run --debugger --reload

docker-image:
	@docker buildx build --platform linux/amd64 -t $(APP_NAME) .
	@docker tag $(APP_NAME) $(APP_NAME):$(VERSION)
	@docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME):$(VERSION)
	@docker push $(DOCKER_REPO)/$(APP_NAME):$(VERSION)
