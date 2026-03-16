# Quantitative Trading Platform

Modular fullstack system for low-latency crypto trading with AI-driven signals, built around:

- **Backend**: FastAPI, CCXT Pro, Redis, PostgreSQL.
- **AI**: Scikit-learn RandomForest pipeline with feature engineering (RSI, MACD, Bollinger).
- **Frontend**: React + Vite + TailwindCSS + Lightweight Charts.
- **Infra**: Docker, docker-compose, Nginx reverse proxy, GitHub Actions, DigitalOcean droplet.

## Repository Layout

```
quant-platform/
  services/
    backend/        # FastAPI app & workers
    frontend/       # React/Vite terminal
  infra/            # docker-compose, nginx, env templates
  .github/workflows # CI/CD pipelines
  docs/             # architecture notes, runbooks
```

See `docs/quant_platform_architecture.md` for a detailed overview. Run `make dev` (todo) to start all services locally once dependencies are installed.

## Quickstart

1. **Backend**
   - `cd services/backend`
   - Create `.env` or use `infra/env/backend.env` template (set `POSTGRES_DSN`, Binance keys, etc.).
   - Install deps: `pip install -e .[dev]`
   - Start API: `uvicorn app.main:app --reload`

2. **Frontend**
   - `cd services/frontend/terminal`
   - Copy `.env` from `infra/env/frontend.env`
   - Install deps: `npm install` (required to resolve current TypeScript complaints about missing `vite`/`react` types)
   - `npm run dev`

3. **Infra (local)**
   - `cd infra`
   - Copy env templates from `infra/env/*.env`
   - `docker compose -f docker-compose.dev.yml up --build`

4. **Prod deploy (preview)**
   - Build Docker images for `api`, `worker`, `frontend`
   - Push to GHCR and use `docker-compose.prod.yml` on DigitalOcean droplet (with Nginx + TLS)

## Development Notes

- The React terminal currently simule un flux temps réel via `setInterval` + Zustand (`useTerminalStore`). Le bouton **Panic Sell** déclenche `panicSell()` (coupe les signaux, met `halted=true`, remet l’utilisation à 0) et le badge LIVE/PAUSE dans `SignalFeed` reflète cet état.
- Pour lever les erreurs TypeScript « Cannot find module 'react' / 'vite/client' / 'lucide-react' / 'zustand' », exécutez :
  ```bash
  cd services/frontend/terminal
  npm install
  npm run dev
  ```
  (les lints actuels dans l’IDE disparaîtront après installation des dépendances du dossier Vite).
