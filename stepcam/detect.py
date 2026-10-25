"""Foot detection: background subtraction, then the lowest points of the silhouette."""
import cv2
import numpy as np

_OPEN_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


def _gray(frame):
    return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)


class Foreground:
    """Empty-floor reference image and the foreground mask against it."""

    def __init__(self):
        self.bg = None
        self._acc = None
        self._need = 0
        self._n = 0

    @property
    def has_background(self):
        return self.bg is not None

    @property
    def collecting(self):
        return self._need > 0

    def begin_background(self, frames):
        self._acc = None
        self._need = frames
        self._n = 0

    def feed(self, frame):
        """Add a frame to the running background average; True once it is done."""
        gray = _gray(frame).astype(np.float32)
        self._acc = gray if self._acc is None else self._acc + gray
        self._n += 1
        if self._n < self._need:
            return False
        self.bg = (self._acc / self._n).astype(np.uint8)
        self._need = 0
        return True

    def mask(self, frame, thresh):
        diff = cv2.absdiff(_gray(frame), self.bg)
        _, mask = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, _OPEN_KERNEL)


def find_feet(mask, min_area=400, min_sep=40, min_dip=6, smooth=9):
    """Lowest image point of each foot, left to right (at most two).

    Legs and body are usually one connected blob, so feet are the peaks of the
    silhouette's bottom contour rather than separate components. A second peak
    counts only if it is at least `min_sep` columns away and the contour dips
    at least `min_dip` pixels between the two.
    """
    if cv2.countNonZero(mask) < min_area:
        return []
    h = mask.shape[0]
    solid = mask > 0
    bottom = np.where(solid.any(axis=0), h - 1 - np.argmax(solid[::-1], axis=0), 0)
    bottom = bottom.astype(np.float32)
    avg = np.convolve(bottom, np.ones(smooth, np.float32) / smooth, mode="same")

    x1 = int(np.argmax(avg))
    peaks = [x1]
    rest = avg.copy()
    rest[max(0, x1 - min_sep) : x1 + min_sep + 1] = 0
    x2 = int(np.argmax(rest))
    if rest[x2] > 0:
        lo, hi = sorted((x1, x2))
        if avg[lo : hi + 1].min() <= min(avg[x1], avg[x2]) - min_dip:
            peaks.append(x2)

    half = smooth // 2
    return [(x, float(bottom[max(0, x - half) : x + half + 1].max())) for x in sorted(peaks)]
