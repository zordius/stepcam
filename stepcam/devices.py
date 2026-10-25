"""Camera names, numbered the way OpenCV's AVFoundation backend numbers them (macOS)."""
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


def camera_name(index, cameras=None):
    """Name of a camera index, or '' when unknown (video files, other platforms)."""
    if not isinstance(index, int):
        return ""
    return dict(list_cameras() if cameras is None else cameras).get(index, "")
