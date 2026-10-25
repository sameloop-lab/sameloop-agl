#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec "${DATABROKER:-databroker}" --address 127.0.0.1 --port "${SAMELOOP_PORT:-55555}" \
  --insecure --disable-authorization --vss "$project_root/config/vss.json"
