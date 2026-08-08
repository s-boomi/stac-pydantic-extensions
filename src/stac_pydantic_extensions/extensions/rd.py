from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


class ProductLevel(StrEnum):
    LV1A = "LV1A"
    LV1B = "LV1B"
    LV2A = "LV2A"
    LV2B = "LV2B"
    LV3A = "LV3A"
    LV3B = "LV3B"


class RemoteDataFields(BaseExtraFields):
    """https://github.com/stac-extensions/remote-data"""

    type: str = Field(default="scene")
    product_level: ProductLevel = Field(...)
    sat_id: str = Field(...)
    runs: list[str] | None = None
    parsecs: list[int | float] | None = None
    anomalous_pixels: float | None = None
    earth_sun_distance: int | float | None = None
    flux_capacitor: bool | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="rd")
    )


FIELD_MODELS = {"v1.0.0": RemoteDataFields}


class RemoteDataExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/remote-data/v1.0.0/schema.json"
    )
    prefix: ClassVar[Literal["rd"]] = "rd"
    fields: RemoteDataFields
    version: ClassVar[Literal["v1.0.0"]] = "v1.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> RemoteDataExtension | None:
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
    ) -> RemoteDataExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=RemoteDataFields.model_validate(obj_properties))
