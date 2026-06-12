#!/usr/bin/env bash
# Generate a self-signed CA plus a server cert (public worker) and a client
# cert (orchestrator), both signed by that CA. Used for mTLS between the
# private and public clusters (see specs/v2-spec.md).
#
# Usage: certs/gen-certs.sh [output-dir]
#   output-dir defaults to certs/ (relative to the repo root).
set -euo pipefail

OUT_DIR="${1:-$(dirname "$0")}"
mkdir -p "$OUT_DIR"
cd "$OUT_DIR"

DAYS=825

# CA
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
  -subj "/CN=hybrid-cloud-agents-ca" -out ca.crt \
  -addext "keyUsage=keyCertSign,cRLSign"

# Server cert (public worker) — SANs cover the in-cluster service name, the
# kind hostAliases name used by the orchestrator, and localhost for local/test runs.
openssl genrsa -out server.key 2048
openssl req -new -key server.key -subj "/CN=public-worker" -out server.csr
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days "$DAYS" -sha256 -out server.crt \
  -extfile <(printf "subjectAltName=DNS:public-worker,DNS:public-cluster,DNS:localhost,IP:127.0.0.1")

# Client cert (orchestrator)
openssl genrsa -out client.key 2048
openssl req -new -key client.key -subj "/CN=orchestrator" -out client.csr
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days "$DAYS" -sha256 -out client.crt

rm -f server.csr client.csr
