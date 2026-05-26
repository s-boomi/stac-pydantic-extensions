from typing import Self, TypeAlias

from pydantic import AnyUrl, model_validator
from stac_pydantic import Catalog
from stac_pydantic.shared import Asset, StacBaseModel

from stac_pydantic_extensions import (
    Band,
    Collection,
    Item,
    ItemAsset,
    Link,
)
from stac_pydantic_extensions.extensions._base import BaseExtension

# Main STAC objects: possess a "stac_extensions" attribute that contains
# links to JSON schemas (optional if the extension is still in dev)
StacObject: TypeAlias = Catalog | Collection | Item
# Possible scopes of the extension
ExtendableStacObject: TypeAlias = StacObject | Asset | Band | Link | ItemAsset


class ExtendedItem(StacBaseModel):
    """Facade structure of a STAC component to deal with extension-related material"""

    stac_object: ExtendableStacObject
    stac_extensions: list[BaseExtension] = []

    def get_ext_schema_uri(self) -> list[AnyUrl] | None:
        if isinstance(self.stac_object, StacObject):
            return self.stac_object.stac_extensions
        return None

    @model_validator(mode="after")
    def fetch_extensions(self) -> Self:
        schema_uris = self.get_ext_schema_uri()
        if schema_uris is not None:
            pass
        return self
