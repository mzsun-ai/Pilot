# Pilot REST API (industrial integration)

Stable, versioned HTTP API for MES/PLM/Lab automation, Python/C#/Java clients, or low-code tools.

**Repository:** [github.com/mzsun-ai/Pilot](https://github.com/mzsun-ai/Pilot)

## Base URL

Replace with your deployment host, e.g. `https://pilot.example.com`.

## Discovery

| Resource | Purpose |
|----------|---------|
| `GET /api/v1/health` | Liveness + service version |
| `GET /docs` | **Swagger UI** (try requests in browser) |
| `GET /redoc` | **ReDoc** (readable reference) |
| `GET /openapi.json` | **OpenAPI 3** machine-readable schema (import into Postman, Insomnia, code generators) |

## Endpoints

### `GET /api/v1/health`

```bash
curl -s https://YOUR_HOST/api/v1/health
```

Example response:

```json
{"status":"ok","service":"pilot","version":"0.2.0","api":"v1"}
```

### `POST /api/v1/simulations`

Submit a **natural-language** design/simulation request. Response is JSON (long-running; may take seconds to minutes if openEMS FDTD runs).

```bash
curl -s -X POST "https://YOUR_HOST/api/v1/simulations" \
  -H "Content-Type: application/json" \
  -d '{"query":"Design a 2.4 GHz rectangular patch antenna on FR4 and show return loss near resonance."}'
```

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `query` | string, 3–4000 chars | yes |

**Response** (`application/json`)

| Field | Meaning |
|-------|---------|
| `ok` | `true` if pipeline finished without exception |
| `task_id` | UUID for this run |
| `state` | Workflow state string (e.g. `done`) |
| `report_markdown` | Full human-readable report |
| `summary` | Structured metrics (S11, mode, solver, paths, …) |
| `artifact_urls` | Relative paths to `s11.png`, `s11.csv`, generated script |
| `error` | Present when `ok` is `false` |

**Artifacts** — prefix with your host:

- `GET /api/v1/artifacts/{task_id}/s11.png`
- `GET /api/v1/artifacts/{task_id}/s11.csv`
- `GET /api/v1/artifacts/{task_id}/run_openems_patch.py`

### Legacy (deprecated)

- `POST /api/run` — same as `/api/v1/simulations`
- `GET /api/artifact/{task_id}/{filename}` — use `/api/v1/artifacts/...` instead

## CORS

The server sends `Access-Control-Allow-Origin: *` so browser-based dashboards on other origins can call the API.

## Code generation from OpenAPI

```bash
curl -s https://YOUR_HOST/openapi.json -o pilot-openapi.json
# Then use openapi-generator, swagger-codegen, or FastAPI client generators.
```

## Security (production)

The MVP has **no authentication**. For industrial deployment, put the service behind:

- API gateway with API keys or mTLS  
- VPN / private network  
- Reverse proxy (nginx) + OAuth2 / JWT validation  

Future optional header: `Authorization: Bearer <token>` (not implemented in MVP).
