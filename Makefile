IMAGE_NAME = al-qari-server
CONTAINER_NAME = al-qari-server-container
PORT = 8080
REGISTRY_ID ?= 0
TAG ?= latest

.PHONY: build run dev stop clean logs

build:
	docker build -t $(IMAGE_NAME):${TAG} .

run:
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):8080 \
	  --env-file .env \
	  $(IMAGE_NAME) \
	  python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

dev:
	docker run -d --name $(CONTAINER_NAME)-dev -p $(PORT):8080 \
	  --env-file .env \
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
	docker build --provenance=false -t $(IMAGE_NAME)_deploy:${TAG} .
	sleep 2
	docker tag $(IMAGE_NAME)_deploy:$(TAG) cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG)
	sleep 2
	docker push cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG)
	sleep 2
	
	docker rmi $(IMAGE_NAME)_deploy:$(TAG) 2>/dev/null || true
	docker rmi cr.yandex/$(REGISTRY_ID)/$(IMAGE_NAME):$(TAG) 2>/dev/null || true