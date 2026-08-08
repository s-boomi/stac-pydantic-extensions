from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.types import (
    ProcessingFieldsType,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    pass


class Expression(StacBaseModel):
    format: str
    expression: Any


class ProcessingFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/processing/tree/v1.0.0"""

    lineage: str | None = None
    level: str | None = None
    facility: str | None = None
    software: dict[str, str] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="processing")
    )


class ProcessingFields_V1_1_0(ProcessingFields_V1_0_0):
    """https://github.com/stac-extensions/processing/tree/v1.0.0"""

    expression: Expression | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="processing")
    )


class ProcessingFields_V1_2_0(ProcessingFields_V1_1_0):
    """https://github.com/stac-extensions/processing/tree/v1.1.0"""

    version: str | None = None
    datetime: str | None = None
    software: dict[str, str] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="processing")
    )


class ProcessingFields(ProcessingFields_V1_2_0):
    """https://github.com/stac-extensions/processing"""

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="processing")
    )


class OldProjectionExtension(OldBaseExtension):
    prefix: str = "processing"
    maturity_level: MaturityLevel = MaturityLevel.PROPOSAL


FIELD_MODELS = {
    "v1.0.0": ProcessingFields_V1_0_0,
    "v1.1.0": ProcessingFields_V1_1_0,
    "v1.2.0": ProcessingFields,
}


class ProcessingExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
    )
    prefix: ClassVar[Literal["processing"]] = "processing"
    fields: ProcessingFieldsType
    version: ClassVar[Literal["v1.2.0"]] = "v1.2.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
    maturity_level: ClassVar[MaturityLevel] = MaturityLevel.CANDIDATE
    old_stac_extensions: ClassVar[list[OldProjectionExtension]] = [
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/processing/v1.0.0/schema.json"
            ),
            version="v1.0.0",
            allowed_objects={
                "Item",
                "Collection",
            },
        ),
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/processing/1.1.0/schema.json"
            ),
            version="v1.1.0",
            allowed_objects={
                "Item",
                "Collection",
            },
        ),
    ]

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> ProcessingExtension | None:
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
    ) -> ProcessingExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ProcessingFields.model_validate(obj_properties))
