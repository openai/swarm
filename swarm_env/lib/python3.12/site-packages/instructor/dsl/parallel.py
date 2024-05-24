from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from collections.abc import Generator
from pydantic import BaseModel
from instructor.function_calls import OpenAISchema, openai_schema
from collections.abc import Iterable

from instructor.mode import Mode

T = TypeVar("T", bound=OpenAISchema)


class ParallelBase:
    def __init__(self, *models: type[OpenAISchema]):
        # Note that for everything else we've created a class, but for parallel base it is an instance
        assert len(models) > 0, "At least one model is required"
        self.models = models
        self.registry = {
            model.__name__ if hasattr(model, "__name__") else str(model): model
            for model in models
        }

    def from_response(
        self,
        response: Any,
        mode: Mode,
        validation_context: Optional[Any] = None,
        strict: Optional[bool] = None,
    ) -> Generator[BaseModel, None, None]:
        #! We expect this from the OpenAISchema class, We should address
        #! this with a protocol or an abstract class... @jxnlco
        assert mode == Mode.PARALLEL_TOOLS, "Mode must be PARALLEL_TOOLS"
        for tool_call in response.choices[0].message.tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments
            yield self.registry[name].model_validate_json(
                arguments, context=validation_context, strict=strict
            )


def get_types_array(typehint: type[Iterable[T]]) -> tuple[type[T], ...]:
    should_be_iterable = get_origin(typehint)
    if should_be_iterable is not Iterable:
        raise TypeError(f"Model should be with Iterable instead if {typehint}")

    if get_origin(get_args(typehint)[0]) is Union:
        # works for Iterable[Union[int, str]]
        the_types = get_args(get_args(typehint)[0])
        return the_types

    if get_origin(get_args(typehint)[0]) is Union:
        # works for Iterable[Union[int, str]]
        the_types = get_args(get_args(typehint)[0])
        return the_types

    # works for Iterable[int]
    return get_args(typehint)


def handle_parallel_model(typehint: type[Iterable[T]]) -> list[dict[str, Any]]:
    the_types = get_types_array(typehint)
    return [
        {"type": "function", "function": openai_schema(model).openai_schema}
        for model in the_types
    ]


def ParallelModel(typehint: type[Iterable[T]]) -> ParallelBase:
    the_types = get_types_array(typehint)
    return ParallelBase(*[model for model in the_types])
