from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions import Collection, Item
from stac_pydantic_extensions.types import (
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import (
        ExtendableStacObject,
    )


def prefix_alias(field_name: str, prefix: str) -> str:
    return prefix + ":" + field_name


class MaturityLevel(IntEnum):
    PROPOSAL = 0
    PILOT = 1
    CANDIDATE = 3
    STABLE = 6
    DEPRECATED = -1


class BaseExtraFields(StacBaseModel):
    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="")
    )


class OldBaseExtraFields(BaseExtraFields):
    pass


class _BaseExtension(StacBaseModel):
    stac_extension: AnyUrl
    prefix: str
    version: str
    allowed_objects: set[str]
    # No maturity level is considered as WIP
    maturity_level: MaturityLevel | None = None


class _BaseClassExtension(StacBaseModel):
    stac_extension: ClassVar[AnyUrl]
    prefix: ClassVar[str]
    version: ClassVar[str]
    allowed_objects: ClassVar[set[str]]
    maturity_level: ClassVar[MaturityLevel | None] = None


class OldBaseExtension(_BaseExtension):
    fields: OldBaseExtraFields | None = None


class BaseExtension(_BaseClassExtension):
    """Base model for extensions"""

    # List of previous STAC extensions
    # Can be left empty some extensions are at their first version
    old_stac_extensions: ClassVar[list[OldBaseExtension]] = []

    fields: BaseExtraFields

    @classmethod
    def schema_uris(cls) -> list[AnyUrl]:
        """List the schema URIs of the extension"""
        return [cls.stac_extension] + [
            old_ext.stac_extension for old_ext in cls.old_stac_extensions
        ]

    @classmethod
    def add_extension(
        cls, stac_object: ExtendableStacObject, **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the extension with fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=BaseExtraFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=BaseExtraFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")

    def remove_extension(
        self, stac_object: ExtendableStacObject
    ) -> ExtendableStacObject:
        """Removes any variation of the extension to the object"""
        if (
            isinstance(stac_object, StacObject)
            and stac_object.stac_extensions is not None
        ):
            ext_to_remove = set(stac_object.stac_extensions).intersection(
                set(self.schema_uris())
            )
            stac_object.stac_extensions = [
                uri
                for uri in stac_object.stac_extensions
                if self.stac_extension not in ext_to_remove
            ]

            if len(stac_object.stac_extensions) == 0:
                stac_object.stac_extensions = None

        # next remove fields
        fields_to_remove = self.fields.model_dump()
        stac_dict = stac_object.model_dump()

        if isinstance(stac_object, Item):
            stac_dict["properties"] = {
                k: v
                for k, v in stac_dict["properties"].items()
                if k not in fields_to_remove
            }
        elif isinstance(stac_object, Collection):
            stac_dict["sumamries"] = {
                k: v
                for k, v in stac_dict["summaries"].items()
                if k not in fields_to_remove
            }
        else:
            stac_dict = {
                k: v for k, v in stac_dict.items() if k not in fields_to_remove
            }

        return stac_object.__class__.model_validate(stac_dict)

    @classmethod
    def has_extension(cls, stac_object: ExtendableStacObject) -> bool:
        """Checks if any variation of the schema exists"""
        if isinstance(stac_object, StacObject):
            if stac_object.stac_extensions is not None:
                return (
                    len(
                        set(stac_object.stac_extensions).intersection(
                            set(cls.schema_uris())
                        )
                    )
                    > 0
                )

        elif isinstance(stac_object, StacSecondaryObject):
            return any(
                field.startswith(cls.prefix)
                for field in stac_object.model_fields.keys()
            )

        return False

    def is_from_github(self) -> bool:
        return self.stac_extension.host == "stac-extensions.github.io"

    @classmethod
    def from_stac_object(cls, stac_object: StacObject) -> BaseExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        if isinstance(stac_object, Item):
            properties = stac_object.properties.to_dict()
        elif isinstance(stac_object, Collection):
            properties = stac_object.summaries
        else:
            properties = stac_object.to_dict()
        # TODO: before that it'd be wise to sort by version used
        # Identify the version first, then generate an object
        return cls(fields=BaseExtraFields.model_validate(properties or {}))

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> BaseExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=BaseExtraFields.model_validate(obj_properties))

    def migrate(self) -> BaseExtension | None:
        return

    def __getattr__(self, name: str):
        allowed_fields = list(self.fields.__dict__.keys())
        if name not in allowed_fields:
            raise AttributeError(
                f"{name} not allowed as a field. Possible fields are {allowed_fields}"
            )
        return getattr(self.fields, name)

    def __setattr__(self, name: str, value: Any):
        allowed_fields = list(self.fields.__dict__.keys())
        if name not in allowed_fields:
            raise AttributeError(
                f"{name} not allowed as a field. Possible fields are {allowed_fields}"
            )
        setattr(self.fields, name, value)
        # TODO: find a way to impact the object too
