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

First run:

1. Click the four corners of the grid on the floor as the camera sees it:
   bottom-left, bottom-right, top-right, top-left. "Up" is the top edge.
2. With the floor empty, press `b` to capture the background.
3. Step on the edge cells. Press `k` to turn key output on (arrow keys),
   `s` to save the calibration to `config.json`.

| Key | Action |
|---|---|
| `c` | re-click the four corners |
| `b` | recapture the empty-floor background |
| `+` / `-` | background-difference threshold |
| `[` / `]` | shrink / grow the dead gap at each active cell's edge |
| `k` | toggle key output (off at start unless `--keys`) |
| `s` | save settings |
| `q` / Esc | quit |

Useful flags: `--mirror` (camera faces the player), `--fps`, `--width`,
`--height`, `--exposure` / `--auto-exposure` (raw `CAP_PROP_*` values; their
meaning depends on the OpenCV backend, so check the "camera reports" line and
the on-screen frame interval stats to see whether they took effect),
`--source file.avi --headless` (replay a video and print events).

The HUD shows the frame interval jitter, processing time, and frame age at
output, so the same window works as the latency / stability debug view.

## Test

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```

## Known limitations

- Not yet tested against a real camera; the unit tests and a headless replay of
  a synthetic video pass.
- Press = a foot's lowest point stays in a cell for `debounce` frames. A foot
  hovering in the air projects to the wrong ground point, so airborne feet can
  trigger or miss presses. Landing detection (audio / vibration) is the planned fix.
- Two feet are found as peaks of the silhouette's bottom contour; feet touching
  or crossing merge into one.
- The whole image is analysed, so anyone else moving in frame counts as a foot.
