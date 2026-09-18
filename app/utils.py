"""
utils.py - Shared utilities: logging, helpers.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Project root & data directory ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / "vocadesk.log"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to both console and file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (DEBUG and above)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


def format_time(dt: datetime | None = None) -> str:
    """Return human-readable 12-hour time string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%I:%M %p").lstrip("0")


def format_date(dt: datetime | None = None) -> str:
    """Return human-readable date string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%A, %B %d, %Y")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
