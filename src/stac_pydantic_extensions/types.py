from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from stac_pydantic import Catalog
from stac_pydantic.shared import Asset

from stac_pydantic_extensions.compat.stac_pydantic import (
    Band,
    Collection,
    Item,
    ItemAsset,
    Link,
)

if TYPE_CHECKING:
    pass

# Main STAC objects: possess a "stac_extensions" attribute that contains
# links to JSON schemas (optional if the extension is still in dev)
StacObject: TypeAlias = Catalog | Collection | Item
# Sub-objects that are usually part of a StacObject, but can receive extensions
# We must make sure their parent has the extension
StacSecondaryObject: TypeAlias = Asset | Band | Link | ItemAsset
# Possible scopes of the extension
ExtendableStacObject: TypeAlias = StacObject | StacSecondaryObject


# For some fields
AnyVariableData: TypeAlias = str | float | int
