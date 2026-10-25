import cv2

from stepcam.app import CORNER_NAMES, Ui


def click(ui, x, y):
    ui.on_mouse(cv2.EVENT_LBUTTONUP, x, y, 0, None)


def test_clicks_are_ignored_unless_calibrating():
    ui = Ui()
    click(ui, 1, 1)
    assert ui.clicks is None


def test_take_corners_waits_for_four_clicks():
    ui = Ui()
    ui.clicks = []
    for i in range(3):
        click(ui, i, i)
        assert ui.take_corners() is None
        assert len(ui.clicks) == i + 1 and len(ui.clicks) < len(CORNER_NAMES)


def test_take_corners_returns_all_four_and_leaves_click_mode():
    ui = Ui()
    ui.clicks = []
    for i in range(4):
        click(ui, i, 10 + i)
    assert ui.take_corners() == [(0, 10), (1, 11), (2, 12), (3, 13)]
    assert ui.clicks is None  # so the HUD never indexes CORNER_NAMES[4]
    assert ui.take_corners() is None


def test_extra_clicks_after_four_are_dropped():
    ui = Ui()
    ui.clicks = []
    for i in range(6):
        click(ui, i, i)
    assert len(ui.take_corners()) == 4
