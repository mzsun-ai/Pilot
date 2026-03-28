"""Build a simulation plan from a task spec."""

from __future__ import annotations

import uuid

from pilot.schema import PlanStep, SimulationPlan, SimulationTaskSpec


def _patch_initial_dimensions_mm(freq_ghz: float, er: float) -> tuple[float, float]:
    """Very rough closed-form starting point for rectangular patch (MVP only)."""
    # Effective permittivity (simplified microstrip-style placeholder; h/W assumed small)
    eps_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12) ** -0.5
    # c in mm/s
    c_mm_per_s = 299_792_458.0 * 1000.0
    f_hz = freq_ghz * 1e9
    # Classic approximate patch width (half-wave in air, scaled by eps_eff)
    w_mm = c_mm_per_s / (2.0 * f_hz * (eps_eff**0.5))
    # Length ~ half guided wavelength with empirical shortening
    l_mm = c_mm_per_s / (2.0 * f_hz * (eps_eff**0.5)) * 0.49
    return round(l_mm, 3), round(w_mm, 3)


def build_plan(spec: SimulationTaskSpec) -> SimulationPlan:
    task_id = str(uuid.uuid4())
    l_mm, w_mm = _patch_initial_dimensions_mm(
        spec.frequency.center_ghz,
        spec.material.relative_permittivity,
    )
    spec.geometry.patch_length_mm = l_mm
    spec.geometry.patch_width_mm = w_mm
    spec.geometry.ground_plane_mm = round(max(l_mm, w_mm) * 2.5, 3)

    steps = [
        PlanStep(
            name="spec",
            description="Structured task spec from natural language",
            tool="pilot.parser",
        ),
        PlanStep(
            name="generate_script",
            description="Emit openEMS Python driver (patch on layered substrate)",
            tool="em_solver.openems_builder.build_openems_patch_script",
        ),
        PlanStep(
            name="run_fdtd",
            description="Execute openEMS FDTD (or mock fallback if CSXCAD/openEMS missing)",
            tool="em_solver.openems_client.run_generated_script",
        ),
        PlanStep(
            name="extract",
            description="Parse s11.csv, estimate resonance and S11 at target frequency",
            tool="em_solver.results_extractor.summarize_s11",
        ),
        PlanStep(
            name="report",
            description="Write markdown report and summary JSON",
            tool="pilot.reporter",
        ),
    ]
    order = [s.name for s in steps]
    return SimulationPlan(task_id=task_id, steps=steps, estimated_order=order)
