.PHONY: clusters-up clusters-down certs seed build deploy test test-e2e dev

KUBECONFIG_PRIVATE := kubeconfig-private.yaml
KUBECONFIG_PUBLIC  := kubeconfig-public.yaml

clusters-up:
	kind create cluster --name private --kubeconfig $(KUBECONFIG_PRIVATE)
	kind create cluster --name public  --kubeconfig $(KUBECONFIG_PUBLIC)

clusters-down:
	kind delete cluster --name private
	kind delete cluster --name public

certs:
	bash certs/gen-certs.sh

seed:
	PYTHONPATH=src python -m private.ingest
	PYTHONPATH=src python -m public.ingest

build:
	docker build -t hybrid-private -f docker/private/Dockerfile .
	docker build -t hybrid-public  -f docker/public/Dockerfile  .

deploy:
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) apply -f manifests/private/
	kubectl --kubeconfig $(KUBECONFIG_PUBLIC)  apply -f manifests/public/

test:
	ruff check .
	ruff format --check .
	pytest tests/unit/ tests/integration/boundary/ -q

test-e2e:
	pytest tests/integration/e2e/ -q

dev: clusters-up certs seed deploy
