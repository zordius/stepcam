import numpy as np

from stepcam.config import Config
from stepcam.pipeline import Pipeline

SIZE = 300
# the whole 300x300 frame is the grid, so image coords == ground coords
CORNERS = [(0, SIZE), (SIZE, SIZE), (SIZE, 0), (0, 0)]


def scene(foot=None):
    frame = np.full((SIZE, SIZE, 3), 80, np.uint8)
    if foot:
        x, bottom = foot
        frame[0:bottom, x - 10 : x + 10] = 255  # a "leg" ending at the contact point
    return frame


def make_pipeline():
    pipe = Pipeline(Config(corners=CORNERS, debounce=2))
    pipe.fg.begin_background(3)
    for _ in range(3):
        pipe.fg.feed(scene())
    return pipe


def test_ready_needs_corners_and_background():
    assert not Pipeline(Config()).ready
    assert make_pipeline().ready


def test_foot_in_up_cell_presses_then_releases():
    pipe = make_pipeline()
    assert pipe.process(scene((150, 40))).events == []
    assert pipe.process(scene((150, 40))).events == [("up", True)]
    assert pipe.process(scene()).events == [("up", False)]


def test_foot_in_center_does_nothing():
    pipe = make_pipeline()
    for _ in range(3):
        assert pipe.process(scene((150, 150))).events == []


def test_feet_report_image_and_ground_points():
    pipe = make_pipeline()
    res = pipe.process(scene((150, 40)))
    assert len(res.feet) == 1
    assert res.feet[0].ground == res.feet[0].image or all(
        abs(a - b) < 1e-3 for a, b in zip(res.feet[0].ground, res.feet[0].image)
    )
