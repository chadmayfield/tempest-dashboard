# tempest-dashboard

## Project Overview
Lightweight, self-contained HTML dashboard for visualizing weather data from tempestd. Vanilla JS with ES modules, Chart.js for charting, no build step. Served as static files.

## Architecture
- **No framework** — vanilla HTML/CSS/JS with ES modules (`import`/`export`)
- **No build step** — serve directly with nginx or `python3 -m http.server`
- **Data source** — tempestd REST API (`/api/v1/...`), no direct DB access
- **Charting** — Chart.js 4.x from CDN with zoom plugin
- **Plugin system** — ES modules loaded at runtime via `plugins.json`

## Directory Structure
```
index.html          # Page structure, CDN script tags
manifest.json       # PWA manifest
sw.js               # Service worker
plugins.json        # Plugin manifest (empty array in core repo)
css/style.css       # CSS custom properties, grid layout, responsive, dark/light
js/config.js        # Server URL resolution, defaults, color palette
js/state.js         # Simple event emitter (~40 lines)
js/api.js           # tempestd REST API client
js/current.js       # Current conditions card rendering
js/controls.js      # Station selector, time range, unit toggle
js/charts.js        # Chart.js instance creation and update
js/plugins.js       # Plugin loader and lifecycle management
js/app.js           # Main entry: init, polling, event wiring
icons/              # PWA icons and favicon
```

## Key Conventions
- **Security first**: Never use innerHTML with API data. Use textContent / DOM APIs.
- **CSS custom properties**: All colors/spacing are CSS variables. Charts read colors from CSS.
- **No secrets in frontend**: Server URLs are not secrets. No API keys or tokens.
- **Plugin trust model**: Plugins execute with full page privileges. Only load from trusted sources.

## Development
```bash
python3 -m http.server 8000
# Open http://localhost:8000?server=http://localhost:8080
```

## tempestd API Reference
- `GET /api/v1/health` — health check
- `GET /api/v1/stations` — list stations
- `GET /api/v1/stations/{id}/current?units=metric|imperial` — latest observation
- `GET /api/v1/stations/{id}/observations?start=...&end=...&resolution=1m|5m|30m|1h|3h&units=...` — historical data
- `GET /api/v1/stations/{id}/summary?date=YYYY-MM-DD&units=...` — daily summary
- `GET /api/v1/stations/{id}/range` — oldest/newest timestamps

## Resolution Mapping
| Time Range | Resolution | ~Data Points |
|------------|-----------|-------------|
| ≤6h        | 1m        | ≤360        |
| 24h        | 5m        | 288         |
| 7d         | 30m       | 336         |
| 30d        | 1h        | 720         |
| 90d        | 3h        | 720         |

## Working Style

- NEVER tag/release without end-to-end testing first — build, run against live service, verify output
- When told to verify: STOP changing code. Read source, trace paths, confirm with evidence. Only then propose a fix
- Trace code paths step by step through actual source — don't guess what functions do
- Verify claims through multiple independent means before presenting them as fact
- Separate investigation from implementation — understand the full problem before proposing a fix