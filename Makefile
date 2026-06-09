.PHONY: clusters-up clusters-down certs load-certs seed build load-images deploy test test-e2e dev

KUBECONFIG_PRIVATE := kubeconfig-private.yaml
KUBECONFIG_PUBLIC  := kubeconfig-public.yaml

# IP of the public cluster's kind node — reachable from the private cluster
# because both run on the same Docker bridge network.
PUBLIC_NODE_IP := $(shell kubectl --kubeconfig $(KUBECONFIG_PUBLIC) get nodes \
	-o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)

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
	# Patch the orchestrator's hostAlias so 'public-worker' resolves to the
	# public cluster's node IP (cross-cluster DNS doesn't work with kind).
	kubectl --kubeconfig $(KUBECONFIG_PRIVATE) patch deployment orchestrator \
		-p '{"spec":{"template":{"spec":{"hostAliases":[{"ip":"$(PUBLIC_NODE_IP)","hostnames":["public-worker"]}]}}}}'
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
