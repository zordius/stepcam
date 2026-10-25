from stepcam import devices


class Dev:
    def __init__(self, uid):
        self._uid = uid

    def uniqueID(self):
        return self._uid


def test_devices_are_ordered_by_unique_id_like_opencv():
    shuffled = [Dev("B-iphone"), Dev("0x8020-facetime"), Dev("A-obs")]
    assert [d.uniqueID() for d in devices.order_like_opencv(shuffled)] == [
        "0x8020-facetime",
        "A-obs",
        "B-iphone",
    ]


def test_camera_name_lookup():
    cams = [(0, "FaceTime HD Camera"), (1, "OBS Virtual Camera")]
    assert devices.camera_name(1, cams) == "OBS Virtual Camera"
    assert devices.camera_name(5, cams) == ""


def test_camera_name_is_empty_for_video_files():
    assert devices.camera_name("clip.avi", [(0, "x")]) == ""
