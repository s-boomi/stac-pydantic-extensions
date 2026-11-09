from __future__ import annotations

from typing import TYPE_CHECKING

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
        ProcessingFields_V1_2_0,
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


StacObject = Catalog | Collection | Item
StacSecondaryObject = Asset | Band | Link | ItemAsset
ExtendableStacObject = StacObject | StacSecondaryObject


# For some fields
type AnyVariableData = str | NumType


# Extensions - base
type BaseExtraFieldsType = BaseExtraFields | OldBaseExtraFields
# Extensions - other extensions
type ElectroOpticalFieldsType = (
    ElectroOpticalFields | ElectroOpticalFields_V1_0_0 | ElectroOpticalFields_V1_1_0
)
type RasterFieldsType = RasterFields | RasterFields_V1_0_0 | RasterFields_V1_1_0
type SatelliteFieldsType = (
    SatelliteFields
    | SatelliteFields_V1_0_0
    | SatelliteFields_V1_1_0
    | SatelliteFields_V1_2_0
)
type ViewGeometryFieldsType = (
    ViewGeometryFields | ViewGeometryFields_V1_0_0 | ViewGeometryFields_V1_1_0
)
type ProjectionFieldsType = (
    ProjectionFields
    | ProjectionFields_V1_0_0
    | ProjectionFields_V1_1_0
    | ProjectionFields_V1_2_0
)
type ProcessingFieldsType = (
    ProcessingFields
    | ProcessingFields_V1_0_0
    | ProcessingFields_V1_1_0
    | ProcessingFields_V1_2_0
)
