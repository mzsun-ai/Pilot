"""Extract resonance / S11 metrics from Pilot-openEMS CSV output."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np

from pilot.logging_utils import get_logger

_LOG = get_logger("em_solver.results_extractor")


def load_s11_csv(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data[:, 0], data[:, 1]


def summarize_s11(
    csv_path: Path,
    target_ghz: Optional[float] = None,
) -> dict[str, Any]:
    if not csv_path.exists():
        return {}
    f_ghz, s11_db = load_s11_csv(csv_path)
    i_min = int(np.argmin(s11_db))
    out: dict[str, Any] = {
        "min_s11_db": float(s11_db[i_min]),
        "at_ghz": float(f_ghz[i_min]),
        "rows": int(len(f_ghz)),
    }
    if target_ghz is not None:
        idx = int(np.argmin(np.abs(f_ghz - target_ghz)))
        out["s11_at_target_db"] = float(s11_db[idx])
    _LOG.info("S11 summary %s: %s", csv_path, out)
    return out
