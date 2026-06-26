from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, ClassVar, Literal

from geojson_pydantic.geometries import Geometry
from pydantic import AfterValidator, AnyUrl, ConfigDict
from stac_pydantic.shared import BBox, StacBaseModel, validate_bbox

from stac_pydantic_extensions import validators
from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.extensions._projjson import ProjJson

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


ProjCodeValue = Annotated[str, AfterValidator(validators.validate_proj_code)]
ProjWktValue = Annotated[str, AfterValidator(validators.validate_proj_wkt)]
BboxValue = Annotated[BBox | None, AfterValidator(validate_bbox)]
ProjTransformValue = Annotated[
    list[float | int], AfterValidator(validators.validate_proj_transform)
]


class Centroid(StacBaseModel):
    lat: float
    lon: float


class ProjectionFields(BaseExtraFields):
    """https://github.com/stac-extensions/proj"""

    code: ProjCodeValue | None = None
    wkt2: ProjWktValue | None = None
    projjson: ProjJson | None = None
    geometry: Geometry | None = None
    bbox: BboxValue | None = None
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

    @classmethod
    def from_stac_object(cls, stac_object: StacObject) -> "ProjectionExtension | None":
        stac_obj_ext = stac_object.stac_extensions
        if stac_obj_ext is not None and cls.stac_extension in stac_obj_ext:
            if isinstance(stac_object, Item):
                properties = stac_object.properties.to_dict()
            elif isinstance(stac_object, Collection):
                properties = stac_object.summaries
            else:
                properties = stac_object.to_dict()
            return cls(fields=ProjectionFields.model_validate(properties or {}))

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> "ProjectionExtension | None":
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ProjectionFields.model_validate(obj_properties))
