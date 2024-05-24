# type: ignore[all]
from functools import wraps
from typing import (
    Callable,
    Protocol,
    TypeVar,
    Union,
    overload,
)
from collections.abc import Awaitable
from typing_extensions import ParamSpec

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from instructor.process_response import handle_response_model
from instructor.retry import retry_async, retry_sync
from instructor.utils import is_async

from instructor.mode import Mode
import logging

logger = logging.getLogger("instructor")

T_Model = TypeVar("T_Model", bound=BaseModel)
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")


class InstructorChatCompletionCreate(Protocol):
    def __call__(
        self,
        response_model: type[T_Model] = None,
        validation_context: dict = None,
        max_retries: int = 1,
        *args: T_ParamSpec.args,
        **kwargs: T_ParamSpec.kwargs,
    ) -> T_Model: ...


class AsyncInstructorChatCompletionCreate(Protocol):
    async def __call__(
        self,
        response_model: type[T_Model] = None,
        validation_context: dict = None,
        max_retries: int = 1,
        *args: T_ParamSpec.args,
        **kwargs: T_ParamSpec.kwargs,
    ) -> T_Model: ...


@overload
def patch(
    client: OpenAI,
    mode: Mode = Mode.TOOLS,
) -> OpenAI: ...


@overload
def patch(
    client: AsyncOpenAI,
    mode: Mode = Mode.TOOLS,
) -> AsyncOpenAI: ...


@overload
def patch(
    create: Callable[T_ParamSpec, T_Retval],
    mode: Mode = Mode.TOOLS,
) -> InstructorChatCompletionCreate: ...


@overload
def patch(
    create: Awaitable[T_Retval],
    mode: Mode = Mode.TOOLS,
) -> InstructorChatCompletionCreate: ...


def patch(
    client: Union[OpenAI, AsyncOpenAI] = None,
    create: Callable[T_ParamSpec, T_Retval] = None,
    mode: Mode = Mode.TOOLS,
) -> Union[OpenAI, AsyncOpenAI]:
    """
    Patch the `client.chat.completions.create` method

    Enables the following features:

    - `response_model` parameter to parse the response from OpenAI's API
    - `max_retries` parameter to retry the function if the response is not valid
    - `validation_context` parameter to validate the response using the pydantic model
    - `strict` parameter to use strict json parsing
    """

    logger.debug(f"Patching `client.chat.completions.create` with {mode=}")

    if create is not None:
        func = create
    elif client is not None:
        func = client.chat.completions.create
    else:
        raise ValueError("Either client or create must be provided")

    func_is_async = is_async(func)

    @wraps(func)
    async def new_create_async(
        response_model: type[T_Model] = None,
        validation_context: dict = None,
        max_retries: int = 1,
        strict: bool = True,
        *args: T_ParamSpec.args,
        **kwargs: T_ParamSpec.kwargs,
    ) -> T_Model:
        response_model, new_kwargs = handle_response_model(
            response_model=response_model, mode=mode, **kwargs
        )
        response = await retry_async(
            func=func,
            response_model=response_model,
            validation_context=validation_context,
            max_retries=max_retries,
            args=args,
            kwargs=new_kwargs,
            strict=strict,
            mode=mode,
        )
        return response

    @wraps(func)
    def new_create_sync(
        response_model: type[T_Model] = None,
        validation_context: dict = None,
        max_retries: int = 1,
        strict: bool = True,
        *args: T_ParamSpec.args,
        **kwargs: T_ParamSpec.kwargs,
    ) -> T_Model:
        response_model, new_kwargs = handle_response_model(
            response_model=response_model, mode=mode, **kwargs
        )
        response = retry_sync(
            func=func,
            response_model=response_model,
            validation_context=validation_context,
            max_retries=max_retries,
            args=args,
            strict=strict,
            kwargs=new_kwargs,
            mode=mode,
        )
        return response

    new_create = new_create_async if func_is_async else new_create_sync

    if client is not None:
        client.chat.completions.create = new_create
        return client
    else:
        return new_create


def apatch(client: AsyncOpenAI, mode: Mode = Mode.TOOLS) -> AsyncOpenAI:
    """
    No longer necessary, use `patch` instead.

    Patch the `client.chat.completions.create` method

    Enables the following features:

    - `response_model` parameter to parse the response from OpenAI's API
    - `max_retries` parameter to retry the function if the response is not valid
    - `validation_context` parameter to validate the response using the pydantic model
    - `strict` parameter to use strict json parsing
    """
    import warnings

    warnings.warn(
        "apatch is deprecated, use patch instead", DeprecationWarning, stacklevel=2
    )
    return patch(client, mode=mode)
