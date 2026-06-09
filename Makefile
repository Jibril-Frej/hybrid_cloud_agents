.PHONY: clusters-up clusters-down certs load-certs seed build load-images deploy test test-e2e dev lock

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

# Push mTLS certs into each cluster as Kubernetes Secrets.
load-certs:
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) create secret generic mtls-certs-private \
		--from-file=ca.crt=certs/ca.crt \
		--from-file=client.crt=certs/client.crt \
		--from-file=client.key=certs/client.key \
		--dry-run=client -o yaml | kubectl --kubeconfig $(KUBECONFIG_PRIVATE) apply -f -
	kubectl --kubeconfig $(KUBECONFIG_PUBLIC) create secret generic mtls-certs-public \
		--from-file=ca.crt=certs/ca.crt \
		--from-file=server.crt=certs/server.crt \
		--from-file=server.key=certs/server.key \
		--dry-run=client -o yaml | kubectl --kubeconfig $(KUBECONFIG_PUBLIC) apply -f -

# Regenerate uv.lock after adding or removing a dependency in pyproject.toml.
lock:
	uv lock

seed:
	PYTHONPATH=src python -m private.ingest
	PYTHONPATH=src python -m public.ingest

build:
	docker build -t hybrid-private:latest -f docker/private/Dockerfile .
	docker build -t hybrid-public:latest  -f docker/public/Dockerfile  .

# Load locally-built images into the kind clusters (bypasses a registry).
load-images:
	kind load docker-image hybrid-private:latest --name private
	kind load docker-image hybrid-public:latest  --name public

deploy:
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) apply -f manifests/private/
	kubectl --kubeconfig $(KUBECONFIG_PUBLIC)  apply -f manifests/public/
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) rollout restart deployment/orchestrator
	kubectl --kubeconfig $(KUBECONFIG_PUBLIC)  rollout restart deployment/public-worker
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) rollout status  deployment/orchestrator
	kubectl --kubeconfig $(KUBECONFIG_PUBLIC)  rollout status  deployment/public-worker

test:
	ruff check .
	ruff format --check .
	pytest tests/unit/ tests/integration/boundary/ -q

test-e2e:
	pytest tests/integration/e2e/ -q

dev: clusters-up certs load-certs seed build load-images deploy
