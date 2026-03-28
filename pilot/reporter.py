"""Generate final human-readable reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pilot.schema import SimulationPlan, SimulationResults, SimulationTaskSpec


def build_markdown_report(
    spec: SimulationTaskSpec,
    plan: SimulationPlan,
    results: SimulationResults,
) -> str:
    lines = [
        "# Pilot EM Simulation Report (openEMS stack)",
        "",
        f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Task",
        "",
        f"- **Raw query:** {spec.raw_query}",
        f"- **Structure:** {spec.structure_type.value}",
        f"- **Material:** {spec.material.name} (εr={spec.material.relative_permittivity}, tanδ={spec.material.loss_tangent})",
        f"- **Target frequency:** {spec.frequency.center_ghz} GHz",
        f"- **S11 constraint (parsed):** ≤ {spec.performance.s11_max_db} dB",
        "",
        "### Geometry hints",
        "",
        f"- Substrate thickness: {spec.geometry.substrate_thickness_mm} mm",
        f"- Patch L × W (initial): {spec.geometry.patch_length_mm} × {spec.geometry.patch_width_mm} mm",
        f"- Ground plane (hint): {spec.geometry.ground_plane_mm} mm",
        "",
        "## Plan",
        "",
        f"- **Task ID:** `{plan.task_id}`",
        "",
    ]
    for i, step in enumerate(plan.steps, 1):
        lines.append(f"{i}. **{step.name}** — {step.description} (`{step.tool}`)")
    lines.extend(
        [
            "",
            "## Results",
            "",
            f"- **Mode:** `{results.mode}` (solver: `{results.solver}`)",
            f"- **Resonance (estimated from S11 curve):** {results.resonance_ghz} GHz",
            f"- **S11 near target freq:** {results.s11_at_target_db} dB",
            f"- **Peak gain:** {results.peak_gain_dbi if results.peak_gain_dbi is not None else '_(not computed in MVP)_'}",
            "",
        ]
    )
    if results.generated_script:
        lines.append(f"- **Generated openEMS script:** `{results.generated_script}`")
    if results.openems_python:
        lines.append(f"- **Python used for openEMS:** `{results.openems_python}`")
    lines.extend(["", "### Exports", ""])
    if results.export_paths:
        for p in results.export_paths:
            lines.append(f"- `{p}`")
    else:
        lines.append("- _(none)_")
    lines.extend(["", "## Notes from parser", ""])
    if spec.notes:
        for n in spec.notes:
            lines.append(f"- {n}")
    else:
        lines.append("- _(none)_")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "**Solver:** open-source **openEMS** (FDTD). "
        "If `mode` is `mock`, CSXCAD/openEMS Python bindings were not available or the run failed — "
        "install `openems` and `python3-openems` (Debian/Ubuntu) or build from "
        "[thliebig/openEMS](https://github.com/thliebig/openEMS), then re-run with `em_solver.mode: auto`."
    )
    return "\n".join(lines)


def save_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
