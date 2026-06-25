from typing import Annotated, ClassVar, Literal

from geojson_pydantic.geometries import Geometry
from pydantic import AfterValidator, AnyUrl, ConfigDict
from stac_pydantic.shared import BBox, StacBaseModel, validate_bbox

from stac_pydantic_extensions import validators
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.extensions._projjson import ProjJson

ProjCodeValue = Annotated[str, AfterValidator(validators.validate_proj_code)]
ProjWktValue = Annotated[str, AfterValidator(validators.validate_proj_wkt)]
BboxOrNone = Annotated[BBox, AfterValidator(validate_bbox)]
ProjTransformValue = Annotated[
    list[float | int], AfterValidator(validators.validate_proj_transform)
]


class Centroid(StacBaseModel):
    lat: float
    lon: float


class ProjectionFields(BaseExtraFields):
    """https://github.com/stac-extensions/proj"""

    code: ProjCodeValue
    wkt2: ProjWktValue
    projjson: ProjJson | None = None
    geometry: Geometry | None = None
    bbox: BboxOrNone
    centroid: Centroid | None = None
    shape: list[int] | None = None
    transform: list[float | int] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="proj")
    )

    # @model_validator(mode="after")
    # def check_passwords_match(self) -> Self:
    #     if self.code is None and self.projjson is None and self.geometry is None:
    #         print(
    #             "This projection is more likely to be non-rectified imagery (ie. GCP)"
    #         )
    #     return self


class ProjectionExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/projection/v2.0.0/schema.json"
    )
    prefix: ClassVar[Literal["proj"]] = "proj"
    fields: ProjectionFields
    version: ClassVar[Literal["v2.0.0"]] = "v2.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection", "Asset", "ItemAsset"}
