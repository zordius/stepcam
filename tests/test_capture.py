import pytest

from stepcam import capture


class FakeCap:
    def __init__(self, opens=True, frames=True):
        self._opens, self._frames = opens, frames

    def isOpened(self):
        return self._opens

    def read(self):
        return self._frames, None

    def release(self):
        pass


@pytest.fixture(autouse=True)
def no_real_camera_names(monkeypatch):
    monkeypatch.setattr(capture, "list_cameras", lambda: [])


def patch_cameras(monkeypatch, cams, opened=None):
    def fake_open(index):
        if opened is not None:
            opened.append(index)
        return cams[index] if index < len(cams) else FakeCap(opens=False)

    monkeypatch.setattr(capture, "_open", fake_open)


def test_skips_silent_cameras_until_one_delivers(monkeypatch):
    patch_cameras(monkeypatch, [FakeCap(frames=False), FakeCap(frames=False), FakeCap()])
    assert capture.find_camera(timeout=0.01) == 2


def test_skips_indexes_that_cannot_open(monkeypatch):
    patch_cameras(monkeypatch, [FakeCap(opens=False), FakeCap()])
    assert capture.find_camera(timeout=0.01) == 1


def test_raises_when_no_camera_delivers(monkeypatch):
    patch_cameras(monkeypatch, [FakeCap(frames=False)])
    with pytest.raises(RuntimeError):
        capture.find_camera(timeout=0.01)


def test_tries_real_cameras_before_virtual_and_iphone(monkeypatch):
    names = [(0, "iPhone Camera"), (1, "FaceTime HD Camera"), (2, "OBS Virtual Camera")]
    monkeypatch.setattr(capture, "list_cameras", lambda: names)
    opened = []
    patch_cameras(monkeypatch, [FakeCap(), FakeCap(frames=False), FakeCap(frames=False)], opened)
    assert capture.find_camera(timeout=0.01) == 0  # only the iPhone delivers, and it is tried last
    assert opened == [1, 2, 0]


def test_stops_at_the_first_working_camera(monkeypatch):
    names = [(0, "iPhone Camera"), (1, "FaceTime HD Camera"), (2, "OBS Virtual Camera")]
    monkeypatch.setattr(capture, "list_cameras", lambda: names)
    opened = []
    patch_cameras(monkeypatch, [FakeCap(), FakeCap(), FakeCap()], opened)
    assert capture.find_camera(timeout=0.01) == 1
    assert opened == [1]  # never touched the virtual camera or the iPhone
