"""Camera names, numbered the way OpenCV's AVFoundation backend numbers them (macOS)."""
import os
import sys


def order_like_opencv(devices):
    """OpenCV sorts video + muxed devices by uniqueID (cap_avfoundation_mac.mm)."""
    return sorted(devices, key=lambda d: str(d.uniqueID()))


def list_cameras():
    """[(index, name)]; empty off macOS or when pyobjc is missing."""
    if sys.platform != "darwin":
        return []
    try:
        import AVFoundation as av
    except ImportError:
        return []
    found = list(av.AVCaptureDevice.devicesWithMediaType_(av.AVMediaTypeVideo))
    found += list(av.AVCaptureDevice.devicesWithMediaType_(av.AVMediaTypeMuxed))
    return [(i, str(d.localizedName())) for i, d in enumerate(order_like_opencv(found))]


def _rank(name):
    lowered = name.lower()
    if "iphone" in lowered or "ipad" in lowered:
        return 2  # Continuity Camera: slow to start and may use the network
    if "virtual" in lowered:
        return 1  # e.g. OBS Virtual Camera: silent unless something feeds it
    return 0


def scan_order(cameras, max_index=9):
    """Indexes in the order auto-detect should try them.

    Real cameras first, then names containing "virtual", then iPhone / iPad;
    ties keep index order. Without names, plain index order.
    """
    if not cameras:
        return list(range(max_index + 1))
    return [index for index, _ in sorted(cameras, key=lambda c: (_rank(c[1]), c[0]))]


def resolve_source(arg, cameras=None):
    """Turn a --source value into a camera index or a video file path.

    Digits are an index and an existing path is a file; anything else is matched
    as a case-insensitive substring of the camera names. Several matches take the
    one auto-detect would try first. Raises LookupError when nothing matches.
    """
    if arg.isdigit():
        return int(arg)
    if os.path.exists(arg):
        return arg
    cameras = list_cameras() if cameras is None else cameras
    names = dict(cameras)
    matches = [i for i in scan_order(cameras) if i in names and arg.lower() in names[i].lower()]
    if not matches:
        available = ", ".join(f"[{i}] {n}" for i, n in cameras) or "none (camera names need macOS + pyobjc)"
        raise LookupError(f"--source {arg!r} is not a camera index or an existing file, and no camera name contains it. Cameras: {available}")
    if len(matches) > 1:
        print(f"{len(matches)} cameras match {arg!r}: {matches}; using {matches[0]}", file=sys.stderr)
    return matches[0]


def camera_name(index, cameras=None):
    """Name of a camera index, or '' when unknown (video files, other platforms)."""
    if not isinstance(index, int):
        return ""
    return dict(list_cameras() if cameras is None else cameras).get(index, "")
