import argparse

import pytest

from stepcam import app, devices


def args(source, tmp_path):
    return argparse.Namespace(
        source=source, config=str(tmp_path / "config.json"), exposure=None, auto_exposure=None,
        width=640, height=480, fps=60, mirror=False, keys=False, headless=True, seconds=1,
    )


def test_unmatched_source_exits_with_error_before_opening_anything(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(devices, "list_cameras", lambda: [(0, "FaceTime HD Camera")])

    def fail_if_opened(*a, **k):
        raise AssertionError("must not open a camera for an unmatched --source")

    monkeypatch.setattr(app, "Capture", fail_if_opened)
    with pytest.raises(SystemExit) as exit_info:
        app.run(args("logitech", tmp_path))
    assert exit_info.value.code not in (0, None)
    assert "logitech" in str(exit_info.value.code)
