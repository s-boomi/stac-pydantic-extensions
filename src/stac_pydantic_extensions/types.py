from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from stac_pydantic import Catalog
from stac_pydantic.shared import NumType

from stac_pydantic_extensions.compat.stac_pydantic import (
    Asset,
    Band,
    Collection,
    Item,
    ItemAsset,
    Link,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.extensions._base import (
        BaseExtraFields,
        OldBaseExtraFields,
    )
    from stac_pydantic_extensions.extensions.eo import (
        ElectroOpticalFields,
        ElectroOpticalFields_V1_0_0,
        ElectroOpticalFields_V1_1_0,
    )
    from stac_pydantic_extensions.extensions.processing import (
        ProcessingFields,
        ProcessingFields_V1_0_0,
        ProcessingFields_V1_1_0,
    )
    from stac_pydantic_extensions.extensions.proj import (
        ProjectionFields,
        ProjectionFields_V1_0_0,
        ProjectionFields_V1_1_0,
        ProjectionFields_V1_2_0,
    )
    from stac_pydantic_extensions.extensions.raster import (
        RasterFields,
        RasterFields_V1_0_0,
        RasterFields_V1_1_0,
    )
    from stac_pydantic_extensions.extensions.sat import (
        SatelliteFields,
        SatelliteFields_V1_0_0,
        SatelliteFields_V1_1_0,
        SatelliteFields_V1_2_0,
    )
    from stac_pydantic_extensions.extensions.view import (
        ViewGeometryFields,
        ViewGeometryFields_V1_0_0,
        ViewGeometryFields_V1_1_0,
    )


# Main STAC objects: possess a "stac_extensions" attribute that contains
# links to JSON schemas (optional if the extension is still in dev)
StacObject: TypeAlias = Catalog | Collection | Item
# Sub-objects that are usually part of a StacObject, but can receive extensions
# We must make sure their parent has the extension
StacSecondaryObject: TypeAlias = Asset | Band | Link | ItemAsset
# Possible scopes of the extension
ExtendableStacObject: TypeAlias = StacObject | StacSecondaryObject


# For some fields
AnyVariableData: TypeAlias = str | NumType


# Extensions - base
BaseExtraFieldsType: TypeAlias = "BaseExtraFields | OldBaseExtraFields"
# Extensions - other extensions
ElectroOpticalFieldsType: TypeAlias = (
    "ElectroOpticalFields | ElectroOpticalFields_V1_0_0 | ElectroOpticalFields_V1_1_0"
)
RasterFieldsType: TypeAlias = "RasterFields | RasterFields_V1_0_0 | RasterFields_V1_1_0"
SatelliteFieldsType: TypeAlias = "SatelliteFields | SatelliteFields_V1_0_0 | SatelliteFields_V1_1_0 | SatelliteFields_V1_2_0"
ViewGeometryFieldsType: TypeAlias = (
    "ViewGeometryFields | ViewGeometryFields_V1_0_0 | ViewGeometryFields_V1_1_0"
)
ProjectionFieldsType: TypeAlias = "ProjectionFields | ProjectionFields_V1_0_0 | ProjectionFields_V1_1_0 | ProjectionFields_V1_2_0"
ProcessingFieldsType: TypeAlias = (
    "ProcessingFields | ProcessingFields_V1_0_0 | ProcessingFields_V1_1_0"
)
