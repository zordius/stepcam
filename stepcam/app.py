"""Main loop and the realtime feedback / debug window."""
import time

import cv2
import numpy as np

from . import config
from .capture import Capture
from .config import GRID
from .geometry import project
from .output import KeyOutput
from .pipeline import Pipeline
from .zones import ACTIVE, cell_rect

WINDOW = "stepcam"
GREEN, YELLOW, GRAY, WHITE, RED = (60, 220, 60), (0, 220, 255), (150, 150, 150), (255, 255, 255), (60, 60, 255)
CORNER_NAMES = ["bottom-left", "bottom-right", "top-right", "top-left"]
BACKGROUND_FRAMES = 30


class Ui:
    def __init__(self):
        self.clicks = None  # list while collecting calibration corners, else None

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP and self.clicks is not None and len(self.clicks) < 4:
            self.clicks.append((x, y))


def _quad(rect):
    x0, y0, x1, y1 = rect
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _poly(img, pts, color, thickness=1):
    cv2.polylines(img, [np.int32(pts).reshape(-1, 1, 2)], True, color, thickness, cv2.LINE_AA)


def draw_camera(img, pipe):
    """Grid, zones and feet drawn on the camera image."""
    cs = GRID / 3
    pressed = pipe.tracker.pressed
    shade = img.copy()
    for row in range(3):
        for col in range(3):
            _poly(img, project(pipe.Hinv, _quad(cell_rect((col, row)))), GRAY)
    for name, cell in ACTIVE.items():
        quad = project(pipe.Hinv, _quad(cell_rect(cell, -pipe.cfg.inset)))
        if pressed[name]:
            cv2.fillPoly(shade, [np.int32(quad).reshape(-1, 1, 2)], GREEN)
        _poly(img, quad, WHITE, 2)
        cx, cy = project(pipe.Hinv, [((cell[0] + 0.5) * cs, (cell[1] + 0.5) * cs)])[0]
        cv2.putText(img, name.upper(), (int(cx) - 20, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA)
    return cv2.addWeighted(shade, 0.35, img, 0.65, 0)


def draw_feet_camera(img, pipe, feet):
    for foot in feet:
        center = (int(foot.image[0]), int(foot.image[1]))
        down = foot.zone is not None and pipe.tracker.pressed[foot.zone]
        cv2.circle(img, center, 8, GREEN if down else (YELLOW if foot.zone else GRAY), -1 if down else 2, cv2.LINE_AA)


def draw_ground(frame, pipe, feet, size):
    """Top-down view of the floor with the grid and feet."""
    view = cv2.resize(cv2.warpPerspective(frame, pipe.H, (GRID, GRID)), (size, size))
    k = size / GRID
    for i in (1, 2):
        cv2.line(view, (int(i * GRID / 3 * k), 0), (int(i * GRID / 3 * k), size), GRAY, 1)
        cv2.line(view, (0, int(i * GRID / 3 * k)), (size, int(i * GRID / 3 * k)), GRAY, 1)
    for name, cell in ACTIVE.items():
        x0, y0, x1, y1 = (int(v * k) for v in cell_rect(cell, -pipe.cfg.inset))
        down = pipe.tracker.pressed[name]
        cv2.rectangle(view, (x0, y0), (x1, y1), GREEN if down else WHITE, -1 if down else 1)
    for foot in feet:
        center = (int(foot.ground[0] * k), int(foot.ground[1] * k))
        down = foot.zone is not None and pipe.tracker.pressed[foot.zone]
        cv2.circle(view, center, 7, RED if down else YELLOW, -1 if down else 2, cv2.LINE_AA)
    return view


def hud(img, lines):
    for i, (text, color) in enumerate(lines):
        cv2.putText(img, text, (8, 18 + 16 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, text, (8, 18 + 16 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)


def run(args):
    cfg = config.load(args.config)
    pipe = Pipeline(cfg)
    props = {}
    if args.exposure is not None:
        props[cv2.CAP_PROP_EXPOSURE] = args.exposure
    if args.auto_exposure is not None:
        props[cv2.CAP_PROP_AUTO_EXPOSURE] = args.auto_exposure
    source = int(args.source) if args.source.isdigit() else args.source
    cap = Capture(source, args.width, args.height, args.fps, args.mirror, props).start()
    keys = KeyOutput(args.keys)
    ui = Ui()
    log = []

    if args.headless:
        if pipe.H is None:
            raise SystemExit(f"headless needs calibration corners in {args.config}")
        pipe.fg.begin_background(BACKGROUND_FRAMES)
    else:
        cv2.namedWindow(WINDOW)
        cv2.setMouseCallback(WINDOW, ui.on_mouse)
        if pipe.H is None:
            ui.clicks = []

    print("camera reports:", cap.actual)
    seen = 0
    started = time.perf_counter()
    proc_ms = age_ms = 0.0
    result = None
    try:
        while True:
            if args.seconds and time.perf_counter() - started > args.seconds:
                break
            item = cap.latest()
            if item is None or item[0] == seen:
                if cap.eof and item and item[0] == seen:
                    break
                if not args.headless and cv2.waitKey(1) & 0xFF == 27:
                    break
                time.sleep(0.0005)
                continue
            seen, ts, frame = item

            if pipe.fg.collecting:
                pipe.fg.feed(frame)
            elif pipe.ready:
                t0 = time.perf_counter()
                result = pipe.process(frame)
                for name, is_down in result.events:
                    keys.send(name, is_down)
                    print(f"{ts - started:9.3f}s {name:5s} {'down' if is_down else 'up'}")
                    log.append((ts - started, name, is_down))
                t1 = time.perf_counter()
                proc_ms, age_ms = (t1 - t0) * 1000, (t1 - ts) * 1000

            if args.headless:
                continue

            cam = frame.copy()
            if pipe.H is not None:
                cam = draw_camera(cam, pipe)
                if result:
                    draw_feet_camera(cam, pipe, result.feet)
            for i, pt in enumerate(ui.clicks or []):
                cv2.circle(cam, (int(pt[0]), int(pt[1])), 5, RED, -1)
                cv2.putText(cam, str(i + 1), (int(pt[0]) + 8, int(pt[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 1)
            fps, jitter, worst = cap.stats()
            lines = [
                (f"fps {fps:5.1f}  interval sd {jitter:4.1f} ms  max {worst:5.1f} ms", WHITE),
                (f"process {proc_ms:4.1f} ms  frame age at output {age_ms:5.1f} ms", WHITE),
                (f"thresh {cfg.diff_thresh}  inset {cfg.inset:.2f}  keys {'ON' if keys.enabled else 'off'}", GREEN if keys.enabled else GRAY),
            ]
            if ui.clicks is not None:
                lines.append((f"click {CORNER_NAMES[len(ui.clicks)]} corner of the grid", YELLOW))
            elif not pipe.fg.has_background:
                lines.append(("clear the floor, then press b to capture the background", YELLOW))
            elif pipe.fg.collecting:
                lines.append(("capturing background...", YELLOW))
            lines.append(("c calibrate  b background  +/- thresh  [ ] inset  k keys  s save  q quit", GRAY))
            hud(cam, lines)
            if pipe.H is not None:
                ground = draw_ground(frame, pipe, result.feet if result else [], cam.shape[0])
                cam = np.hstack([cam, ground])
            cv2.imshow(WINDOW, cam)

            if ui.clicks is not None and len(ui.clicks) == 4:
                pipe.set_corners(ui.clicks)
                ui.clicks = None
                result = None

            k = cv2.waitKey(1) & 0xFF
            if k in (27, ord("q")):
                break
            elif k == ord("c"):
                ui.clicks = []
            elif k == ord("b"):
                pipe.fg.begin_background(BACKGROUND_FRAMES)
            elif k in (ord("+"), ord("=")):
                cfg.diff_thresh = min(255, cfg.diff_thresh + 2)
            elif k == ord("-"):
                cfg.diff_thresh = max(1, cfg.diff_thresh - 2)
            elif k == ord("["):
                cfg.inset = max(0.0, round(cfg.inset - 0.01, 2))
            elif k == ord("]"):
                cfg.inset = min(0.4, round(cfg.inset + 0.01, 2))
            elif k == ord("k"):
                keys.toggle()
            elif k == ord("s"):
                config.save(cfg, args.config)
                print("saved", args.config)
    finally:
        keys.release_all()
        cap.stop()
        cv2.destroyAllWindows()
    return log
