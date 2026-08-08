from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import NumType

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.types import (
    ExtendableStacObject,
    SatelliteFieldsType,
    StacObject,
    StacSecondaryObject,
)


class OldSatelliteExtension(OldBaseExtension):
    prefix: str = "sat"
    maturity_level: MaturityLevel = MaturityLevel.STABLE


class SatelliteFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/sat/tree/v1.0.0"""

    platform_international_designator: str | None = None
    orbit_state: str | None = None
    absolute_orbit: NumType | None = None
    relative_orbit: NumType | None = None
    anx_datetime: str | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="sat")
    )

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> SatelliteFieldsType:
        obj = self.model_dump()
        if version == "v1.1.0":
            return SatelliteFields_V1_1_0.model_validate(obj)

        if version == "v1.2.0":
            return SatelliteFields.model_validate(obj)

        raise ValueError("Couldn't recognize `sat` version!")


class SatelliteFields_V1_1_0(SatelliteFields_V1_0_0):
    """https://github.com/stac-extensions/sat/tree/v1.1.0"""

    orbit_cycle: NumType | None = None
    orbit_state_vectors: dict[str, list[NumType]] | None = None

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> SatelliteFieldsType:
        obj = self.model_dump()
        if version == "v1.2.0":
            return SatelliteFields.model_validate(obj)

        raise ValueError("Couldn't recognize version!")


class SatelliteFields_V1_2_0(SatelliteFields_V1_0_0):
    """https://github.com/stac-extensions/sat/tree/v1.2.0"""

    acquisition_station: str | None = None

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> SatelliteFieldsType:
        return self


class SatelliteFields(SatelliteFields_V1_2_0):
    """https://github.com/stac-extensions/sat"""

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> SatelliteFieldsType:
        return self


FIELD_MODELS = {
    "v1.0.0": SatelliteFields_V1_0_0,
    "v1.1.0": SatelliteFields_V1_1_0,
    "v1.2.0": SatelliteFields,
}


class SatelliteExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/sat/v1.2.0/schema.json"
    )
    prefix: ClassVar[Literal["sat"]] = "sat"
    fields: SatelliteFieldsType
    version: ClassVar[Literal["v1.2.0"]] = "v1.2.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
    maturity_level: ClassVar[MaturityLevel] = MaturityLevel.STABLE
    old_stac_extensions: ClassVar[list[OldSatelliteExtension]] = [
        OldSatelliteExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/sat/v1.0.0/schema.json"
            ),
            version="v1.0.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldSatelliteExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/sat/1.1.0/schema.json"
            ),
            version="v1.1.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
    ]

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> SatelliteExtension | None:
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
    ) -> SatelliteExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=SatelliteFields.model_validate(obj_properties))
