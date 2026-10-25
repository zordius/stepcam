# stepcam

Webcam-based virtual dance pad: turns foot positions seen by a webcam into
arrow-key events, so open-source DDR simulators such as StepMania can be played
without a physical pad.

Status: early prototype.

## Design

- Fixed camera, manual exposure (no auto-exposure, to keep frame timing stable).
- Four clicked floor corners define a homography to a top-down view of the floor.
- The top-down view is split into a 3x3 virtual grid (no physical markers).
  Only the four edge cells (up / down / left / right) are active; the center,
  the corners and everything outside the grid are idle.
- Foot ground-contact point = lowest point of each foot blob, mapped through
  the homography.
- A realtime feedback view doubles as the debug view (zones, feet, fps,
  per-frame timestamps).

Planned later: audio / vibration onset to time the footfall, with vision only
choosing the direction.

## Prior art

- [ddr_cv](https://github.com/tchittesh/ddr_cv) — webcam 3x3 grid controller for
  StepMania; known weak points are 30 fps and false presses from its
  moving-means-airborne heuristic.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m stepcam
```

macOS: grant the terminal Camera and Accessibility permissions
(System Settings → Privacy & Security).
