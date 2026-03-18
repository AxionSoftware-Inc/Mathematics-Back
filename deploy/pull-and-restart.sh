#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONT_ROOT="$(cd "${BACKEND_ROOT}/../../Math-Front" && pwd)"

git -C "${BACKEND_ROOT}" pull --ff-only
git -C "${FRONT_ROOT}" pull --ff-only

docker compose --env-file "${SCRIPT_DIR}/.env.production" -f "${SCRIPT_DIR}/docker-compose.prod.yml" up -d --build
