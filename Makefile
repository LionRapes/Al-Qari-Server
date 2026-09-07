IMAGE_NAME = al-qari-server
CONTAINER_NAME = al-qari-server-container
PORT = 8080
REGISTRY_ID ?= 0
TAG ?= latest
APP_ENV ?= development

.PHONY: build run dev stop clean logs

build:
	docker build -t $(IMAGE_NAME):${TAG} .

run:
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):8080 \
	  --env-file .env \
	  --env-file .env.production \
	  -e APP_ENV=production \
	  $(IMAGE_NAME)

dev:
	docker run -d --name $(CONTAINER_NAME)-dev -p $(PORT):8080 \
	  --env-file .env \
	  -e APP_ENV \
	  -v $(CURDIR)/app:/code/app \
	  $(IMAGE_NAME) \
	  python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker stop $(CONTAINER_NAME)-dev || true
	docker rm $(CONTAINER_NAME)-dev || true

clean: stop
	docker rmi $(IMAGE_NAME) || true

logs:
	docker logs -f $(CONTAINER_NAME)

tag:
	docker tag $(IMAGE_NAME):$(TAG) cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG)

push:
	@if [ "$(REGISTRY_ID)" = "0" ]; then \
		echo "ERROR: REGISTRY_ID is 0. Push cancelled."; \
		exit 1; \
	fi
	
	docker build --provenance=false -t $(IMAGE_NAME)_deploy:${TAG} .
	powershell -Command "Start-Sleep -Seconds 2"

	docker tag $(IMAGE_NAME)_deploy:$(TAG) cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG)
	powershell -Command "Start-Sleep -Seconds 2"

	docker push cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG)
	powershell -Command "Start-Sleep -Seconds 2"
	
	docker rmi $(IMAGE_NAME)_deploy:$(TAG) 2>NUL || exit 0
	docker rmi cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG) 2>NUL || exit 0