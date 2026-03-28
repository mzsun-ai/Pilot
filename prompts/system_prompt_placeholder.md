# Pilot — LLM system prompt (placeholder)

Future versions can replace the rule-based `pilot/parser.py` with an LLM that emits **strict JSON**
matching `SimulationTaskSpec` (Pydantic in `pilot/schema.py`).

The downstream solver is **openEMS** (free FDTD). The agent should not mention HFSS/AEDT.

Required JSON fields for the narrow MVP:

- `structure_type` (e.g. `rectangular_patch`)
- `material.relative_permittivity`, `material.loss_tangent`, `material.name`
- `frequency.center_ghz`
- `performance.s11_max_db` (default -10 if omitted)

Wire-up: `SimulationTaskSpec.model_validate_json(...)`.
