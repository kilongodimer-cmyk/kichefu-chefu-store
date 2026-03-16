# Frontend Terminal (React/Vite)

Planned stack:
- **React 18** via Vite template.
- **TypeScript** for stronger contracts with backend events.
- **TailwindCSS** configured in `dark` mode with custom palette.
- **Lightweight Charts** (TradingView) for candlesticks + overlays.
- **Lucide-react** for iconography.
- WebSocket client (native or socket.io) for streaming signals/logs.

## Scaffolding Steps
1. `npm create vite@latest terminal -- --template react-ts`
2. `cd terminal && npm install`
3. Add TailwindCSS: `npx tailwindcss init -p`
4. Configure `tailwind.config.js` with custom colors + `darkMode: 'class'`
5. Install deps: `npm i lightweight-charts lucide-react zustand socket.io-client`
6. Create layout components: `ChartPanel`, `SignalFeed`, `RiskPanel`, `ControlBar` (panic sell button).
7. Use `vite.config.ts` proxy to backend WS during dev.

Final tree under `services/frontend/terminal/` (todo).
