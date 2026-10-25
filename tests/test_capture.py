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


def patch_cameras(monkeypatch, cams):
    monkeypatch.setattr(capture, "_open", lambda index: cams[index] if index < len(cams) else FakeCap(opens=False))


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
