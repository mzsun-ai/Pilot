# Surrogate pillar (model registry)

## Purpose

A **lightweight registry** for surrogate / ML models used in EM workflows: metadata, bilingual titles/descriptions, tags, paper and code links, optional **artifact bundles** (e.g. weights, ONNX, README).

## Data

- Canonical file: `data/surrogates_catalog.json`
- Shape: `{ "items": [ { ... } ] }` — each item at minimum has `id` (slug); registration accepts extended fields via Pydantic model in `pilot/platform/api_models.py`.

## HTTP

- `GET /api/v1/surrogates/list` — full catalog.
- `POST /api/v1/surrogates/register` — JSON body; optional header `X-Pilot-Register-Key` if `surrogate.admin_register_key` set in config.
- `POST /api/v1/surrogates/upload-bundle` — multipart `surrogate_id` + file; stores under `outputs/surrogate_bundles/`.
- `GET /api/v1/surrogates/download/{surrogate_id}/{filename}` — download uploaded bundle file.

## Configuration

```yaml
surrogate:
  admin_register_key: ""   # if non-empty, required for register + upload-bundle
```

## UI

- Static page `web/static/surrogate.html` loads catalog via `GET .../list` and renders cards (including featured entry when present in JSON).

## Extension points (roadmap)

- **Schema version** per item for migrations.
- **Benchmark** block (latency, accuracy vs FDTD).
- **Inference adapter** protocol (local callable name + env) — stub only in 1.x.
- **Agent integration**: resolve surrogate by tag from NL or task spec metadata.

## Security note

- Register and bundle upload are **admin** operations when key is set; list/download may remain open for lab intranets — tighten per deployment.
