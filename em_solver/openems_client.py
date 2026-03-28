"""Detect openEMS + CSXCAD and execute generated simulation scripts."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pilot.logging_utils import get_logger

_LOG = get_logger("em_solver.openems_client")

PROBE_CODE = (
    "from CSXCAD import ContinuousStructure; "
    "from openEMS import openEMS; "
    "from openEMS.physical_constants import C0"
)


def probe_openems_python(exe: Optional[str] = None) -> tuple[bool, str, str]:
    """
    Return (ok, python_executable, message).
    Tries: given exe, sys.executable, then common `python3`.
    """
    candidates: list[str] = []
    if exe:
        candidates.append(exe)
    candidates.append(sys.executable)
    p3 = shutil.which("python3")
    if p3 and p3 not in candidates:
        candidates.append(p3)

    for py in candidates:
        if not py:
            continue
        try:
            r = subprocess.run(
                [py, "-c", PROBE_CODE],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode == 0:
                return True, py, f"openEMS Python API available via {py}"
        except (OSError, subprocess.TimeoutExpired) as e:
            _LOG.debug("probe failed for %s: %s", py, e)
            continue
    return False, sys.executable, "openEMS/CSXCAD Python modules not importable"


@dataclass
class OpenEMSRunResult:
    returncode: int
    stdout: str
    stderr: str
    script_path: Path


def run_generated_script(
    script_path: Path,
    *,
    python_exe: str,
    cwd: Optional[Path] = None,
    timeout_sec: int = 900,
) -> OpenEMSRunResult:
    script_path = script_path.resolve()
    cwd = cwd or script_path.parent
    _LOG.info("Running openEMS driver: %s (python=%s)", script_path, python_exe)
    proc = subprocess.run(
        [python_exe, str(script_path)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    _LOG.info("openEMS subprocess finished rc=%s", proc.returncode)
    if proc.stdout:
        _LOG.debug("stdout:\n%s", proc.stdout[:4000])
    if proc.stderr:
        _LOG.debug("stderr:\n%s", proc.stderr[:4000])
    return OpenEMSRunResult(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        script_path=script_path,
    )
