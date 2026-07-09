import re

from pydantic import ValidationError
from pyproj import CRS
from pyproj.exceptions import CRSError
from stac_pydantic.collection import Range
from stac_pydantic.shared import NumType

DOI_PATTERN = re.compile(r"^10\\.[0-9a-zA-Z]{4,}/[^\\s]+$")


def validate_percentage(v: NumType | Range | None) -> NumType | Range | None:
    """Checks if the value is a valid percentage in case of a number, or in
    the case of a Range object, checks of the minimum and maximum are between
    0 and 100 included.
    """
    if v is not None and isinstance(v, Range):
        v_min, v_max = v.minimum, v.maximum
        try:
            v_min = float(v_min)
            v_max = float(v_max)
            if v_min < 0 or v_max > 100:
                raise ValidationError(
                    f"Range must be between [0,100]. Range value: {v.to_dict()}"
                )
        except ValueError as val_err:
            raise ValidationError(
                f"{v_min} or {v_max} must be numbers, not {type(v_min)} or {type(v_max)} respectively."
            ) from val_err

    if v is not None and isinstance(v, NumType) and (v < 0 or v > 100):
        raise ValidationError(f"{v} must be between 0 and 100")

    return v


def validate_proj_code(v: str | None) -> str | None:
    try:
        if v is not None:
            if v.startswith("epsg:"):
                CRS.from_epsg(int(v.split(":")[-1]))
            else:
                CRS.from_string(v)
    except Exception as e:
        raise ValidationError(f"{v} is not a valid proj code") from e

    return v


def validate_proj_wkt(v: str | None) -> str | None:
    if v is not None:
        try:
            CRS.from_wkt(v)
        except CRSError as e:
            raise ValidationError(f"{v} is not a valid WKT2 string") from e
    return v


def validate_proj_projcode(v: str | None) -> str | None:
    if v is not None:
        try:
            CRS.from_proj4(v)
        except CRSError as e:
            raise ValidationError(f"{v} is not a valid proj4 code") from e
    return v


def validate_proj_transform(v: list[int | float] | None) -> list[int | float] | None:
    if v is not None:
        if len(v) > 9 or len(v) < 6:
            raise ValidationError(
                f"{str(v)[:15]} is {len(v)} elements long. "
                "It must be either 9 or 6 elements long"
            )
        if len(v) == 9 and v[6:] != [0, 0, 1]:
            raise ValidationError(
                f"Last row of a 3x3 transform must always be 0, 0, 1. Last elements were {v[6:]}"
            )

    return v


def validate_doi(v: str | None) -> str | None:
    if v is not None:
        if DOI_PATTERN.fullmatch(v) is None:
            raise ValidationError(f"{v} is not a valid DOI")
    return v


def validate_off_nadir(v: float | int | None) -> float | int | None:
    if v is not None:
        if v < 0 or v > 90:
            raise ValidationError(
                "Off Nadir, incidence and moon "
                f"elevation angles must be between 0 and 90° (value={v})"
            )

    return v


def validate_azimuth(v: float | int | None) -> float | int | None:
    if v is not None:
        if v < 0 or v > 360:
            raise ValidationError(
                f"Azimuth angles must be between 0 and 360° (value={v})"
            )

    return v


def validate_elevation(v: float | int | None) -> float | int | None:
    if v is not None:
        if v < -90 or v > 90:
            raise ValidationError(
                f"Sun elevation angle must be between -90 and 90° (value={v})"
            )

    return v
