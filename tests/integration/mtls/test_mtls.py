"""Integration tests for mTLS enforcement between orchestrator and public worker.

Asserts that:
1. Clients with valid certificates signed by the trusted CA are accepted.
2. Clients without certificates are rejected.
3. Clients with certificates signed by an untrusted CA are rejected.
4. The orchestrator can successfully call the public worker over real mTLS.

This validates the transport-layer security in specs/v2-spec.md.
"""

import os
import signal
import socket
import ssl
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import orchestrator.main
from tests.conftest import REPO_ROOT

# A failed TLS handshake (missing/untrusted client cert) surfaces differently
# depending on the platform's OpenSSL build: some raise ConnectError/SSLError
# directly, others close the connection before responding, which httpx reports
# as RemoteProtocolError.
HANDSHAKE_FAILURE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
    ssl.SSLError,
)


def _trust(
    ca_cert_path: Path, cert_path: Path | None = None, key_path: Path | None = None
) -> ssl.SSLContext:
    """Build an SSL context that trusts the given CA and, optionally, presents a client cert.

    httpx's string-path form of `verify=` is deprecated, and so is its
    `cert=` kwarg — both the CA and the client cert/key must be combined into
    a single ssl.SSLContext passed as `verify=`.
    """
    context = ssl.create_default_context(cafile=str(ca_cert_path))
    if cert_path is not None and key_path is not None:
        context.load_cert_chain(str(cert_path), str(key_path))
    return context


class TestTrustHelper:
    """Unit tests for the _trust() helper function."""

    @pytest.mark.parametrize("missing", ["key", "cert"])
    def test_trust_ignores_incomplete_cert_pair(self, temp_certs_dir, missing):
        """_trust() ignores cert_path/key_path if only one of the pair is given."""
        ca_path = temp_certs_dir["good"] / "ca.crt"
        cert_path = None if missing == "cert" else temp_certs_dir["good"] / "client.crt"
        key_path = None if missing == "key" else temp_certs_dir["good"] / "client.key"

        context = _trust(ca_path, cert_path, key_path)
        assert isinstance(context, ssl.SSLContext)


def _find_free_port() -> int:
    """Find an available TCP port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    return port


def _wait_for_server(host: str, port: int, max_attempts: int = 100, delay: float = 0.1) -> bool:
    """Poll a server until it's listening or timeout.

    Args:
        host: The host to connect to.
        port: The port to connect to.
        max_attempts: Maximum number of retries.
        delay: Delay in seconds between retries.

    Returns:
        True if server became ready, False if timeout.
    """
    for attempt in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                s.connect((host, port))
            return True
        except (OSError, TimeoutError):
            if attempt < max_attempts - 1:
                time.sleep(delay)
    return False


@pytest.fixture(scope="session")
def public_worker_server(temp_certs_dir):
    """Start the public worker as a subprocess with mTLS enabled.

    Yields:
        A dict with 'url' (str), 'good_dir' (Path), and 'bad_dir' (Path).
    """
    port = _find_free_port()
    url = f"https://127.0.0.1:{port}/query"

    good_dir = temp_certs_dir["good"]

    # Start the public worker the same way manifests/public/deployment.yaml does:
    # `uv run uvicorn` picks up TLS config from UVICORN_SSL_* env vars
    # (ssl-cert-reqs=2 is ssl.CERT_REQUIRED).
    env = os.environ | {
        "UVICORN_SSL_CERTFILE": str(good_dir / "server.crt"),
        "UVICORN_SSL_KEYFILE": str(good_dir / "server.key"),
        "UVICORN_SSL_CA_CERTS": str(good_dir / "ca.crt"),
        "UVICORN_SSL_CERT_REQS": "2",
    }
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "public.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    def _terminate() -> None:
        # `uv run` re-execs uvicorn as a child process; killing the whole
        # process group (via start_new_session=True above) ensures both die.
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGKILL)
            process.wait()

    # Wait for server to be ready (just check TCP connectivity)
    ready = _wait_for_server("127.0.0.1", port, max_attempts=100, delay=0.1)
    if not ready:
        _terminate()
        pytest.fail(f"Public worker server did not start on {url} within timeout")

    yield {
        "url": url,
        "good_dir": good_dir,
        "bad_dir": temp_certs_dir["bad"],
    }

    _terminate()


class TestMTLSEnforcement:
    """Test that mTLS is properly enforced on the public worker."""

    def test_valid_client_cert_succeeds(self, public_worker_server):
        """Request with valid client cert signed by trusted CA succeeds.

        This is the happy path: orchestrator has the correct certs and can
        communicate with the public worker.
        """
        url = public_worker_server["url"]
        good_dir = public_worker_server["good_dir"]

        client = httpx.Client(
            verify=_trust(good_dir / "ca.crt", good_dir / "client.crt", good_dir / "client.key"),
        )

        response = client.post(url, json={"query": "test query"})
        assert response.status_code == 200
        data = response.json()
        # The public worker now returns retrieved public document chunks.
        assert "answer" in data
        assert data["answer"]

        client.close()

    def test_missing_client_cert_fails(self, public_worker_server):
        """Request without client cert is rejected by server.

        The public worker requires mutual TLS, so requests without a client
        certificate should fail at the TLS handshake level.
        """
        url = public_worker_server["url"]
        good_dir = public_worker_server["good_dir"]

        # Client with no cert, but trusting the CA
        client = httpx.Client(verify=_trust(good_dir / "ca.crt"))

        with pytest.raises(HANDSHAKE_FAILURE_EXCEPTIONS):
            client.post(url, json={"query": "test query"})

        client.close()

    def test_client_cert_from_untrusted_ca_fails(self, public_worker_server):
        """Request with cert signed by untrusted CA is rejected.

        Even though the request has a client certificate, it is signed by a
        different CA that the server does not trust. The TLS handshake should fail.
        """
        url = public_worker_server["url"]
        good_dir = public_worker_server["good_dir"]
        bad_dir = public_worker_server["bad_dir"]

        # Client with cert signed by bad CA, trying to connect to server
        # that only trusts the good CA
        client = httpx.Client(
            verify=_trust(good_dir / "ca.crt", bad_dir / "client.crt", bad_dir / "client.key"),
        )

        with pytest.raises(HANDSHAKE_FAILURE_EXCEPTIONS):
            client.post(url, json={"query": "test query"})

        client.close()


class TestOrchestratorMTLS:
    """Test the orchestrator's end-to-end mTLS communication with public worker."""

    def test_orchestrator_query_endpoint_over_real_mtls(self, public_worker_server, monkeypatch):
        """POST /query from orchestrator to public worker over real mTLS succeeds.

        This is the full integration test: the orchestrator's _mtls_kwargs()
        builds an SSLContext from real cert files and httpx.post() executes
        the request over real mTLS to the public worker (not mocked).
        """
        url = public_worker_server["url"]
        good_dir = public_worker_server["good_dir"]

        # Set the orchestrator's mTLS config to point at the live public worker
        # and the generated certs (good_dir is already trusted by the server)
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_URL", url)
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CERT", str(good_dir / "client.crt"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_KEY", str(good_dir / "client.key"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CA", str(good_dir / "ca.crt"))

        # Call the orchestrator's /query endpoint (via TestClient, no mocking of httpx.post)
        client = TestClient(orchestrator.main.app)
        response = client.post("/query", json={"query": "test query over mtls"})

        # Assert successful response with the expected format
        assert response.status_code == 200
        data = response.json()
        # The answer combines retrieved public chunks with private context
        # appended locally.
        assert "answer" in data
        assert "private context:" in data["answer"]
