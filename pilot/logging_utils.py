"""Logging setup for Pilot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Path,
    level: str = "INFO",
    file_name: str = "pilot_run.log",
) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / file_name

    root = logging.getLogger("pilot")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    root.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    root.addHandler(sh)

    for sub in ("em_solver", "hfss"):
        logging.getLogger(sub).handlers = []
        logging.getLogger(sub).setLevel(root.level)
        logging.getLogger(sub).addHandler(fh)
        logging.getLogger(sub).addHandler(sh)

    return log_path


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
