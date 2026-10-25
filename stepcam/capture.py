"""Threaded camera (or video file) capture that keeps only the newest frame."""
import statistics
import sys
import threading
import time
from collections import deque

import cv2


def _fourcc(value):
    return "".join(chr((int(value) >> (8 * i)) & 0xFF) for i in range(4)).strip("\x00 ") or "?"


def _open(source):
    backend = cv2.CAP_ANY if isinstance(source, str) or sys.platform != "darwin" else cv2.CAP_AVFOUNDATION
    return cv2.VideoCapture(source, backend)


def probe(max_index=4, seconds=2.0):
    """Try camera indexes and print which ones actually deliver frames."""
    for index in range(max_index + 1):
        cap = _open(index)
        if not cap.isOpened():
            print(f"camera {index}: cannot open")
            continue
        frames, t0 = 0, time.perf_counter()
        while time.perf_counter() - t0 < seconds:
            ok, frame = cap.read()
            frames += ok
        size = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
        print(f"camera {index}: {frames} frames in {seconds:.0f}s, {size}" + ("" if frames else "  <- no frames"))
        cap.release()


class Capture:
    def __init__(self, source=0, width=640, height=480, fps=60, mirror=False, props=None):
        self.is_file = isinstance(source, str)
        self.cap = _open(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"cannot open video source {source!r}")
        if not self.is_file:
            # FOURCC first: 60 fps is normally only offered in MJPG mode
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        for prop, value in (props or {}).items():
            self.cap.set(prop, value)
        self.mirror = mirror
        # what the driver reports back; it may silently ignore what was requested
        self.actual = {
            "size": f"{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}",
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "fourcc": _fourcc(self.cap.get(cv2.CAP_PROP_FOURCC)),
            "exposure": self.cap.get(cv2.CAP_PROP_EXPOSURE),
            "auto_exposure": self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
        }
        self.eof = False
        self._latest = None
        self._seq = 0
        self._stamps = deque(maxlen=120)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=1)
        self.cap.release()

    def _run(self):
        period = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 30)
        while not self._stop.is_set():
            ok, frame = self.cap.read()
            ts = time.perf_counter()  # when read() returned, not when light hit the sensor
            if not ok:
                if self.is_file:
                    self.eof = True
                    return
                time.sleep(0.05)  # a live camera may just be slow to start
                continue
            if self.mirror:
                frame = cv2.flip(frame, 1)
            with self._lock:
                self._seq += 1
                self._latest = (self._seq, ts, frame)
                self._stamps.append(ts)
            if self.is_file:
                time.sleep(period)

    def latest(self):
        """(sequence, timestamp, frame) of the newest frame, or None before the first."""
        with self._lock:
            return self._latest

    def stats(self):
        """(fps, interval stddev ms, max interval ms) over the last ~120 frames."""
        with self._lock:
            stamps = list(self._stamps)
        if len(stamps) < 3:
            return 0.0, 0.0, 0.0
        gaps = [b - a for a, b in zip(stamps, stamps[1:])]
        return 1 / statistics.fmean(gaps), statistics.pstdev(gaps) * 1000, max(gaps) * 1000
