import re
from typing import cast

from geojson_pydantic.types import BBox
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
    if v is None:
        return None

    v = v.strip()

    try:
        if v.lower().startswith("epsg:"):
            CRS.from_epsg(int(v.split(":")[-1]))
        elif v.lower().startswith("iau:"):
            # PROJ's IAU authority lookup is case-sensitive — "iau" alone
            # isn't recognized, only "IAU". The rest of the code (body id,
            # feature code) can stay as the user wrote it.
            _, rest = v.split(":", 1)
            CRS.from_string(f"urn:ogc:def:crs:IAU:{rest}")
        else:
            CRS.from_string(v)
    except Exception as e:
        raise ValueError(f"{v} is not a valid proj code") from e

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


def validate_bbox(v: BBox | None) -> BBox | None:
    """Validate BBOX value against WGS84 (-180/-90/180/90)
    or extraterrestrial (0/0/360/180) conventions."""
    if v is not None:
        if len(v) == 4:
            xmin, ymin, xmax, ymax = cast(tuple[int, int, int, int], v)

        elif len(v) == 6:
            xmin, ymin, min_elev, xmax, ymax, max_elev = cast(
                tuple[int, int, int, int, int, int], v
            )
            if max_elev < min_elev:
                raise ValueError(
                    "Maximum elevation must greater than minimum elevation"
                )
        else:
            raise ValueError("Bounding box must have 4 or 6 coordinates")

        # Check against both accepted conventions

        lon_valid = (-180 <= xmin and xmax <= 180) or (0 <= xmin and xmax <= 360)
        lat_valid = (-90 <= ymin and ymax <= 90) or (0 <= ymin and ymax <= 180)

        if not (lon_valid and lat_valid):
            raise ValueError(
                "Bounding box must be within (-180, -90, 180, 90) "
                "or (0, 0, 360, 180), longitude and latitude checked independently"
            )

        if ymax < ymin:
            raise ValueError(
                f"Maximum latitude ({ymax}) must be greater than minimum latitude  ({ymin})"
            )

    return v


def validate_bbox_interval(v: list[BBox]) -> list[BBox]:  # noqa: C901
    ivalues = iter(v)

    overall_bbox = next(ivalues, None)
    if not overall_bbox:
        return v

    assert validate_bbox(overall_bbox)

    if len(overall_bbox) == 4:
        xmin, ymin, xmax, ymax = overall_bbox
    else:
        xmin, ymin, _, xmax, ymax, _ = overall_bbox

    # Split point for antimeridian wraparound depends only on the longitude
    # convention in use: standard (-180/180) wraps at +/-180, split at 0.
    # 0-360 style wraps at 0/360, split at 180. Latitude convention is irrelevant here.
    lon_is_standard = xmin < 0 or xmax < 0
    split = 0 if lon_is_standard else 180

    crossing_antimeridian = xmin > xmax
    for bbox in ivalues:
        error_msg = ValueError(
            f"`BBOX` {bbox} not fully contained in `Overall BBOX` {overall_bbox}"
        )
        _ = validate_bbox(bbox)

        if len(bbox) == 4:
            xmin_sub, ymin_sub, xmax_sub, ymax_sub = bbox
        else:
            xmin_sub, ymin_sub, _, xmax_sub, ymax_sub, _ = bbox

        if not ((ymin_sub >= ymin) and (ymax_sub <= ymax)):
            raise error_msg

        sub_crossing_antimeridian = xmin_sub > xmax_sub
        if not crossing_antimeridian and sub_crossing_antimeridian:
            raise error_msg

        elif crossing_antimeridian:
            # Case 1
            if sub_crossing_antimeridian:
                if not (xmin_sub > xmin and xmax_sub < xmax):
                    raise error_msg
            # Case 2
            elif xmin_sub >= split and xmin_sub < xmin:
                raise error_msg
            # Case 3
            elif xmin_sub <= split and xmax_sub > xmax:
                raise error_msg

        else:
            if not ((xmin_sub >= xmin) and (xmax_sub <= xmax)):
                raise error_msg

    return v
