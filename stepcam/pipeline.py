"""Frame in, key events out. No camera or GUI here, so it is testable."""
from dataclasses import dataclass, field

import numpy as np

from .detect import Foreground, find_feet
from .geometry import homography, project
from .zones import ZoneTracker


@dataclass
class Foot:
    image: tuple  # lowest point in the camera image
    ground: tuple  # same point in ground coords (0..GRID)
    zone: str = None  # active zone it is in, if any


@dataclass
class Result:
    mask: np.ndarray = None
    feet: list = field(default_factory=list)
    events: list = field(default_factory=list)


class Pipeline:
    def __init__(self, cfg):
        self.cfg = cfg
        self.fg = Foreground()
        self.tracker = ZoneTracker(cfg)
        self.H = None
        self.Hinv = None
        self.set_corners(cfg.corners)

    def set_corners(self, corners):
        if len(corners) == 4:
            self.cfg.corners = [list(map(float, c)) for c in corners]
            self.H = homography(self.cfg.corners)
            self.Hinv = np.linalg.inv(self.H)

    @property
    def ready(self):
        return self.H is not None and self.fg.has_background

    def process(self, frame):
        mask = self.fg.mask(frame, self.cfg.diff_thresh)
        image_pts = find_feet(mask)
        ground_pts = project(self.H, image_pts)
        events = self.tracker.update(ground_pts)
        feet = [Foot(i, g, self.tracker.zone_of(g)) for i, g in zip(image_pts, ground_pts)]
        return Result(mask, feet, events)
