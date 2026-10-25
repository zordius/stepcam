import numpy as np

from stepcam.detect import find_feet


def blank(h=300, w=300):
    return np.zeros((h, w), np.uint8)


def test_no_feet_when_mask_is_empty():
    assert find_feet(blank()) == []


def test_small_noise_is_ignored():
    mask = blank()
    mask[100:105, 100:105] = 255
    assert find_feet(mask) == []


def test_two_legs_joined_by_body_give_two_feet():
    mask = blank()
    mask[0:120, 80:220] = 255  # body
    mask[120:250, 90:110] = 255  # left leg, foot bottom at y=249
    mask[120:240, 190:210] = 255  # right leg, foot bottom at y=239
    feet = find_feet(mask)
    assert len(feet) == 2
    (lx, ly), (rx, ry) = feet
    assert 90 <= lx <= 110 and ly == 249
    assert 190 <= rx <= 210 and ry == 239


def test_one_leg_gives_one_foot():
    mask = blank()
    mask[0:120, 120:180] = 255
    mask[120:250, 140:160] = 255
    feet = find_feet(mask)
    assert len(feet) == 1
    assert feet[0][1] == 249


def test_feet_together_without_a_dip_count_as_one():
    mask = blank()
    mask[0:250, 100:200] = 255  # flat bottom edge, nothing to separate
    assert len(find_feet(mask)) == 1
