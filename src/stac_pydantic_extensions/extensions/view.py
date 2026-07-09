from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.model_annotations import Azimuth, Elevation, OffNadir

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


class ViewGeometryFields(BaseExtraFields):
    """https://github.com/stac-extensions/view"""

    off_nadir: OffNadir | None = None
    incidence_angle: OffNadir | None = None
    azimuth: Azimuth | None = None
    sun_azimuth: Azimuth | None = None
    sun_elevation: Elevation | None = None
    moon_azimuth: Azimuth | None = None
    moon_elevation: OffNadir | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="view")
    )


class OldViewExtension(OldBaseExtension):
    prefix: str = "view"
    allowed_objects: set[str] = {"Item", "Collection"}
    maturity_level: MaturityLevel = MaturityLevel.STABLE


class ViewGeometryExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/view/v1.1.0/schema.json"
    )
    old_stac_extensions: ClassVar[list[OldViewExtension]] = [
        OldViewExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/view/v1.0.0/schema.json"
            ),
            version="v1.0.0",
        )
    ]
    prefix: ClassVar[Literal["view"]] = "view"
    fields: ViewGeometryFields
    version: ClassVar[Literal["v1.1.0"]] = "v1.1.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
    maturity_level: ClassVar[MaturityLevel | None] = MaturityLevel.STABLE

    @classmethod
    def from_stac_object(cls, stac_object: StacObject) -> ViewGeometryExtension | None:
        stac_obj_ext = stac_object.stac_extensions
        if stac_obj_ext is not None and cls.stac_extension in stac_obj_ext:
            if isinstance(stac_object, Item):
                properties = stac_object.properties.to_dict()
            elif isinstance(stac_object, Collection):
                properties = stac_object.summaries
            else:
                properties = stac_object.to_dict()
            return cls(fields=ViewGeometryFields.model_validate(properties or {}))

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> ViewGeometryExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ViewGeometryFields.model_validate(obj_properties))
