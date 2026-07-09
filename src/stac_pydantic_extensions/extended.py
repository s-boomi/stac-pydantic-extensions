from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self
from warnings import warn

from pydantic import AnyUrl, ConfigDict, model_validator
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions._registry import extension_registry
from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item
from stac_pydantic_extensions.extensions._base import BaseExtraFields
from stac_pydantic_extensions.types import (
    ExtendableStacObject,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.extensions._base import BaseExtension


class ExtensionContainer:
    """An utilitary class handling scope-available extensions per object"""

    def _instanciate_extensions(self, stac_object: ExtendableStacObject):
        """If the STAC extendable object in question already has extensions available, this
        function will generate one instance for each, at the beginning.
        """
        if isinstance(stac_object, StacObject):
            stac_extensions: list[AnyUrl] | None = stac_object.stac_extensions
            if stac_extensions is not None and len(stac_extensions) > 0:
                available_extensions = self._extension_index()
                for stac_extension in stac_extensions:
                    ext_key = available_extensions[stac_extension]
                    CurrentExtension = self.fields[ext_key]
                    ext_obj = CurrentExtension.from_stac_object(stac_object)
                    if ext_obj is not None:
                        self._instanciated[ext_key] = ext_obj
                return
        if isinstance(stac_object, StacSecondaryObject):
            ext_found = set(
                [
                    attr.split(":")[0]
                    for attr in stac_object.model_dump().keys()
                    if ":" in attr
                ]
            )
            for ext_name in ext_found:
                CurrentExtension = self.fields[ext_name]
                ext_obj = CurrentExtension.from_stac_secondary_object(stac_object)
                if ext_obj is not None:
                    self._instanciated[ext_name] = ext_obj
            return

        return

    def __init__(self, stac_object: ExtendableStacObject):
        self._fields: dict[str, type[BaseExtension]] = dict(
            extension_registry.allowed_extensions_by_stac_item(stac_object)
        )
        self._instanciated: dict[str, BaseExtension] = {}
        self._instanciate_extensions(stac_object)

    @property
    def fields(self) -> dict[str, type[BaseExtension]]:
        return self._fields

    @property
    def field_names(self) -> set[str]:
        return set(self.fields.keys())

    @property
    def declared(self) -> set[str]:
        return set(self._instanciated.keys())

    def __dir__(self):
        return sorted(self.fields)

    def __getattr__(self, name: str) -> type[BaseExtension] | BaseExtension:
        """Returns the class or the instantiated version for the extension"""
        if name not in self.field_names:
            raise AttributeError(
                f"{name!r} is not available for this instance of {self.__class__.__name__}"
            )

        if name in self._instanciated:
            return self._instanciated[name]

        return self.fields[name]

    def _extension_index(self) -> dict[AnyUrl, str]:
        return {
            schema_uri: ext_name
            for ext_name, ext in self.fields.items()
            for schema_uri in ext.schema_uris()
        }

    def add_extension(
        self, ext_name: str, stac_object: ExtendableStacObject, **ext_fields
    ):
        ExtensionToAdd = self.fields[ext_name]
        ext_obj = ExtensionToAdd.add_extension(stac_object=stac_object, **ext_fields)
        self._instanciated[ext_name] = ext_obj

    def remove_extension(
        self, ext_name: str, stac_object: ExtendableStacObject
    ) -> ExtendableStacObject:
        if ext_name not in self._instanciated:
            return stac_object
        ext_to_remove = self._instanciated[ext_name]

        # first remove the schema
        stac_object = ext_to_remove.remove_extension(stac_object)

        del self._instanciated[ext_name]

        return stac_object


class ExtendedItem(StacBaseModel):
    """Facade structure of a STAC component to deal with extension-related material"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stac_object: ExtendableStacObject
    ext: ExtensionContainer | None = None

    def get_ext_schema_uri(self) -> list[AnyUrl] | None:
        if isinstance(self.stac_object, StacObject):
            return self.stac_object.stac_extensions
        return None

    @model_validator(mode="after")
    def init_extensions(self) -> Self:
        """Instantiates self.ext"""
        self.ext = ExtensionContainer(self.stac_object)
        return self

    def show_ext_names(self) -> set[str]:
        if self.ext is None:
            return set()
        return set(self.ext.field_names)

    def add_extension(self, ext_name: str, extra_fields: BaseExtraFields | None = None):
        if self.ext is not None:
            self.ext.add_extension(
                ext_name,
                self.stac_object,
                **extra_fields.to_dict() if extra_fields is not None else {},
            )

    def remove_extension(self, ext_name: str) -> ExtendableStacObject:
        """Removes `ext_name` extension from the STAC object.

        In the case of an Item, goes recursively through assets and bands for a thorough cleaning
        """
        if self.ext is not None:
            new_stac_obj = self.ext.remove_extension(ext_name, self.stac_object)

            if isinstance(new_stac_obj, Item):
                new_stac_obj.assets = {
                    asset_name: ExtendedItem(stac_object=asset).remove_extension(
                        ext_name
                    )
                    for asset_name, asset in new_stac_obj.assets.items()
                }
                # Inspect bands for item
                if new_stac_obj.properties.bands is not None:
                    new_stac_obj.properties.bands = [
                        ExtendedItem(stac_object=band).remove_extension(ext_name)
                        for band in new_stac_obj.properties.bands
                    ]
                # ...And for asset
                for asset_name, asset in new_stac_obj.assets.items():
                    if "bands" in asset._additional_fields:
                        new_stac_obj.assets[asset_name].bands = [
                            ExtendedItem(stac_object=band).remove_extension(ext_name)
                            for band in asset.bands
                        ]

            self.stac_object = new_stac_obj
        return self.stac_object

    def to_dict(
        self, by_alias: bool = True, exclude_unset: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        warn(
            "`to_dict` method is deprecated. Use `model_dump` instead",
            DeprecationWarning,
        )
        return self.model_dump(by_alias=by_alias, exclude_unset=exclude_unset, **kwargs)

    def to_json(
        self, by_alias: bool = True, exclude_unset: bool = True, **kwargs: Any
    ) -> str:
        warn(
            "`to_json` method is deprecated. Use `model_dump_json` instead",
            DeprecationWarning,
        )
        return self.model_dump_json(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def model_dump(  # type: ignore[override]
        self, *, by_alias: bool = True, exclude_unset: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        self._apply_changes()
        return self.stac_object.model_dump(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def model_dump_json(  # type: ignore[override]
        self, *, by_alias: bool = True, exclude_unset: bool = True, **kwargs: Any
    ) -> str:
        self._apply_changes()
        return self.stac_object.model_dump_json(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def _apply_changes(self):
        if self.ext is None:
            return

        obj_as_dict = self.stac_object.model_dump()

        for ext_name in self.ext.declared:
            if isinstance(self.stac_object, Item):
                obj_as_dict["properties"].update(
                    getattr(self.ext, ext_name).fields.model_dump()
                )
            elif isinstance(self.stac_object, Collection):
                obj_as_dict["summaries"].update(
                    getattr(self.ext, ext_name).fields.model_dump()
                )
            else:
                obj_as_dict.update(getattr(self.ext, ext_name).fields.model_dump())

        self.stac_object = self.stac_object.__class__.model_validate(obj_as_dict)
