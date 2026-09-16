from __future__ import annotations

from enum import StrEnum, auto
from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions import Collection
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
    as_summary_fields,
)
from stac_pydantic_extensions.types import (
    ExtendableStacObject,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import (
        ExtendableStacObject,
    )


class SolSysTargets(StrEnum):
    """Accepted values for the planetary body's target class
    according to the IVOA.
    """

    ASTEROID = auto()
    DWARF_PLANET = auto()
    PLANET = auto()
    SATELLITE = auto()
    COMET = auto()
    EXOPLANET = auto()
    INTERPLANETARY_MEDIUM = auto()
    SAMPLE = auto()
    SKY = auto()
    SPACECRAFT = auto()
    SPACEJUNK = auto()
    STAR = auto()
    CALIBRATION = auto()


class SolSysFields(BaseExtraFields):
    """https://github.com/stac-extensions/ssys"""

    targets: list[str] | None = None
    local_time: str | None = None
    target_class: SolSysTargets | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="ssys")
    )

    def migrate(self, stac_object: ExtendableStacObject, version: str) -> SolSysFields:
        return self


FIELD_MODELS = {"v1.1.1": SolSysFields}


class SolSysExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/ssys/v1.1.1/schema.json"
    )
    prefix: ClassVar[Literal["ssys"]] = "ssys"
    fields: SolSysFields
    version: ClassVar[Literal["v1.1.1"]] = "v1.1.1"
    allowed_objects: ClassVar[set[str]] = {"Item", "Catalog", "Collection"}

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> SolSysExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        properties = cls._extract_properties(stac_object=stac_object)

        # Find the version
        stac_extensions = stac_object.stac_extensions or []
        stac_ext_version = (
            cls.version
            if cls.stac_extension in stac_extensions
            else [
                stac_ext_info.version
                for stac_ext_info in cls.old_stac_extensions
                if stac_ext_info.stac_extension in stac_extensions
            ][0]
        )

        model = FIELD_MODELS[stac_ext_version]
        if isinstance(stac_object, Collection):
            model = as_summary_fields(model)
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
    ) -> SolSysExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=SolSysFields.model_validate(obj_properties))

    @classmethod
    def add_extension(
        cls, stac_object: "ExtendableStacObject", **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the SolSysExtension with the corresponding fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=SolSysFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=SolSysFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")
