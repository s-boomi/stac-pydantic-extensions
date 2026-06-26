from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)

if TYPE_CHECKING:
    pass


class Expression(StacBaseModel):
    format: str
    expression: Any


class ProcessingFields(BaseExtraFields):
    """https://github.com/stac-extensions/processing"""

    expression: Expression | None = None
    lineage: str | None = None
    level: str | None = None
    facility: str | None = None
    datetime: str | None = None
    version: str | None = None
    software: dict[str, str] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="processing")
    )


class ProcessingExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
    )
    prefix: ClassVar[Literal["processing"]] = "processing"
    fields: ProcessingFields
    version: ClassVar[Literal["v1.2.0"]] = "v1.2.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
