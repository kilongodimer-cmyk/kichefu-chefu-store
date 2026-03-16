# Infrastructure

Planned assets for deployment on DigitalOcean droplet (Dockerized):

- `docker-compose.dev.yml`: local stack with FastAPI, frontend dev server, Redis, Postgres.
- `docker-compose.prod.yml`: production stack with built images, Nginx reverse proxy, certbot.
- `nginx/conf.d/default.conf`: reverse proxy rules (API, frontend, websockets).
- `env/` directory containing `backend.env`, `frontend.env`, `postgres.env`, `infra.env` templates (copy as needed).
- `scripts/deploy.sh`: SSH helper to pull/pull compose stack on droplet (idempotent, git-aware).

## CI/CD Outline
1. GitHub Actions workflow `ci.yml`: lint/test backend + frontend (ruff, mypy, pytest, npm build).
2. `deploy.yml`: on `main` push + manual dispatch -> build backend + frontend images, push to GHCR, SSH into droplet, `docker compose pull && docker compose up -d`.
3. Secrets required (configure in repo Settings → Secrets and variables → Actions):
   - `DO_HOST`: public IP of the droplet
   - `DO_USER`: SSH user (e.g. `root`)
   - `DO_SSH_KEY`: private key with deploy rights (multi-line string)
   - `DO_APP_PATH`: absolute path to app repo on server
   - Optional overrides: `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, etc. (passed via `.env` template files)

### Manual SSH deploy

```
ssh $DO_USER@$DO_HOST "APP_DIR=/opt/quant-platform ./scripts/deploy.sh"
```

Environment variables

- `APP_DIR`: repo path on the server (defaults to current dir)
- `GIT_BRANCH`: branch to deploy (defaults `main`)
- `COMPOSE_FILE`: compose stack path (defaults `infra/docker-compose.prod.yml`)

### Database migrations / bootstrap

- The backend ships with `pyproject` dependency on Alembic but, for now, schema creation relies on SQLAlchemy metadata.
- To (re)create tables locally or in CI:

```
cd services/backend
POSTGRES_DSN=postgresql+asyncpg://... python -m app.db.migrate
```

- Integrate this command into deployment (e.g., an SSH step after `docker compose up`) to guarantee schema drift is resolved.

## Monitoring & Alerts
- FastAPI exposes `/metrics` (Prometheus).
- Redis/DB metrics via exporters.
- Telegram bot integration from backend worker for critical events (order executed, daily limit hit, panic sell triggered).

Further files to implement once services are ready.
