# Pilot

**Pilot** is an open-source **electromagnetic simulation assistant**: you describe an antenna in natural language, it builds a structured task, generates an **openEMS** (FDTD) Python script, runs **real openEMS** when available (or a documented **mock** fallback), and produces reports and S11 plots. Includes a **bilingual (EN / 中文) web UI**.

- **License:** [MIT](LICENSE)  
- **No HFSS, AEDT, or paid solvers** — uses [openEMS](https://github.com/thliebig/openEMS) only.

**Publish this repo to GitHub:** see [docs/PUBLISH_TO_GITHUB.md](docs/PUBLISH_TO_GITHUB.md) (create `Pilot`, push, and how to host the web app — GitHub Pages alone cannot run the API; use Docker on Render/Fly/etc.).

## Quick start (CLI)

```bash
conda activate Pilot
cd /home/mingze/Pilot
pip install -r requirements.txt
python main.py --query "Design a 2.4 GHz rectangular patch antenna on FR4 and show me the return loss near resonance."
```

If **openEMS + CSXCAD** are installed (see below or `deps/BUILD.md` for building into conda), `em_solver.mode: auto` runs **real FDTD**.

## Web UI

```bash
conda activate Pilot
cd /home/mingze/Pilot
pip install -r requirements.txt
uvicorn web.app:app --host 0.0.0.0 --port 8765
```

Open `http://127.0.0.1:8765/` — use **EN / 中文** in the header. **REST API:** `POST /api/v1/simulations` with JSON `{"query":"..."}` (see [docs/API.md](docs/API.md); legacy `POST /api/run` still works).

**Public URL:** serve with any host that runs Python (see `Dockerfile` for a minimal deploy; full openEMS in Docker requires a custom image — see `deps/BUILD.md`).

## Docker (demo / mock-friendly)

```bash
docker build -t pilot-web .
docker run -p 8765:8765 pilot-web
```

## Outputs (per run)

- `outputs/task_specs/<task_id>_task_spec.json` — structured spec  
- `outputs/task_specs/<task_id>_plan.json` — plan steps  
- `outputs/openems_runs/<task_id>/run_openems_patch.py` — generated openEMS driver  
- `outputs/openems_runs/<task_id>/openems_workspace/` — FDTD workspace when openEMS runs  
- `outputs/openems_runs/<task_id>/s11.csv`, `s11.png`  
- `outputs/reports/<task_id>_report.md`, `_summary.json`  
- `logs/`

## Installing openEMS (Linux)

```bash
sudo apt-get install openems python3-openems
```

Then in `configs/config.yaml`:

```yaml
em_solver:
  python_exe: "/usr/bin/python3"
```

Or build from source into conda: **`deps/BUILD.md`** (local clones live in `deps/src/`, not committed).

## Configuration

| Key | Meaning |
|-----|---------|
| `em_solver.mode` | `auto` \| `openems` \| `mock` |
| `em_solver.timeout_sec` | Subprocess time limit for FDTD |
| `em_solver.python_exe` | Optional Python with openEMS |

## Tests

```bash
pytest -q
```

## Reference

Generated geometry follows the upstream tutorial `Simple_Patch_Antenna.py` from [thliebig/openEMS](https://github.com/thliebig/openEMS). See `examples/openems_reference_Simple_Patch_Antenna.py`.

## Limitations (MVP)

- Rule-based NL parser; LLM + JSON schema is planned (`prompts/`).  
- Heuristic patch sizing; no automatic optimization.  
- Default script focuses on S11 (no NF2FF / gain) to keep runtime down.
