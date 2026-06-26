from stac_pydantic_extensions.types import AnyVariableData
from enum import StrEnum, auto
from typing import ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)


class VariableFieldType(StrEnum):
    DATA = auto()
    AUXILIARY = auto()


class DimensionType(StrEnum):
    SPATIAL = auto()
    TEMPORAL = auto()
    GEOMETRY = auto()


class DimensionFields(StacBaseModel):
    type: str | DimensionType = Field(...)
    description: str | None = None


class HorizontalSpatialRasterDimension(DimensionFields):
    type: str | DimensionType = DimensionType.SPATIAL


class VerticalSpatialDimension(DimensionFields):
    type: str | DimensionType = DimensionType.SPATIAL


class TemporalDimension(DimensionFields):
    type: str | DimensionType = DimensionType.TEMPORAL


class SpatialVectorDimension(DimensionFields):
    type: str | DimensionType = DimensionType.GEOMETRY


class AdditionalDimension(DimensionFields):
    type: str = Field(...)  # never spatial or geometry


class VariableFields(StacBaseModel):
    dimensions: list[str] = Field(...)
    type: VariableFieldType = Field(...)
    description: str | None = None
    extent: list[AnyVariableData | None] | None = None
    values: list[AnyVariableData] | None = None
    unit: str | None = None
    nodata: AnyVariableData | None = None
    data_type: str | None = None


class DatacubeFields(BaseExtraFields):
    """https://github.com/stac-extensions/datacube"""

    dimensions: dict[str, DimensionFields] = Field(...)
    variables: dict[str, VariableFields] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="cube")
    )


class DatacubeExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/datacube/v2.3.0/schema.json"
    )
    prefix: ClassVar[Literal["cube"]] = "cube"
    fields: DatacubeFields
    version: ClassVar[Literal["v2.3.0"]] = "v2.3.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
