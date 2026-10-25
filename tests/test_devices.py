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


def test_scan_order_puts_virtual_then_iphone_last():
    cams = [(0, "陳建宏的iPhone Camera"), (1, "FaceTime HD Camera (Built-in)"), (2, "OBS Virtual Camera")]
    assert devices.scan_order(cams) == [1, 2, 0]


def test_scan_order_matches_case_insensitively_and_covers_ipad():
    cams = [(0, "My iPad Camera"), (1, "VIRTUAL cam"), (2, "USB Webcam"), (3, "Another Webcam")]
    assert devices.scan_order(cams) == [2, 3, 1, 0]


def test_scan_order_keeps_index_order_within_a_group():
    cams = [(0, "Cam B"), (1, "Cam A"), (2, "Cam C")]
    assert devices.scan_order(cams) == [0, 1, 2]


def test_iphone_named_virtual_still_goes_last():
    cams = [(0, "iPhone Virtual Camera"), (1, "OBS Virtual Camera"), (2, "Webcam")]
    assert devices.scan_order(cams) == [2, 1, 0]


def test_scan_order_without_names_is_plain_index_order():
    assert devices.scan_order([], max_index=3) == [0, 1, 2, 3]


def test_camera_name_is_empty_for_video_files():
    assert devices.camera_name("clip.avi", [(0, "x")]) == ""
