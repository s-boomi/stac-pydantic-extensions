from typing import Self, TypeAlias

from pydantic import AnyUrl, create_model, model_validator
from stac_pydantic import Catalog
from stac_pydantic.shared import Asset, StacBaseModel
from typing_extensions import Any

from stac_pydantic_extensions._registry import extension_registry
from stac_pydantic_extensions.compat.stac_pydantic import (
    Band,
    Collection,
    Item,
    ItemAsset,
    Link,
)

# Main STAC objects: possess a "stac_extensions" attribute that contains
# links to JSON schemas (optional if the extension is still in dev)
StacObject: TypeAlias = Catalog | Collection | Item
# Sub-objects that are usually part of a StacObject, but can receive extensions
# We must make sure their parent has the extension
StacSecondaryObject: TypeAlias = Asset | Band | Link | ItemAsset
# Possible scopes of the extension
ExtendableStacObject: TypeAlias = StacObject | StacSecondaryObject


def _create_extension_container(
    stac_object: ExtendableStacObject,
) -> type[StacBaseModel]:

    # Ensure the dynamic fields mapping is a plain dict so it matches
    # the expected signature overloads of pydantic.create_model
    dynamic_fields: dict[str, Any] = dict(
        extension_registry.allowed_extensions_by_stac_item(stac_object)
    )

    return create_model(
        "ExtensionContainer",
        __base__=StacBaseModel,
        **dynamic_fields,
    )


class ExtendedItem(StacBaseModel):
    """Facade structure of a STAC component to deal with extension-related material"""

    stac_object: ExtendableStacObject
    ext: type[StacBaseModel] | None = None

    def get_ext_schema_uri(self) -> list[AnyUrl] | None:
        if isinstance(self.stac_object, StacObject):
            return self.stac_object.stac_extensions
        return None

    @model_validator(mode="after")
    def init_extensions(self) -> Self:
        self.ext: type[StacBaseModel] = _create_extension_container(self.stac_object)
        return self
