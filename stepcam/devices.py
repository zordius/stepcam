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


def camera_name(index, cameras=None):
    """Name of a camera index, or '' when unknown (video files, other platforms)."""
    if not isinstance(index, int):
        return ""
    return dict(list_cameras() if cameras is None else cameras).get(index, "")
