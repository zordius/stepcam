"""Persisted settings: calibration corners and tuning knobs."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

GRID = 300  # side length of the top-down ground view; one cell is GRID / 3


@dataclass
class Config:
    corners: list = field(default_factory=list)  # image points: BL, BR, TR, TL
    diff_thresh: int = 30  # background-difference threshold (0-255)
    inset: float = 0.15  # shrink active cells by this fraction of a cell per side
    hold_margin: float = 0.10  # grow active cells by this fraction while pressed
    debounce: int = 2  # frames a foot must stay in a zone before it presses


def load(path):
    p = Path(path)
    if not p.exists():
        return Config()
    known = Config.__dataclass_fields__
    return Config(**{k: v for k, v in json.loads(p.read_text()).items() if k in known})


def save(cfg, path):
    Path(path).write_text(json.dumps(asdict(cfg), indent=2) + "\n")
