# V2 Spec — Harden the transport (mTLS)

V2 takes the V1 plumbing and adds mutual TLS between the orchestrator and the
public worker. **No application logic changes** — the wire contract
(`PublicWorkerRequest` / `PublicWorkerResponse`) and the request/response flow
are identical to V1. This version is purely "the same system, but encrypted
and mutually authenticated."

## Adds on top of V1

- `certs/gen-certs.sh` — generates a self-signed CA plus a client cert/key
  (orchestrator) and a server cert/key (public worker).
- `make certs` — runs the script.
- `make load-certs` — pushes the certs into each cluster as Kubernetes
  Secrets (`mtls-certs-private`, `mtls-certs-public`).
- Cert volume mounts on both Deployments, and env vars on the orchestrator
  pointing at its client cert/key and the shared CA
  (`PUBLIC_WORKER_CERT`, `PUBLIC_WORKER_KEY`, `PUBLIC_WORKER_CA`).
- The public worker's uvicorn server is configured for TLS with client-cert
  verification (`ssl_cert_reqs=CERT_REQUIRED`).
- `PUBLIC_WORKER_URL` changes from `http://...` to `https://...`.

## Tests

- The existing V1 boundary test continues to pass unchanged — the request
  shape (`{"query": "..."}`) hasn't changed.
- New test: a client without a valid client certificate (or with the wrong
  CA) is rejected by the public worker — i.e., mTLS is actually enforced, not
  just configured.

## `.gitignore`

Generated cert material (`certs/*.crt`, `certs/*.key`, `certs/*.csr`,
`certs/*.srl`, `certs/*.pem`) is gitignored; only `gen-certs.sh` is tracked.
