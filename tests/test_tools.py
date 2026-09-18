import pytest

from stac_pydantic_extensions.tools import simple_latlon_to_wgs_84


def test_simple_latlon_4_tuple_basic_offset():
    bbox = (10, 20, 30, 40)
    result = simple_latlon_to_wgs_84(bbox)
    assert result == (10 - 180, 20 - 90, 30 - 180, 40 - 90)


def test_simple_latlon_4_tuple_returns_tuple_of_len_4():
    result = simple_latlon_to_wgs_84((0, 0, 0, 0))
    assert len(result) == 4


def test_simple_latlon_4_tuple_all_zeros():
    assert simple_latlon_to_wgs_84((0, 0, 0, 0)) == (-180, -90, -180, -90)


def test_simple_latlon_4_tuple_at_extremes():
    # world bbox in lon/lat
    assert simple_latlon_to_wgs_84((-180, -90, 180, 90)) == (-360, -180, 0, 0)


def test_simple_latlon_4_tuple_negative_values():
    result = simple_latlon_to_wgs_84((-10, -20, -30, -40))
    assert result == (-190, -110, -210, -130)


def test_simple_latlon_4_tuple_floats_preserved():
    result = simple_latlon_to_wgs_84((10.5, 20.25, 30.75, 40.125))
    assert result == pytest.approx((-169.5, -69.75, -149.25, -49.875))


def test_simple_latlon_6_tuple_basic_offset():
    bbox = (10, 20, 5, 30, 40, 15)
    result = simple_latlon_to_wgs_84(bbox)
    assert result == (10 - 180, 20 - 90, 5, 30 - 180, 40 - 90, 15)


def test_simple_latlon_6_tuple_returns_tuple_of_len_6():
    result = simple_latlon_to_wgs_84((0, 0, 0, 0, 0, 0))
    assert len(result) == 6


def test_simple_latlon_6_tuple_elevation_untouched():
    result = simple_latlon_to_wgs_84((0, 0, 100, 0, 0, -50))
    assert result[2] == 100
    assert result[5] == -50


def test_simple_latlon_6_tuple_negative_elevation():
    result = simple_latlon_to_wgs_84((1, 2, -100, 3, 4, -200))
    assert result == (1 - 180, 2 - 90, -100, 3 - 180, 4 - 90, -200)


@pytest.mark.parametrize(
    "bad_bbox",
    [
        (1, 2, 3),  # too short
        (1, 2, 3, 4, 5),  # not 4 or 6
        (1, 2, 3, 4, 5, 6, 7),  # too long
        (),  # empty
    ],
)
def test_simple_latlon_invalid_length_raises(bad_bbox):
    with pytest.raises(ValueError):
        simple_latlon_to_wgs_84(bad_bbox)


def test_simple_latlon_non_numeric_input_raises_type_error():
    with pytest.raises(TypeError):
        simple_latlon_to_wgs_84(("a", "b", "c", "d"))


def test_simple_latlon_return_type_is_tuple():
    result = simple_latlon_to_wgs_84((1, 2, 3, 4))
    assert isinstance(result, tuple)


def test_simple_latlon_input_not_mutated():
    bbox = (1, 2, 3, 4)
    original = tuple(bbox)
    simple_latlon_to_wgs_84(bbox)
    assert bbox == original


@pytest.mark.parametrize(
    "bbox",
    [
        (0, 0, 10, 10),
        (-50, -50, 50, 50),
        (100, 45, 120, 60),
    ],
)
def test_simple_latlon_xmin_ymin_xmax_ymax_relative_order_preserved(bbox):
    # subtracting a constant preserves ordering when it held before
    xmin, ymin, xmax, ymax = bbox
    result = simple_latlon_to_wgs_84(bbox)
    if xmin <= xmax:
        assert result[0] <= result[2]
    if ymin <= ymax:
        assert result[1] <= result[3]
