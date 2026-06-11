PRIVATE_CTX := kind-private
PUBLIC_CTX := kind-public
PUBLIC_NODE := public-control-plane

.PHONY: clusters-up clusters-down build load-images deploy test test-e2e dev

clusters-up:
	kind create cluster --name private
	kind create cluster --name public

clusters-down:
	kind delete cluster --name private
	kind delete cluster --name public

build:
	docker build -f docker/private/Dockerfile -t orchestrator:latest .
	docker build -f docker/public/Dockerfile -t public-worker:latest .

load-images:
	kind load docker-image orchestrator:latest --name private
	kind load docker-image public-worker:latest --name public

deploy:
	kubectl --context $(PUBLIC_CTX) apply -f manifests/public/deployment.yaml
	# Patch the orchestrator's hostAliases placeholder with the public node's
	# real address — kind clusters share a Docker network but not DNS.
	$(eval PUBLIC_NODE_IP := $(shell docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' $(PUBLIC_NODE)))
	sed 's/0.0.0.0/$(PUBLIC_NODE_IP)/' manifests/private/deployment.yaml | kubectl --context $(PRIVATE_CTX) apply -f -
	kubectl --context $(PUBLIC_CTX) rollout restart deployment/public-worker
	kubectl --context $(PRIVATE_CTX) rollout restart deployment/orchestrator
	kubectl --context $(PUBLIC_CTX) rollout status deployment/public-worker
	kubectl --context $(PRIVATE_CTX) rollout status deployment/orchestrator

test:
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest tests/unit/ tests/integration/boundary/ -q

test-e2e:
	uv run pytest tests/integration/e2e/ -m e2e -q

dev: clusters-up build load-images deploy
