from __future__ import annotations

from typing import TYPE_CHECKING

from stac_pydantic_extensions.extensions._base import BaseExtension
from stac_pydantic_extensions.extensions.eo import ElectroOpticalExtension
from stac_pydantic_extensions.extensions.ssys import SolSysExtension
from stac_pydantic_extensions.extensions.wmts import WebMapLinksExtension

if TYPE_CHECKING:
    from stac_pydantic_extensions.extended import ExtendableStacObject

AVAILABLE_EXTENSIONS: list[type[BaseExtension]] = [
    ElectroOpticalExtension,
    SolSysExtension,
    WebMapLinksExtension,
]


class _ExtensionRegistry:
    @staticmethod
    def _set_extensions(
        extensions: list[type[BaseExtension]],
    ) -> dict[str, type[BaseExtension]]:
        return {extension.prefix: extension for extension in extensions}

    def __init__(self, extensions: list[type[BaseExtension]]):
        self._ext: dict[str, type[BaseExtension]] = self._set_extensions(extensions)

    @property
    def ext(self) -> dict[str, type[BaseExtension]]:
        return self._ext

    @ext.setter
    def ext(self, _v: dict[str, type[BaseExtension]]) -> None:
        self._ext = _v

    def allowed_extensions_by_stac_item(
        self, stac_object: ExtendableStacObject
    ) -> dict[str, type[BaseExtension]]:
        return {
            k: v
            for k, v in self.ext.items()
            if stac_object.__class__.__name__ in v.allowed_objects
        }

    def create_model_fields_by_stac_item(
        self, stac_object: ExtendableStacObject
    ) -> dict[str, tuple[type, type[BaseExtension]]]:
        return {
            k: (BaseExtension, v)
            for k, v in self.ext.items()
            if stac_object.__class__.__name__ in v.allowed_objects
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} extensions={[ext_name for ext_name in self.ext.keys()]}>"

    def __str__(self) -> str:
        return f"Registered extensions: {', '.join([ext_name for ext_name in self.ext.keys()])}"


# For export
extension_registry = _ExtensionRegistry(AVAILABLE_EXTENSIONS)
