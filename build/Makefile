APP_NAME = icinga2-push-events

APP_DIR = /opt/icinga2-push

PWD = $(shell pwd )
ROOT = $(shell pwd )
SRC_DIR = $(shell pwd )/..
VERSION = 0
COUNTER = $(shell bash get-version.sh )

images: image-app image-testdata

image-app: build-requirements.txt
	docker build -t $(APP_NAME):build -f Containerfile.push $(SRC_DIR)
	docker tag $(APP_NAME):build ghcr.io/wftech/icinga2-push-events/icinga2-push-events:build
	docker push ghcr.io/wftech/icinga2-push-events/icinga2-push-events:build

image-testdata: build-requirements.txt
	docker build -t $(APP_NAME):build -f Containerfile.testdata $(SRC_DIR)
	docker tag $(APP_NAME):build ghcr.io/wftech/icinga2-push-events/icinga2-push-events:testdata
	docker push ghcr.io/wftech/icinga2-push-events/icinga2-push-events:testdata


build-requirements.txt: $(SRC_DIR)/Pipfile
	cd $(SRC_DIR) && pipenv lock --requirements > build-requirements.txt
