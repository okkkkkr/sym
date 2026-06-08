#!/usr/bin/env bash
set -euo pipefail

APP_ROOT=${APP_ROOT:-/opt/sym}
PYTHON_BIN=${PYTHON_BIN:-$APP_ROOT/.venv/bin/python}
PIP_BIN=${PIP_BIN:-$APP_ROOT/.venv/bin/pip}
COREPACK_BIN=${COREPACK_BIN:-corepack}

cd "$APP_ROOT"

git pull

if [[ -x "$PIP_BIN" ]]; then
  "$PIP_BIN" install -r requirements.txt
fi

"$COREPACK_BIN" enable
"$COREPACK_BIN" prepare pnpm@9.15.9 --activate

(
  cd web
  pnpm install --frozen-lockfile
  pnpm build
)

(
  cd official-web
  pnpm install --frozen-lockfile
  pnpm build
)

sudo systemctl restart sym-api sym-celery-worker sym-celery-beat

if [[ "${1:-}" == "--reload-nginx" ]]; then
  sudo systemctl reload nginx
fi
