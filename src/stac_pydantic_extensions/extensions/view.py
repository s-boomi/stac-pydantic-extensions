from typing import Annotated, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions import validators
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)

OffNadir = Annotated[float | int, validators.validate_off_nadir]
Elevation = Annotated[float | int, validators.validate_elevation]
Azimuth = Annotated[float | int, validators.validate_azimuth]


class ViewGeometryFields(BaseExtraFields):
    """https://github.com/stac-extensions/view"""

    off_nadir: OffNadir | None = None
    incidence_angle: OffNadir | None = None
    azimuth: Azimuth | None = None
    sun_azimuth: Azimuth | None = None
    sun_elevation: Elevation | None = None
    moon_azimuth: Azimuth | None = None
    moon_elevation: OffNadir | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="view")
    )


class ViewGeometryExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/view/v1.1.0/schema.json"
    )
    prefix: ClassVar[Literal["view"]] = "view"
    fields: ViewGeometryFields
    version: ClassVar[Literal["v1.1.0"]] = "v1.1.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
