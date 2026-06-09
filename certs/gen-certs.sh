#!/usr/bin/env bash
# Generates a self-signed CA plus server and client cert/key pairs for mTLS.
# Output files are gitignored; only this script is tracked.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# CA
openssl genrsa -out "$DIR/ca.key" 4096
openssl req -new -x509 -days 3650 -key "$DIR/ca.key" \
  -out "$DIR/ca.crt" \
  -subj "/CN=hybrid-cloud-agents-ca/O=hybrid-cloud-agents"

# Server cert (public worker)
openssl genrsa -out "$DIR/server.key" 2048
openssl req -new -key "$DIR/server.key" \
  -out "$DIR/server.csr" \
  -subj "/CN=public-worker/O=hybrid-cloud-agents"
openssl x509 -req -days 365 \
  -in "$DIR/server.csr" \
  -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" -CAcreateserial \
  -out "$DIR/server.crt"

# Client cert (orchestrator)
openssl genrsa -out "$DIR/client.key" 2048
openssl req -new -key "$DIR/client.key" \
  -out "$DIR/client.csr" \
  -subj "/CN=orchestrator/O=hybrid-cloud-agents"
openssl x509 -req -days 365 \
  -in "$DIR/client.csr" \
  -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" -CAcreateserial \
  -out "$DIR/client.crt"

rm -f "$DIR"/*.csr "$DIR"/*.srl
echo "Certificates generated in $DIR/"
