from __future__ import annotations

from functools import lru_cache
from typing import ClassVar, Literal

from geojson_pydantic.geometries import Geometry
from geojson_pydantic.types import BBox
from pydantic import AnyUrl, ConfigDict, Field
from stac_pydantic.shared import StacBaseModel
from typing_extensions import Any

from stac_pydantic_extensions import Collection
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    as_summary_fields,
    prefix_alias,
)
from stac_pydantic_extensions.extensions._projjson import ProjJson
from stac_pydantic_extensions.model_annotations import (
    ProjCodeValue,
    ProjWktValue,
)
from stac_pydantic_extensions.types import (
    ExtendableStacObject,
    ProjectionFieldsType,
    StacObject,
    StacSecondaryObject,
)


class Centroid(StacBaseModel):
    lat: float
    lon: float


class OldProjectionExtension(OldBaseExtension):
    prefix: str = "proj"
    maturity_level: MaturityLevel = MaturityLevel.STABLE


class ProjectionFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/projection/tree/v1.0.0"""

    epsg: int = Field(...)
    wkt2: ProjWktValue | None = None
    projjson: ProjJson | dict[str, Any] | None = None  # In the meantime
    geometry: Geometry | None = None
    bbox: BBox | None = None
    centroid: Centroid | None = None
    shape: list[int] | None = None
    transform: list[float | int] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="proj")
    )

    def migrate(
        self, stac_object: ExtendableStacObject, version: str | None = None
    ) -> ProjectionFieldsType:
        return self


class ProjectionFields_V1_1_0(ProjectionFields_V1_0_0):
    """https://github.com/stac-extensions/projection/tree/v1.1.0"""

    epsg: int | None = None

    def migrate(
        self, stac_object: ExtendableStacObject, version: str | None = None
    ) -> ProjectionFieldsType:
        return self


class ProjectionFields_V1_2_0(ProjectionFields_V1_1_0):
    """https://github.com/stac-extensions/projection/tree/v1.2.0"""

    code: ProjCodeValue | None = None

    def migrate(
        self, stac_object: ExtendableStacObject, version: str | None = None
    ) -> ProjectionFieldsType:
        return self


class ProjectionFields(BaseExtraFields):
    """https://github.com/stac-extensions/projection"""

    code: ProjCodeValue | None = None
    wkt2: ProjWktValue | None = None
    projjson: ProjJson | dict[str, Any] | None = None  # Temporary fix
    geometry: Geometry | None = None
    bbox: BBox | None = None  # Removing validator because projection dependent
    centroid: Centroid | None = None
    shape: list[int] | None = None
    transform: list[float | int] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="proj")
    )

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> ProjectionFields:
        return self


FIELD_MODELS = {
    "v1.0.0": ProjectionFields_V1_0_0,
    "v1.1.0": ProjectionFields_V1_1_0,
    "v1.2.0": ProjectionFields_V1_2_0,
    "v2.0.0": ProjectionFields,
}


@lru_cache(maxsize=None)
def as_proj_summary_fields(
    fields_cls: type[ProjectionFields],
) -> type[ProjectionFields]:
    return as_summary_fields(fields_cls)


class ProjectionExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/projection/v2.0.0/schema.json"
    )
    prefix: ClassVar[Literal["proj"]] = "proj"
    fields: ProjectionFieldsType
    version: ClassVar[Literal["v2.0.0"]] = "v2.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection", "Asset", "ItemAsset"}
    maturity_level: ClassVar[MaturityLevel] = MaturityLevel.STABLE
    old_stac_extensions: ClassVar[list[OldProjectionExtension]] = [
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/projection/v1.0.0/schema.json"
            ),
            version="v1.0.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/projection/1.1.0/schema.json"
            ),
            version="v1.1.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/projection/1.2.0/schema.json"
            ),
            version="v1.2.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldProjectionExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/projection/2.0.0/schema.json"
            ),
            version="v2.0.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
    ]

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> ProjectionExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        properties = cls._extract_properties(stac_object=stac_object)

        # Find the version
        stac_extensions = stac_object.stac_extensions or []
        stac_ext_version = (
            cls.version
            if cls.stac_extension in stac_extensions
            else [
                stac_ext_info.version
                for stac_ext_info in cls.old_stac_extensions
                if stac_ext_info.stac_extension in stac_extensions
            ][0]
        )

        model = FIELD_MODELS[stac_ext_version]
        if isinstance(stac_object, Collection):
            model = as_proj_summary_fields(model)
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
    ) -> ProjectionExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ProjectionFields.model_validate(obj_properties))

    @classmethod
    def add_extension(
        cls, stac_object: ExtendableStacObject, **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the RasterExtension with the corresponding fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=ProjectionFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=ProjectionFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")
