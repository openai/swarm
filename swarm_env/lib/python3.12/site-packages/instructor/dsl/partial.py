# --------------------------------------------------------------------------------
# The following code is adapted from a comment on GitHub in the pydantic/pydantic repository by silviumarcu.
# Source: https://github.com/pydantic/pydantic/issues/6381#issuecomment-1831607091
#
# This code is used in accordance with the repository's license, and this reference
# serves as an acknowledgment of the original author's contribution to this project.
# --------------------------------------------------------------------------------

from __future__ import annotations

import pydantic_core
from pydantic import BaseModel, create_model  # type: ignore - remove once Pydantic is updated
from pydantic.fields import FieldInfo
from typing import (
    Any,
    Generic,
    get_args,
    get_origin,
    NoReturn,
    Optional,
    TypeVar,
)
from collections.abc import AsyncGenerator, Generator, Iterable
from copy import deepcopy
from functools import cache

from instructor.mode import Mode
from instructor.utils import extract_json_from_stream, extract_json_from_stream_async

T_Model = TypeVar("T_Model", bound=BaseModel)


class MakeFieldsOptional:
    pass


def _make_field_optional(
    field: FieldInfo,
) -> tuple[Any, FieldInfo]:
    tmp_field = deepcopy(field)

    annotation = field.annotation

    # Handle generics (like List, Dict, etc.)
    if get_origin(annotation) is not None:
        # Get the generic base (like List, Dict) and its arguments (like User in List[User])
        generic_base = get_origin(annotation)
        generic_args = get_args(annotation)

        # Recursively apply Partial to each of the generic arguments
        modified_args = tuple(
            (
                Partial[arg, MakeFieldsOptional]  # type: ignore[valid-type]
                if isinstance(arg, type) and issubclass(arg, BaseModel)
                else arg
            )
            for arg in generic_args
        )

        # Reconstruct the generic type with modified arguments
        tmp_field.annotation = (
            Optional[generic_base[modified_args]] if generic_base else None
        )
        tmp_field.default = None
    # If the field is a BaseModel, then recursively convert it's
    # attributes to optionals.
    elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
        tmp_field.annotation = Optional[Partial[annotation, MakeFieldsOptional]]  # type: ignore[assignment, valid-type]
        tmp_field.default = {}
    else:
        tmp_field.annotation = Optional[field.annotation]  # type: ignore[assignment]
        tmp_field.default = None

    return tmp_field.annotation, tmp_field  # type: ignore


class PartialBase(Generic[T_Model]):
    @classmethod
    @cache
    def get_partial_model(cls) -> type[T_Model]:
        """Return a partial model we can use to validate partial results."""
        assert issubclass(
            cls, BaseModel
        ), f"{cls.__name__} must be a subclass of BaseModel"

        return create_model(
            __model_name=(
                cls.__name__
                if cls.__name__.startswith("Partial")
                else f"Partial{cls.__name__}"
            ),
            __base__=cls,
            __module__=cls.__module__,
            **{
                field_name: _make_field_optional(field_info)
                for field_name, field_info in cls.model_fields.items()
            },
        )  # type: ignore[all]

    @classmethod
    def from_streaming_response(
        cls, completion: Iterable[Any], mode: Mode, **kwargs: Any
    ) -> Generator[T_Model, None, None]:
        json_chunks = cls.extract_json(completion, mode)

        if mode == Mode.MD_JSON:
            json_chunks = extract_json_from_stream(json_chunks)

        yield from cls.model_from_chunks(json_chunks, **kwargs)

    @classmethod
    async def from_streaming_response_async(
        cls, completion: AsyncGenerator[Any, None], mode: Mode, **kwargs: Any
    ) -> AsyncGenerator[T_Model, None]:
        json_chunks = cls.extract_json_async(completion, mode)

        if mode == Mode.MD_JSON:
            json_chunks = extract_json_from_stream_async(json_chunks)

        return cls.model_from_chunks_async(json_chunks, **kwargs)

    @classmethod
    def model_from_chunks(
        cls, json_chunks: Iterable[Any], **kwargs: Any
    ) -> Generator[T_Model, None, None]:
        potential_object = ""
        partial_model = cls.get_partial_model()
        for chunk in json_chunks:
            potential_object += chunk

            obj = pydantic_core.from_json(potential_object or "{}", allow_partial=True)
            obj = partial_model.model_validate(obj, strict=None, **kwargs)
            yield obj

    @classmethod
    async def model_from_chunks_async(
        cls, json_chunks: AsyncGenerator[str, None], **kwargs: Any
    ) -> AsyncGenerator[T_Model, None]:
        potential_object = ""
        partial_model = cls.get_partial_model()
        async for chunk in json_chunks:
            potential_object += chunk
            obj = pydantic_core.from_json(potential_object or "{}", allow_partial=True)
            obj = partial_model.model_validate(obj, strict=None, **kwargs)
            yield obj

    @staticmethod
    def extract_json(
        completion: Iterable[Any], mode: Mode
    ) -> Generator[str, None, None]:
        for chunk in completion:
            try:
                if chunk.choices:
                    if mode == Mode.FUNCTIONS:
                        if json_chunk := chunk.choices[0].delta.function_call.arguments:
                            yield json_chunk
                    elif mode in {Mode.JSON, Mode.MD_JSON, Mode.JSON_SCHEMA}:
                        if json_chunk := chunk.choices[0].delta.content:
                            yield json_chunk
                    elif mode == Mode.TOOLS:
                        if json_chunk := chunk.choices[0].delta.tool_calls:
                            yield json_chunk[0].function.arguments
                    else:
                        raise NotImplementedError(
                            f"Mode {mode} is not supported for MultiTask streaming"
                        )
            except AttributeError:
                pass

    @staticmethod
    async def extract_json_async(
        completion: AsyncGenerator[Any, None], mode: Mode
    ) -> AsyncGenerator[str, None]:
        async for chunk in completion:
            try:
                if chunk.choices:
                    if mode == Mode.FUNCTIONS:
                        if json_chunk := chunk.choices[0].delta.function_call.arguments:
                            yield json_chunk
                    elif mode in {Mode.JSON, Mode.MD_JSON, Mode.JSON_SCHEMA}:
                        if json_chunk := chunk.choices[0].delta.content:
                            yield json_chunk
                    elif mode == Mode.TOOLS:
                        if json_chunk := chunk.choices[0].delta.tool_calls:
                            yield json_chunk[0].function.arguments
                    else:
                        raise NotImplementedError(
                            f"Mode {mode} is not supported for MultiTask streaming"
                        )
            except AttributeError:
                pass


class Partial(Generic[T_Model]):
    """Generate a new class which has PartialBase as a base class.

    Notes:
        This will enable partial validation of the model while streaming.

    Example:
        Partial[SomeModel]
    """

    def __new__(
        cls,
        *args: object,  # noqa :ARG003
        **kwargs: object,  # noqa :ARG003
    ) -> Partial[T_Model]:
        """Cannot instantiate.

        Raises:
            TypeError: Direct instantiation not allowed.
        """
        raise TypeError("Cannot instantiate abstract Partial class.")

    def __init_subclass__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> NoReturn:
        """Cannot subclass.

        Raises:
           TypeError: Subclassing not allowed.
        """
        raise TypeError(f"Cannot subclass {cls.__module__}.Partial")

    def __class_getitem__(
        cls,
        wrapped_class: type[T_Model] | tuple[type[T_Model], type[MakeFieldsOptional]],
    ) -> type[T_Model]:
        """Convert model to one that inherits from PartialBase.

        We don't make the fields optional at this point, we just wrap them with `Partial` so the names of the nested models will be
        `Partial{ModelName}`. We want the output of `model_json_schema()` to
        reflect the name change, but everything else should be the same as the
        original model. During validation, we'll generate a true partial model
        to support partially defined fields.

        """

        make_fields_optional = None
        if isinstance(wrapped_class, tuple):
            wrapped_class, make_fields_optional = wrapped_class

        def _wrap_models(field: FieldInfo) -> tuple[object, FieldInfo]:
            tmp_field = deepcopy(field)

            annotation = field.annotation

            # Handle generics (like List, Dict, etc.)
            if get_origin(annotation) is not None:
                # Get the generic base (like List, Dict) and its arguments (like User in List[User])
                generic_base = get_origin(annotation)
                generic_args = get_args(annotation)

                # Recursively apply Partial to each of the generic arguments
                modified_args = tuple(
                    (
                        Partial[arg]
                        if isinstance(arg, type) and issubclass(arg, BaseModel)
                        else arg
                    )
                    for arg in generic_args
                )

                # Reconstruct the generic type with modified arguments
                tmp_field.annotation = (
                    generic_base[modified_args] if generic_base else None
                )
            # If the field is a BaseModel, then recursively convert it's
            # attributes to optionals.
            elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
                tmp_field.annotation = Partial[annotation]
            return tmp_field.annotation, tmp_field

        return create_model(
            __model_name=(
                wrapped_class.__name__
                if wrapped_class.__name__.startswith("Partial")
                else f"Partial{wrapped_class.__name__}"
            ),
            __base__=(wrapped_class, PartialBase),
            __module__=wrapped_class.__module__,
            **{
                field_name: (
                    _make_field_optional(field_info)
                    if make_fields_optional is not None
                    else _wrap_models(field_info)
                )
                for field_name, field_info in wrapped_class.model_fields.items()
            },
        )  # type: ignore
