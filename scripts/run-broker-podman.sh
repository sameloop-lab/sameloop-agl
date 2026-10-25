#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec podman run --rm --name sameloop-kuksa \
  -p "127.0.0.1:${SAMELOOP_PORT:-55555}:55555" \
  -v "$project_root/config:/sameloop:ro,Z" \
  ghcr.io/eclipse-kuksa/kuksa-databroker:0.7.1 \
  --address 0.0.0.0 --port 55555 --insecure --disable-authorization --vss /sameloop/vss.json
