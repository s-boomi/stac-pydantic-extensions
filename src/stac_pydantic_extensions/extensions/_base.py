from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

if TYPE_CHECKING:
    from stac_pydantic_extensions.extended import (
        ExtendableStacObject,
        StacObject,
        StacSecondaryObject,
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


class BaseExtension(StacBaseModel):
    """Base model for extensions"""

    stac_extension: ClassVar[AnyUrl]
    prefix: ClassVar[str]
    fields: BaseExtraFields
    version: ClassVar[str]
    allowed_objects: ClassVar[set[str]]
    # No maturity level is considered as WIP
    maturity_level: ClassVar[MaturityLevel | None] = None

    # TODO: handle older versions
    # If older versions are found, don't instantiate the fields on the new one
    # Best to use a model_validator - before and restitute the fields
    # On their STAC element of v1.1.0
    def add_schema(self, stac_object: ExtendableStacObject) -> None:
        if isinstance(stac_object, StacObject) and stac_object.stac_extensions is None:
            stac_object.stac_extensions = [self.stac_extension]

        elif (
            isinstance(stac_object, StacObject)
            and stac_object.stac_extensions is not None
            and not self.has_extension(stac_object)
        ):
            stac_object.stac_extensions.append(self.stac_extension)

    def remove_schema(self, stac_object: ExtendableStacObject) -> None:
        if (
            isinstance(stac_object, StacObject)
            and stac_object.stac_extensions is not None
        ):
            stac_object.stac_extensions = [
                uri
                for uri in stac_object.stac_extensions
                if self.stac_extension != str(uri)
            ]

            if len(stac_object.stac_extensions) == 0:
                stac_object.stac_extensions = None

    def has_extension(self, stac_object: ExtendableStacObject) -> bool:
        if isinstance(stac_object, StacObject):
            if self.stac_extension is not None:
                return stac_object.stac_extensions is not None and any(
                    self.stac_extension == uri for uri in stac_object.stac_extensions
                )
        elif isinstance(stac_object, StacSecondaryObject):
            return any(
                field.startswith(self.prefix)
                for field in stac_object.model_fields.keys()
            )

        return False

    def is_from_github(self) -> bool:
        return self.stac_extension.host == "stac-extensions.github.io"

    @classmethod
    def from_stac_object(cls, stac_object: StacObject) -> BaseExtension:  # ty:ignore[invalid-return-type]
        stac_obj_ext = stac_object.stac_extensions
        if stac_obj_ext is not None and cls.stac_extension in stac_obj_ext:
            return cls(fields=BaseExtraFields(**stac_object.to_dict()))

    @classmethod
    def from_stac__secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> BaseExtension:  # ty:ignore[empty-body]
        pass
