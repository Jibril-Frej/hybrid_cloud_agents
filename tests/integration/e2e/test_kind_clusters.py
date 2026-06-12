"""End-to-end test against the live `private`/`public` kind clusters.

Requires `make dev` (or `clusters-up` + `build` + `load-images` + `deploy`) to
have been run first. Not part of `make test` / CI — run manually via
`make test-e2e`.
"""

import subprocess

import httpx
import pytest

PRIVATE_NODE_PORT = 30080


def _node_ip(container_name: str) -> str:
    """Return the kind Docker network IP of a kind node container."""
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.NetworkSettings.Networks.kind.IPAddress}}", container_name],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.e2e
def test_orchestrator_forwards_query_to_public_worker():
    """The orchestrator's /query combines the public worker's answer with private context."""
    private_ip = _node_ip("private-control-plane")

    response = httpx.post(
        f"http://{private_ip}:{PRIVATE_NODE_PORT}/query",
        json={"query": "hello from e2e"},
    )

    response.raise_for_status()
    answer = response.json()["answer"]
    assert answer.startswith("public worker received: hello from e2e | private context: [")
