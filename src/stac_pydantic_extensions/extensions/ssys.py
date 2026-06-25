from enum import StrEnum, auto
from typing import ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)


class SolSysTargets(StrEnum):
    """Accepted values for the planetary body's target class
    according to the IVOA.
    """

    ASTEROID = auto()
    DWARF_PLANET = auto()
    PLANET = auto()
    SATELLITE = auto()
    COMET = auto()
    EXOPLANET = auto()
    INTERPLANETARY_MEDIUM = auto()
    SAMPLE = auto()
    SKY = auto()
    SPACECRAFT = auto()
    SPACEJUNK = auto()
    STAR = auto()
    CALIBRATION = auto()


class SolSysFields(BaseExtraFields):
    """https://github.com/stac-extensions/ssys"""

    targets: list[str] | None = None
    local_time: str | None = None
    target_class: SolSysTargets | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="ssys")
    )


class SolSysExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/ssys/v1.1.1/schema.json"
    )
    prefix: ClassVar[Literal["ssys"]] = "ssys"
    fields: SolSysFields
    version: ClassVar[Literal["v1.1.1"]] = "v1.1.1"
    allowed_objects: ClassVar[set[str]] = {"Item", "Catalog", "Collection"}
