"""Image <-> ground-plane mapping."""
import cv2
import numpy as np

from .config import GRID


def homography(corners):
    """Image points (BL, BR, TR, TL as seen by the camera) -> ground coords."""
    src = np.float32(corners)
    dst = np.float32([[0, GRID], [GRID, GRID], [GRID, 0], [0, 0]])
    return cv2.getPerspectiveTransform(src, dst)


def project(matrix, points):
    """Map a list of (x, y) points through a 3x3 homography."""
    if not len(points):
        return []
    out = cv2.perspectiveTransform(np.float32(points).reshape(-1, 1, 2), matrix)
    return [tuple(p) for p in out.reshape(-1, 2)]
