#!/usr/bin/env python3
"""Pilot CLI: natural language -> openEMS FDTD workflow (with mock fallback)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure package imports when run as script from project root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pilot.logging_utils import setup_logging
from pilot.utils import load_config
from pilot.workflow import run_pilot_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Pilot — free EM agent (openEMS)")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help='Natural language request, e.g. "Design a 2.4 GHz patch on FR4..."',
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "config.yaml",
        help="Path to YAML config",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root (default: directory containing main.py)",
    )
    args = parser.parse_args()

    cfg_path = args.config.resolve()
    root = args.root.resolve()
    config = load_config(cfg_path)
    log_cfg = config.get("logging", {})
    log_dir = root / config.get("paths", {}).get("logs_dir", "logs")
    setup_logging(log_dir, level=log_cfg.get("level", "INFO"), file_name=log_cfg.get("file_name", "pilot_run.log"))

    out = run_pilot_pipeline(args.query, config=config, root=root)
    print(out.get("report_markdown", ""))
    print(
        f"\n---\nArtifacts:\n"
        f"  task_spec: {out.get('task_spec_path')}\n"
        f"  report: {out.get('report_path')}\n"
        f"  script: {out.get('generated_script')}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
