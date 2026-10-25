from stepcam.config import Config
from stepcam.zones import ZoneTracker

UP = (150, 50)  # center of the top edge cell
LEFT = (50, 150)
CENTER = (150, 150)
CORNER = (50, 50)


def test_press_needs_debounce_frames():
    t = ZoneTracker(Config(debounce=2))
    assert t.update([UP]) == []
    assert t.update([UP]) == [("up", True)]
    assert t.update([UP]) == []


def test_release_when_foot_leaves():
    t = ZoneTracker(Config(debounce=1))
    t.update([UP])
    assert t.update([CENTER]) == [("up", False)]


def test_center_and_corners_are_idle():
    t = ZoneTracker(Config(debounce=1))
    assert t.update([CENTER, CORNER]) == []


def test_two_feet_two_directions():
    t = ZoneTracker(Config(debounce=1))
    events = t.update([UP, LEFT])
    assert sorted(events) == [("left", True), ("up", True)]


def test_hysteresis_keeps_press_just_outside_the_cell():
    cfg = Config(debounce=1, hold_margin=0.1)
    t = ZoneTracker(cfg)
    t.update([UP])
    edge = (150, 100 + 5)  # 5 units past the cell edge, inside the hold margin
    assert t.update([edge]) == []
    assert t.pressed["up"]


def test_inset_leaves_a_dead_gap_at_the_cell_edge():
    t = ZoneTracker(Config(debounce=1, inset=0.15))
    assert t.update([(150, 100 - 5)]) == []  # 5 units inside the edge, within the inset
