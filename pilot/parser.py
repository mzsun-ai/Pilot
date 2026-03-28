"""Natural language -> SimulationTaskSpec (rule-based MVP)."""

from __future__ import annotations

import re
from typing import Optional

from pilot.schema import (
    FrequencyTarget,
    GeometryHints,
    MaterialSpec,
    PerformanceTarget,
    SimulationTaskSpec,
    StructureType,
)


_GHZ_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:GHz|ghz|Ghz)",
    re.IGNORECASE,
)
_S11_RE = re.compile(
    r"S11\s*[<>]=?\s*(-?\d+(?:\.\d+)?)\s*dB",
    re.IGNORECASE,
)
_S11_ALT_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*dB.*S11|S11.*(-?\d+(?:\.\d+)?)\s*dB",
    re.IGNORECASE,
)


def parse_natural_language(
    query: str,
    *,
    default_er: float = 4.4,
    default_tan_delta: float = 0.02,
    substrate_thickness_mm: float = 1.6,
) -> SimulationTaskSpec:
    """Heuristic parser for the narrow MVP (patch antenna, FR4, GHz, S11)."""
    q = query.strip()
    notes: list[str] = []

    # Frequency
    m = _GHZ_RE.search(q)
    if m:
        f0 = float(m.group(1))
    else:
        f0 = 2.4
        notes.append("No explicit GHz found; defaulting center frequency to 2.4 GHz.")

    # S11 target (user said S11 < -10 dB => threshold -10)
    s11_db: Optional[float] = None
    m2 = _S11_RE.search(q)
    if m2:
        s11_db = float(m2.group(1))
    else:
        m3 = _S11_ALT_RE.search(q)
        if m3:
            s11_db = float(next(g for g in m3.groups() if g is not None))

    if s11_db is None:
        s11_db = -10.0
        notes.append("No explicit S11 constraint; using S11_max = -10 dB.")

    # Material
    material_name = "FR4"
    er = default_er
    tan_d = default_tan_delta
    ql = q.lower()
    if "ro4350" in ql or "ro 4350" in ql:
        material_name = "RO4350B"
        er = 3.66
        tan_d = 0.004
        notes.append("Detected RO4350B-like mention; using typical eps_r/tan_d.")
    elif "fr4" in ql:
        material_name = "FR4"

    # Structure
    structure = StructureType.UNKNOWN
    if "patch" in ql and "antenna" in ql:
        structure = StructureType.RECTANGULAR_PATCH
    elif "patch" in ql:
        structure = StructureType.RECTANGULAR_PATCH
    if structure == StructureType.UNKNOWN:
        notes.append("Structure not clearly identified; assuming rectangular patch for demo workflow.")

    perf = PerformanceTarget(
        s11_max_db=s11_db,
        description=f"Require S11 <= {s11_db} dB near resonance (parsed heuristic).",
    )

    return SimulationTaskSpec(
        raw_query=q,
        structure_type=structure,
        material=MaterialSpec(
            name=material_name,
            relative_permittivity=er,
            loss_tangent=tan_d,
        ),
        frequency=FrequencyTarget(center_ghz=f0),
        performance=perf,
        geometry=GeometryHints(substrate_thickness_mm=substrate_thickness_mm),
        notes=notes,
        metadata={"parser": "rule_v1"},
    )
