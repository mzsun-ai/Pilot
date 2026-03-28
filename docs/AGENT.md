# Agent pillar (simulation orchestration)

## Purpose

Turn **natural language** into a **structured EM simulation task**, generate an **openEMS-oriented driver script**, run **real FDTD** when available or **mock** S11 otherwise, and emit **reports + artifacts**.

## Code

| Piece | Role |
|-------|------|
| `pilot/parser.py` | NL → `SimulationTaskSpec` (rule-based MVP). |
| `pilot/planner.py` | Spec → `SimulationPlan` + task id. |
| `pilot/workflow.py` | Full pipeline + state machine transitions; non-blocking **validator** (frequency / geometry warnings) and **`pipeline_trace`** returned to the API. |
| `pilot/state_machine.py` | Workflow states for logging / future UI. |
| `em_solver/openems_builder.py` | CSXCAD/openEMS Python script generation. |
| `em_solver/openems_client.py` | Subprocess execution, probe Python with openEMS. |
| `em_solver/mock_client.py` | Deterministic fallback curve. |
| `em_solver/results_extractor.py` | S11 CSV analysis. |
| `pilot/reporter.py` | Markdown report text. |

## HTTP

- `POST /api/v1/simulations` — body `{"query": "..."}`; JSON response includes `pipeline_trace` (stages: parse, plan, validate, generate, execute, report).
- `GET /api/v1/artifacts/{task_id}/{filename}` — `s11.png`, `s11.csv`, `run_openems_patch.py`, `mock_meta.json`.

## Outputs (per run)

- `outputs/task_specs/{uuid}_task_spec.json`, `_plan.json`
- `outputs/openems_runs/{uuid}/` — script, workspace, csv, png
- `outputs/reports/{uuid}_report.md`, `_summary.json`

## Configuration (`em_solver` + `parser` in YAML)

- `mode`: `auto` \| `openems` \| `mock`
- `timeout_sec`, `python_exe`
- Parser defaults: εᵣ, loss tangent, substrate thickness

## Extension points (roadmap)

- **Validator**: today emits **warnings** only; optional hard-fail / repair loops later.
- **LLM-assisted** parse behind feature flag with JSON schema validation.
- **Trace**: stage list shipped in API; add timings and solver stderr excerpts later.
- **Plugin** embedding: same functions callable without FastAPI.

## Failure behavior

- openEMS failure → logged → mock fallback where configured.
- Parser / plan failure → exception surfaced to API as `ok: false` with `error` string (web) or raised (CLI).
