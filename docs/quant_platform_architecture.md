---
title: Quant Trading Platform Architecture Overview
created: 2026-03-16
---

## 1. Vision & High-Level Modules

> _Résumé_: cette section fixe l'intention générale de la plateforme. Les puces ci-dessous servent de contrat d'architecture rapide pour les nouveaux contributeurs.

A modular, low-latency trading stack with clear separation of concerns:

1. **Market Data Engine (FastAPI service + CCXT Pro)**
   - Maintains live WebSocket subscriptions (Binance spot/futures) with automatic resubscription.
   - Normalizes ticker, order book, and trade streams into a unified schema.
   - Publishes snapshots + deltas into Redis streams for consumers.

2. **Strategy & AI Service (FastAPI worker pool)**
   - Consumes market snapshots from Redis, computes indicators (RSI, MACD, Bollinger) with Pandas/NumPy.
   - Runs RandomForestClassifier (scikit-learn) on rolling feature windows to emit a confidence score [0,1].
   - Emits trade signals + metadata into PostgreSQL (historical log) and Redis (for execution + UI).

3. **Risk & Execution Engine**
   - Enforces capital allocation: max 2% equity per trade, daily loss guard, dynamic position sizing.
   - Calculates stop-loss & take-profit levels before order placement; attaches to orders via Binance OCO when possible.
   - Handles order management lifecycle (open, partial fill, cancel, panic-sell) with idempotent logic.

4. **Real-Time Frontend Terminal (React/Vite + Tailwind + Lightweight Charts)**
   - Dark-only UI showing candlesticks, open positions, executed orders, AI log stream.
   - Live WebSocket feed (socket.io or native WS) from backend gateway.
   - Manual controls: Panic Sell, pause bot, adjust thresholds.

5. **Infrastructure Layer**
   - Dockerized services orchestrated with docker-compose (backend, frontend, Postgres, Redis, Nginx).
   - Deployed on DigitalOcean droplet (>= 2 vCPU, 2GB RAM) with static IP whitelisted in Binance portal.
   - GitHub Actions pipeline builds/pushes images to GHCR, triggers remote deploy via SSH.

## 2. Data Flow

> _Intention_: visualiser le flux temps réel du tick vers l'exécution, pour évaluer facilement les points de latence ou SPOF.

```text
Binance WS -> Market Data Service -> Redis Streams ->
  a) Strategy/AI workers -> Signals -> Postgres + Redis (signals channel)
  b) Execution Engine <- Signals + Risk checks -> Binance REST/WS

Postgres -> historical analytics, dashboards
Redis -> low-latency cache for frontend + inter-service pub/sub
```

- **Redis Keys** _(pense-bête pour l'équipe ops)_
  - `md:orderbook:<symbol>`: latest depth snapshot (expire 2s)
  - `md:trades:<symbol>`: capped list of recent trades
  - `signals:live`: stream of strategy outputs
  - `risk:status`: daily loss, equity, flags
- **Postgres Tables** (minimum) — à compléter lors de la phase d'alembic initiale.
  - `trades`, `orders`, `signals`, `risk_events`, `model_versions`

## 3. Service Contracts

> _Pourquoi_: clarifier les endpoints exposés pour que chaque squad sache comment intégrer ses micro-services.

| Service | API / Events | Notes |
| --- | --- | --- |
| Market Data | `GET /health`, `WS /stream` (for mirroring) | Runs independently; restarts auto-subscribe |
| Strategy | `POST /backtest`, `POST /train`, `WS /signals` | Training jobs run offline; model artifact stored in S3-compatible bucket |
| Execution | `POST /orders`, `POST /panic-sell`, `GET /positions` | Requires Binance API keys via env + KMS/DO secrets |
| Frontend Gateway | `WS /terminal`, `GET /metrics` | Aggregates data for UI, proxies panic sell |

## 4. Deployment Blueprint

> _Objectif_: normaliser le socle infra (Docker/compose + CI/CD) avant de brancher la logique métier.

1. **Docker Images**
   - `backend-core`: FastAPI app exposing `/md`, `/strategy`, `/risk` routers; uvicorn workers via gunicorn.
   - `frontend-terminal`: Node 20 + Vite build -> nginx static.
   - `tasks`: background worker image (Celery/Arq) for training + alerts.

2. **docker-compose.prod.yml**
   - Services: `api`, `worker`, `frontend`, `redis`, `postgres`, `nginx` (reverse proxy), `telemetry` (optional Loki/Promtail).
   - Networks: `internal` (services) + `edge` (nginx only).

3. **CI/CD (GitHub Actions)**
   - Lint & test (pytest, frontend unit tests).
   - Build/push Docker images with tags (`latest`, git SHA).
   - Deploy job runs `ssh do-droplet "docker compose pull && docker compose up -d"`.

4. **Observability & Alerts**
   - FastAPI + worker logs shipped to Loki/Vector.
   - Prometheus exporter for latency, fills, PnL, risk events.
   - Telegram bot integration: send alerts on errors, order fills, daily limit triggered.

## 5. Security & Compliance

> _Rappel_: la plateforme manipule des API keys et des ordres réels, la sécurité est donc un premier-class citizen.

- API keys stored in DO Secrets Manager; mounted as env vars at runtime.
- Nginx terminates TLS (Let's Encrypt certbot container) and only exposes frontend + limited backend endpoints.
- JWT-based auth for UI with role separation (admin vs view-only).
- Strict rate limiting + HMAC verification for webhook endpoints.
- Panic Sell endpoint requires hardware-backed TOTP confirmation.

## 6. Next Implementation Steps

> _Roadmap immédiate_: prioriser les briques critiques pour obtenir un MVP tradable en quelques sprints.

1. Scaffold repository structure:
   - `/services/backend` FastAPI app with modular routers.
   - `/services/frontend` React/Vite project with Tailwind + chart setup.
   - `/infra` Docker compose, nginx config, GH Actions workflow templates.
2. Implement market data ingestion (Binance testnet) and write to Redis.
3. Define Postgres schema + alembic migrations.
4. Build basic terminal UI showing live candles + signal log.
5. Integrate training pipeline + checkpoint storage.
6. Harden deployment (CI/CD, monitoring, alerts).
