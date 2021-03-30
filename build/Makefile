APP_NAME = icinga2-push-events

APP_DIR = /opt/icinga2-push

PWD = $(shell pwd )
ROOT = $(shell pwd )
SRC_DIR = $(shell pwd )/..
VERSION = 0
COUNTER = $(shell bash get-version.sh )

image-app: build-requirements.txt
	docker build -t $(APP_NAME):build -f Containerfile $(SRC_DIR)

build-requirements.txt: $(SRC_DIR)/Pipfile
	cd $(SRC_DIR) && pipenv lock --requirements > build-requirements.txt
