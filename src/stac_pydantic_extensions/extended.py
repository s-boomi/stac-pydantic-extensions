from __future__ import annotations

from typing import TYPE_CHECKING, Self, TypeAlias

from pydantic import AnyUrl, ConfigDict, model_validator
from stac_pydantic import Catalog
from stac_pydantic.shared import Asset, StacBaseModel

from stac_pydantic_extensions._registry import extension_registry
from stac_pydantic_extensions.compat.stac_pydantic import (
    Band,
    Collection,
    Item,
    ItemAsset,
    Link,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.extensions._base import BaseExtension

# Main STAC objects: possess a "stac_extensions" attribute that contains
# links to JSON schemas (optional if the extension is still in dev)
StacObject: TypeAlias = Catalog | Collection | Item
# Sub-objects that are usually part of a StacObject, but can receive extensions
# We must make sure their parent has the extension
StacSecondaryObject: TypeAlias = Asset | Band | Link | ItemAsset
# Possible scopes of the extension
ExtendableStacObject: TypeAlias = StacObject | StacSecondaryObject


class ExtensionContainer:
    def _instanciate_extensions(self, stac_object: ExtendableStacObject):
        if isinstance(stac_object, StacObject):
            stac_extensions: list[AnyUrl] | None = stac_object.stac_extensions
            if stac_extensions is not None:
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
