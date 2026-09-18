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
