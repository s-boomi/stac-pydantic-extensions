from __future__ import annotations

from enum import StrEnum, auto
from typing import ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.types import (
    AnyVariableData,
    StacObject,
    StacSecondaryObject,
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


FIELD_MODELS = {"v2.3.0": DatacubeFields}


class DatacubeExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/datacube/v2.3.0/schema.json"
    )
    prefix: ClassVar[Literal["cube"]] = "cube"
    fields: DatacubeFields
    version: ClassVar[Literal["v2.3.0"]] = "v2.3.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> DatacubeExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        properties = cls._extract_properties(stac_object=stac_object)

        # Find the version
        stac_ext_version = (
            cls.version
            if cls.stac_extension in stac_object.stac_extensions
            else [
                stac_ext_info.version
                for stac_ext_info in cls.old_stac_extensions
                if stac_ext_info.stac_extension in stac_object.stac_extensions
            ][0]
        )

        model = FIELD_MODELS[stac_ext_version]
        fields = model.model_validate(properties or {})

        if migrate and stac_ext_version != cls.version:
            # First remove old schema and replace by current
            stac_object.stac_extensions = [
                stac_extension
                for stac_extension in stac_object.stac_extensions or []
                if stac_extension not in cls.schema_uris()
            ]
            stac_object.stac_extensions.append(cls.stac_extension)
            fields = fields.migrate(
                stac_object,
                cls.version,
            )

        return cls(
            fields=fields,
            _loaded_version=None if migrate else stac_ext_version,
        )

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> DatacubeExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=DatacubeFields.model_validate(obj_properties))
