from __future__ import annotations
from inspect import isclass
import typing
from pydantic import BaseModel, create_model  # type: ignore - remove once Pydantic is updated
from enum import Enum


from instructor.dsl.partial import Partial
from instructor.function_calls import OpenAISchema


T = typing.TypeVar("T")


class AdapterBase(BaseModel):
    pass


class ModelAdapter(typing.Generic[T]):
    """
    Accepts a response model and returns a BaseModel with the response model as the content.
    """

    def __class_getitem__(cls, response_model: type[BaseModel]) -> type[BaseModel]:
        assert is_simple_type(response_model), "Only simple types are supported"
        tmp = create_model(
            "Response",
            content=(response_model, ...),
            __doc__="Correctly Formated and Extracted Response.",
            __base__=(AdapterBase, OpenAISchema),
        )
        return tmp


def is_simple_type(
    response_model: type[BaseModel] | str | int | float | bool,
) -> bool:
    # ! we're getting mixes between classes and instances due to how we handle some
    # ! response model types, we should fix this in later PRs
    if isclass(response_model) and issubclass(response_model, BaseModel):
        return False

    if typing.get_origin(response_model) in {typing.Iterable, Partial}:
        # These are reserved for streaming types, would be nice to
        return False

    if response_model in {
        str,
        int,
        float,
        bool,
    }:
        return True

    # If the response_model is a simple type like annotated
    if typing.get_origin(response_model) in {
        typing.Annotated,
        typing.Literal,
        typing.Union,
        list,  # origin of List[T] is list
    }:
        return True

    if isclass(response_model) and issubclass(response_model, Enum):
        return True

    return False
