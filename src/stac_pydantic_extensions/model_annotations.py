from __future__ import annotations

from typing import Annotated

from geojson_pydantic.types import BBox
from pydantic import AfterValidator
from stac_pydantic.collection import Range
from stac_pydantic.shared import NumType, validate_bbox

from stac_pydantic_extensions import validators

# For EO but can be generalized
PercentageValue = Annotated[
    NumType | Range, AfterValidator(validators.validate_percentage)
]
# Mainly for proj
ProjCodeValue = Annotated[str, AfterValidator(validators.validate_proj_code)]
ProjWktValue = Annotated[str, AfterValidator(validators.validate_proj_wkt)]
BboxValue = Annotated[BBox | None, AfterValidator(validate_bbox)]
ProjTransformValue = Annotated[
    list[float | int], AfterValidator(validators.validate_proj_transform)
]
# For scientific extension
ValidateDoi = Annotated[str, validators.validate_doi]
# For view extension
OffNadir = Annotated[float | int, validators.validate_off_nadir]
Elevation = Annotated[float | int, validators.validate_elevation]
Azimuth = Annotated[float | int, validators.validate_azimuth]
