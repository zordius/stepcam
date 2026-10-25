"""Virtual 3x3 grid: only the four edge cells are active, everything else is idle."""
from .config import GRID

# (column, row) of each active cell; row 0 is the top edge of the clicked grid
ACTIVE = {"up": (1, 0), "down": (1, 2), "left": (0, 1), "right": (2, 1)}


def cell_rect(cell, grow=0.0):
    """Cell bounds (x0, y0, x1, y1) in ground coords, grown (or shrunk) by `grow` cells."""
    size = GRID / 3
    col, row = cell
    g = grow * size
    return (col * size - g, row * size - g, (col + 1) * size + g, (row + 1) * size + g)


def _inside(p, rect):
    return rect[0] <= p[0] <= rect[2] and rect[1] <= p[1] <= rect[3]


class ZoneTracker:
    """Turns foot ground points into press/release events per direction."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.pressed = {name: False for name in ACTIVE}
        self._count = {name: 0 for name in ACTIVE}

    def zone_of(self, point):
        """Active zone a point is in (pressed zones use the larger hold area)."""
        for name, cell in ACTIVE.items():
            grow = self.cfg.hold_margin if self.pressed[name] else -self.cfg.inset
            if _inside(point, cell_rect(cell, grow)):
                return name
        return None

    def update(self, points):
        """Feed this frame's ground points; return [(name, is_down), ...] events."""
        events = []
        for name, cell in ACTIVE.items():
            if self.pressed[name]:
                if not any(_inside(p, cell_rect(cell, self.cfg.hold_margin)) for p in points):
                    self.pressed[name] = False
                    self._count[name] = 0
                    events.append((name, False))
                continue
            enter = cell_rect(cell, -self.cfg.inset)
            self._count[name] = self._count[name] + 1 if any(_inside(p, enter) for p in points) else 0
            if self._count[name] >= self.cfg.debounce:
                self.pressed[name] = True
                events.append((name, True))
        return events
