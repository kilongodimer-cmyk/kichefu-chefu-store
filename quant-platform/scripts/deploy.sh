#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.prod.yml}"

cd "$APP_DIR"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file '$COMPOSE_FILE' introuvable" >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch "$GIT_REMOTE" "$GIT_BRANCH"
  git checkout "$GIT_BRANCH"
  git pull --ff-only "$GIT_REMOTE" "$GIT_BRANCH"
fi

docker compose -f "$COMPOSE_FILE" pull

docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# Ensure database schema is up to date
docker compose -f "$COMPOSE_FILE" run --rm api python -m app.db.migrate

docker image prune -f --filter "dangling=true" >/dev/null 2>&1 || true
