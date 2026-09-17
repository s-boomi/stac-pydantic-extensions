import pytest
from pydantic import BaseModel, ValidationError

from stac_pydantic_extensions import validators
from stac_pydantic_extensions.model_annotations import (
    PercentageValue,
    ValidateDoi,
)


@pytest.mark.parametrize("value", [0, 50, 100, 12.5])
def test_validate_percentage_number_valid(value):
    assert validators.validate_percentage(value) == value


@pytest.mark.parametrize("value", [-1, 100.1, -0.01])
def test_validate_percentage_number_invalid(value):
    with pytest.raises(TypeError):  # currently TypeError due to bug #2
        validators.validate_percentage(value)


def test_validate_percentage_none_passthrough():
    assert validators.validate_percentage(None) is None


@pytest.mark.parametrize("value", [0, 90, 45.5])
def test_validate_off_nadir_valid(value):
    assert validators.validate_off_nadir(value) == value


@pytest.mark.parametrize("value", [-0.1, 90.1])
def test_validate_off_nadir_invalid(value):
    with pytest.raises(TypeError):
        validators.validate_off_nadir(value)


def test_doi_regex_bug_reproduction():
    """Regression test pinning the known-broken DOI regex.
    Once DOI_PATTERN is fixed, this should be flipped to assert success."""
    with pytest.raises(TypeError):
        validators.validate_doi("10.5061/dryad.s2v81.2/27.2")


class _PercentModel(BaseModel):
    value: PercentageValue | None = None


def test_percentage_annotated_accepts_valid():
    assert _PercentModel(value=42).value == 42


def test_percentage_annotated_rejects_invalid():
    # Today this will raise TypeError bubbling out of pydantic's validator
    # machinery rather than a clean ValidationError — that's the bug.
    with pytest.raises((ValidationError, TypeError)):
        _PercentModel(value=142)


class _DoiModel(BaseModel):
    doi: ValidateDoi | None = None


def test_doi_annotated_currently_never_validates():
    """Pins bug #3: validate_doi isn't wrapped in AfterValidator, so this
    currently succeeds even though '10.5061/dryad...' is malformed w.r.t.
    the bad regex, AND even a clearly-invalid string sails through."""
    assert _DoiModel(doi="not-a-doi-at-all").doi == "not-a-doi-at-all"


@pytest.mark.parametrize(
    "code", ["epsg:4326", "EPSG:4326", "urn:ogc:def:crs:EPSG::4326"]
)
def test_proj_code_valid(code):
    assert validators.validate_proj_code(code) == code


def test_proj_code_invalid():
    with pytest.raises(ValueError):
        validators.validate_proj_code("not-a-real-crs")


@pytest.mark.parametrize(
    "transform",
    [
        [30, 0, 224985, 0, -30, 6790215],
        [30, 0, 224985, 0, -30, 6790215, 0, 0, 1],
    ],
)
def test_proj_transform_valid(transform):
    assert validators.validate_proj_transform(transform) == transform


def test_proj_transform_wrong_length():
    with pytest.raises(TypeError):
        validators.validate_proj_transform([1, 2, 3])


def test_proj_transform_bad_last_row():
    with pytest.raises(TypeError):
        validators.validate_proj_transform([30, 0, 0, 0, -30, 0, 1, 1, 1])


@pytest.mark.parametrize(
    "code",
    [
        "IAU:2015:19900",
        "iau:2015:19900",
        "urn:ogc:def:crs:IAU:2015:19900",
        "epsg:4326",
        "EPSG:4326",
        "4326",
        "OGC:CRS84",
        "ESRI:102100",
    ],
)
def test_validate_proj_code_valid(code):
    assert validators.validate_proj_code(code) == code.strip()


def test_validate_proj_code_strips_whitespace():
    assert validators.validate_proj_code("  EPSG:4326  ") == "EPSG:4326"


@pytest.mark.parametrize(
    "code",
    ["epsg:", "epsg:abc", "", "not-a-real-crs"],
)
def test_validate_proj_code_invalid(code):
    with pytest.raises(ValueError):
        validators.validate_proj_code(code)


def test_validate_bbox_none_returns_none():
    assert validators.validate_bbox(None) is None


@pytest.mark.parametrize(
    "bbox",
    [
        # Standard WGS84 convention (-180/-90/180/90)
        (-180, -90, 180, 90),
        (-120, -45, -60, 45),
        (0, 0, 10, 10),  # ambiguous, but valid in both -> should pass
        (-10, -10, 10, 10),
        # Extraterrestrial convention (0/0/360/180)
        (0, 0, 360, 180),
        (10, 10, 350, 170),
        (200, 100, 250, 150),
    ],
)
def test_validate_bbox_valid_4_coord_bbox(bbox):
    assert validators.validate_bbox(bbox) == bbox


@pytest.mark.parametrize(
    "bbox",
    [
        (-180, -90, 0, 180, 90, 1000),  # standard
        (0, 0, 0, 360, 180, 5000),  # extraterrestrial
        (10, 10, -500, 20, 20, 500),  # standard, negative min_elev
    ],
)
def test_validate_bbox_valid_6_coord_bbox(bbox):
    assert validators.validate_bbox(bbox) == bbox


@pytest.mark.parametrize(
    "bbox",
    [
        (-10, 10, 200, 20),  # negative lon mixed with lon > 180
        (-200, -90, 180, 90),  # xmin < -180
        (-180, -100, 180, 90),  # ymin < -90
        (
            0,
            -10,
            360,
            180,
        ),  # ymin < 0, xmax = 360 -> not standard, not extraterrestrial
        (0, 0, 400, 180),  # xmax > 360
        (0, 0, 360, 200),  # ymax > 180
        (-181, 0, 0, 10),  # xmin < -180
    ],
)
def test_validate_bbox_invalid_bbox_out_of_range(bbox):
    with pytest.raises(ValueError, match="Bounding box must be within"):
        validators.validate_bbox(bbox)


@pytest.mark.parametrize(
    "bbox",
    [
        (-10, 10, 10, 5),  # standard range, but ymax < ymin
        (10, 100, 20, 50),  # extraterrestrial range, but ymax < ymin
    ],
)
def test_validate_bbox_invalid_latitude_order(bbox):
    with pytest.raises(
        ValueError, match="Maximum latitude .* must be greater than minimum latitude"
    ):
        validators.validate_bbox(bbox)


def test_validate_bbox_invalid_elevation_order():
    bbox = (-10, -10, 1000, 10, 10, 500)  # max_elev < min_elev
    with pytest.raises(
        ValueError, match="Maximum elevation must greater than minimum elevation"
    ):
        validators.validate_bbox(bbox)


@pytest.mark.parametrize(
    "bbox",
    [
        (-10, -10, 10),
        (-10, -10, 10, 10, 10),
        (-10, -10, 10, 10, 10, 10, 10),
        (),
    ],
)
def test_validate_bbox_invalid_length(bbox):
    with pytest.raises(ValueError, match="Bounding box must have 4 or 6 coordinates"):
        validators.validate_bbox(bbox)


def test_validate_bbox_interval_empty_list_returns_unchanged():
    assert validators.validate_bbox_interval([]) == []


def test_validate_bbox_interval_single_overall_bbox_standard():
    v = [(-180, -90, 180, 90)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_single_overall_bbox_mixed_convention():
    v = [(0.064, -60.0, 359.988, 59.9688)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_sub_bbox_contained_standard():
    v = [(-180, -90, 180, 90), (-10, -10, 10, 10)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_sub_bbox_contained_mixed_convention():
    # Overall uses lon 0-360 / lat -90-90; sub-bbox nested within it.
    v = [(0.064, -60.0, 359.988, 59.9688), (100, -20, 200, 20)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_sub_bbox_not_contained_in_latitude():
    v = [(0.064, -60.0, 359.988, 59.9688), (100, -70, 200, 20)]
    with pytest.raises(ValueError, match="not fully contained"):
        validators.validate_bbox_interval(v)


def test_validate_bbox_interval_sub_bbox_not_contained_in_longitude():
    v = [(10, -60.0, 350, 59.9688), (5, -10, 20, 10)]
    with pytest.raises(ValueError, match="not fully contained"):
        validators.validate_bbox_interval(v)


def test_validate_bbox_interval_antimeridian_crossing_standard_convention():
    # Overall crosses antimeridian at +/-180 (split=0)
    v = [(174, -3, -174, 5), (176, 1, 179, 3)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_antimeridian_crossing_standard_convention_invalid():
    v = [(174, -3, -174, 5), (170, 1, 179, 3)]  # xmin_sub < overall xmin
    with pytest.raises(ValueError, match="not fully contained"):
        validators.validate_bbox_interval(v)


def test_validate_bbox_interval_antimeridian_crossing_extraterrestrial_convention():
    # Overall crosses wrap at 0/360 (split=180); equivalent shape to the
    # standard case above but shifted into 0-360 space.
    v = [(354, 0, 186, 95), (356, 5, 359, 8)]
    assert validators.validate_bbox_interval(v) == v


def test_validate_bbox_interval_sub_crossing_but_overall_not_crossing_raises():
    v = [(-10, -10, 10, 10), (5, -5, -5, 5)]  # sub wraps, overall doesn't
    with pytest.raises(ValueError, match="not fully contained"):
        validators.validate_bbox_interval(v)
