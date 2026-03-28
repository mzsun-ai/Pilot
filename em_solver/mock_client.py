"""Fallback when openEMS is not installed: analytic-ish S11 curve + plots (not FDTD)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pilot.logging_utils import get_logger
from pilot.schema import SimulationTaskSpec

_LOG = get_logger("em_solver.mock_client")


def run_openems_mock(spec: SimulationTaskSpec, run_dir: Path) -> dict:
    """
    Produce s11.csv / s11.png without openEMS.
    Uses a simple resonant dip model around f0 (demo / CI only).
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    f0 = spec.frequency.center_ghz
    span = 0.15 * f0
    freqs = np.linspace(max(0.5, f0 - span), f0 + span, 400)
    # Lorentzian-shaped |S11| in linear, then dB
    q = 80.0
    x = (freqs - f0) / (f0 / (2 * q))
    gamma = 0.08
    lin = np.sqrt(gamma**2 + x**2) / np.sqrt(1 + x**2) * 0.25 + 0.02
    s11_db = 20 * np.log10(np.maximum(lin, 1e-6))

    csv_path = run_dir / "s11.csv"
    hdr = "freq_ghz,s11_db"
    np.savetxt(csv_path, np.column_stack([freqs, s11_db]), delimiter=",", header=hdr, comments="")

    fig, ax = plt.subplots(figsize=(7, 4), tight_layout=True)
    ax.plot(freqs, s11_db, "b-", lw=2)
    ax.grid(True)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("S11 (dB)")
    ax.set_title("Return loss (mock — no openEMS FDTD)")
    png_path = run_dir / "s11.png"
    fig.savefig(png_path, dpi=120)

    i_min = int(np.argmin(s11_db))
    meta = {
        "solver": "mock_lorentzian",
        "note": "Install openEMS + python3-openems (e.g. apt) for real FDTD.",
        "mock_resonance_ghz": float(freqs[i_min]),
        "mock_min_s11_db": float(s11_db[i_min]),
    }
    (run_dir / "mock_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _LOG.warning("openEMS unavailable — wrote mock S11 to %s", csv_path)
    return {
        "export_paths": [str(csv_path), str(png_path)],
        "raw_metrics": meta,
        "subprocess_stderr": "",
    }
