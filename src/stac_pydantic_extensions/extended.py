from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import AnyUrl, ConfigDict, model_validator
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions._registry import extension_registry
from stac_pydantic_extensions.types import (
    ExtendableStacObject,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.extensions._base import BaseExtension


class ExtensionContainer:
    def _instanciate_extensions(self, stac_object: ExtendableStacObject):
        if isinstance(stac_object, StacObject):
            stac_extensions: list[AnyUrl] | None = stac_object.stac_extensions
            if stac_extensions is not None and len(stac_extensions) > 0:
                available_extensions = self._extension_index()
                for stac_extension in stac_extensions:
                    ext_key = available_extensions[stac_extension]
                    CurrentExtension = self.fields[ext_key]
                    ext_obj = CurrentExtension.from_stac_object(stac_object)
                    if ext_obj is not None:
                        self._instanciated[ext_key] = ext_obj
                return
        if isinstance(stac_object, StacSecondaryObject):
            return

        return

    def __init__(self, stac_object: ExtendableStacObject):
        self._fields: dict[str, type[BaseExtension]] = dict(
            extension_registry.allowed_extensions_by_stac_item(stac_object)
        )
        self._instanciated: dict[str, BaseExtension] = {}
        self._instanciate_extensions(stac_object)

    @property
    def fields(self) -> dict[str, type[BaseExtension]]:
        return self._fields

    @property
    def field_names(self) -> set[str]:
        return set(self.fields.keys())

    def __dir__(self):
        return sorted(self.fields)

    def __getattr__(self, name: str) -> type[BaseExtension] | BaseExtension:
        if name not in self.field_names:
            raise AttributeError(
                f"{name!r} is not available for this instance of {self.__class__.__name__}"
            )

        if name in self._instanciated:
            return self._instanciated[name]

        return self.fields[name]

    def _extension_index(self) -> dict[AnyUrl, str]:
        return {ext.stac_extension: ext_name for ext_name, ext in self.fields.items()}


class ExtendedItem(StacBaseModel):
    """Facade structure of a STAC component to deal with extension-related material"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stac_object: ExtendableStacObject
    ext: ExtensionContainer | None = None

    def get_ext_schema_uri(self) -> list[AnyUrl] | None:
        if isinstance(self.stac_object, StacObject):
            return self.stac_object.stac_extensions
        return None

    @model_validator(mode="after")
    def init_extensions(self) -> Self:
        self.ext = ExtensionContainer(self.stac_object)
        return self

    def show_ext_names(self) -> set[str]:
        if self.ext is None:
            return set()
        return set(self.ext.field_names)
