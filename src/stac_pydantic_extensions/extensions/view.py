from typing import Annotated, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions import validators
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)

OffNadirOrNone = Annotated[float | int, validators.validate_off_nadir]
ElevationOrNone = Annotated[float | int, validators.validate_elevation]
AzimuthOrNone = Annotated[float | int, validators.validate_azimuth]


class ViewGeometryFields(BaseExtraFields):
    """https://github.com/stac-extensions/view"""

    off_nadir: OffNadirOrNone
    incidence_angle: OffNadirOrNone
    azimuth: AzimuthOrNone
    sun_azimuth: AzimuthOrNone
    sun_elevation: ElevationOrNone
    moon_azimuth: AzimuthOrNone
    moon_elevation: OffNadirOrNone

    model_config = ConfigDict(
        extra="forbid", alias_generator=lambda s: prefix_alias(s, prefix="view")
    )


class ViewGeometryExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/view/v1.1.0/schema.json"
    )
    prefix: ClassVar[Literal["view"]] = "view"
    fields: ViewGeometryFields
    version: ClassVar[Literal["v1.1.0"]] = "v1.1.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
