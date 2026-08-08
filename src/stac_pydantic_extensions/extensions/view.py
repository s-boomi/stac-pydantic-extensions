from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.model_annotations import Azimuth, Elevation, OffNadir
from stac_pydantic_extensions.types import ExtendableStacObject, ViewGeometryFieldsType

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


class ViewGeometryFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/view/tree/v1.0.0"""

    off_nadir: OffNadir | None = None
    incidence_angle: OffNadir | None = None
    azimuth: Azimuth | None = None
    sun_azimuth: Azimuth | None = None
    sun_elevation: Elevation | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="view")
    )

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> ViewGeometryFieldsType:
        obj = self.model_dump()
        if version == "v1.1.0":
            return ViewGeometryFields.model_validate(obj)

        raise ValueError("Couldn't recognize `sat` version!")


class ViewGeometryFields_V1_1_0(ViewGeometryFields_V1_0_0):
    """https://github.com/stac-extensions/view/tree/v1.1.0"""

    moon_azimuth: Azimuth | None = None
    moon_elevation: OffNadir | None = None

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> ViewGeometryFieldsType:
        return self


class ViewGeometryFields(ViewGeometryFields_V1_1_0):
    """https://github.com/stac-extensions/view"""

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> ViewGeometryFieldsType:
        return self


FIELD_MODELS = {
    "v1.0.0": ViewGeometryFields_V1_0_0,
    "v1.1.0": ViewGeometryFields,
}


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
    fields: ViewGeometryFieldsType
    version: ClassVar[Literal["v1.1.0"]] = "v1.1.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
    maturity_level: ClassVar[MaturityLevel | None] = MaturityLevel.STABLE

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> ViewGeometryExtension | None:
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
    ) -> ViewGeometryExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ViewGeometryFields.model_validate(obj_properties))
