import enum
import json
import uuid
import logging
import inspect
import functools

from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    TypedDict,
    Literal,
    Union,
)
from typing_extensions import ParamSpec, NotRequired
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, validate_call

from openai import OpenAI
from instructor.function_calls import openai_schema


P = ParamSpec("P")
T_Retval = TypeVar("T_Retval", bound=BaseModel)


class OpenAIChatKwargs(TypedDict):
    messages: list[ChatCompletionMessageParam]
    functions: NotRequired[list[dict[str, Any]]]


class FinetuneFormat(enum.Enum):
    MESSAGES = "messages"
    RAW = "raw"


def get_signature_from_fn(fn: Callable[..., Any]) -> str:
    """
    Get the function signature as a string.

    :Example:

    >>> def my_function(a: int, b: int) -> int:
    >>>     return a + b
    >>>
    >>> get_signature_from_fn(my_function)
    "def my_function(a: int, b: int) -> int"

    :param fn: Function to get the signature for.
    :return: Function signature as a string.
    """
    sig = inspect.signature(fn)
    lines = f"def {fn.__name__}{sig}"
    docstring = inspect.getdoc(fn)
    if docstring:
        formatted_docstring = f'"""\n{docstring}\n"""'
    else:
        formatted_docstring = ""
    return f"{lines}\n{formatted_docstring}"


@functools.lru_cache
def format_function(func: Callable[..., Any]) -> str:
    """
    Format a function as a string with docstring and body.
    """
    source_lines = inspect.getsourcelines(func)
    definition = " ".join(source_lines[0]).strip()

    docstring = inspect.getdoc(func)
    if docstring:
        formatted_docstring = f'"""\n{docstring}\n"""'
    else:
        formatted_docstring = ""

    body = inspect.getsource(func)
    body = body.replace(f"def {func.__name__}", "")

    return f"{definition}\n{formatted_docstring}\n{body}"


def is_return_type_base_model_or_instance(func: Callable[..., Any]) -> bool:
    """
    Check if the return type of a function is a pydantic BaseModel or an instance of it.

    :param func: Function to check.
    :return: True if the return type is a pydantic BaseModel or an instance of it.
    """
    return_type = inspect.signature(func).return_annotation
    assert (
        return_type != inspect.Signature.empty
    ), "Must have a return type hint that is a pydantic BaseModel"
    return inspect.isclass(return_type) and issubclass(return_type, BaseModel)


class Instructions:
    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        log_handlers: Optional[list[logging.Handler]] = None,
        finetune_format: FinetuneFormat = FinetuneFormat.MESSAGES,
        indent: int = 2,
        include_code_body: bool = False,
        openai_client: Optional[OpenAI] = None,
    ) -> None:
        """
        Instructions for distillation and dispatch.

        :param name: Name of the instructions.
        :param id: ID of the instructions.
        :param log_handlers: List of log handlers to use.
        :param finetune_format: Format to use for finetuning.
        :param indent: Indentation to use for finetuning.
        :param include_code_body: Whether to include the code body in the finetuning.
        """
        self.name = name
        self.id = id or str(uuid.uuid4())
        self.unique_id = str(uuid.uuid4())
        self.finetune_format = finetune_format
        self.indent = indent
        self.include_code_body = include_code_body
        self.client = openai_client or OpenAI()

        self.logger = logging.getLogger(self.name)
        for handler in log_handlers or []:
            self.logger.addHandler(handler)

    def distil(
        self,
        *args: Any,
        name: Optional[str] = None,
        mode: Literal["distil", "dispatch"] = "distil",
        model: str = "gpt-3.5-turbo",
        fine_tune_format: Optional[FinetuneFormat] = None,
    ) -> Union[
        Callable[P, Union[T_Retval, ChatCompletion]],
        Callable[[Callable[P, T_Retval]], Callable[P, Union[T_Retval, ChatCompletion]]],
    ]:
        """
        Decorator to track the function call and response, supports distillation and dispatch modes.

        If used without arguments, it must be used as a decorator.

        :Example:

        >>> @distil
        >>> def my_function() -> MyModel:
        >>>     return MyModel()
        >>>
        >>> @distil(name="my_function")
        >>> def my_function() -> MyModel:
        >>>     return MyModel()

        :param fn: Function to track.
        :param name: Name of the function to track. Defaults to the function name.
        :param mode: Mode to use for distillation. Defaults to "distil".
        """
        allowed_modes = {"distil", "dispatch"}
        assert mode in allowed_modes, f"Must be in {allowed_modes}"

        if fine_tune_format is None:
            fine_tune_format = self.finetune_format

        def _wrap_distil(
            fn: Callable[P, T_Retval],
        ) -> Callable[P, Union[T_Retval, ChatCompletion]]:
            msg = f"Return type hint for {fn} must subclass `pydantic.BaseModel'"
            assert is_return_type_base_model_or_instance(fn), msg
            return_base_model = inspect.signature(fn).return_annotation

            @functools.wraps(fn)
            def _dispatch(*args: P.args, **kwargs: P.kwargs) -> ChatCompletion:
                openai_kwargs = self.openai_kwargs(
                    name=name if name else fn.__name__,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    base_model=return_base_model,
                )
                return self.client.chat.completions.create(
                    **openai_kwargs,
                    model=model,
                    response_model=return_base_model,  # type: ignore - TODO figure out why `response_model` is not recognized
                )

            @functools.wraps(fn)
            def _distil(*args: P.args, **kwargs: P.kwargs) -> T_Retval:
                resp = fn(*args, **kwargs)
                self.track(
                    fn,
                    args,
                    kwargs,
                    resp,
                    name=name,
                    finetune_format=fine_tune_format,
                )
                return resp

            return _dispatch if mode == "dispatch" else _distil

        if len(args) == 1 and callable(args[0]):
            return _wrap_distil(args[0])

        return _wrap_distil

    @validate_call
    def track(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        resp: BaseModel,
        name: Optional[str] = None,
        finetune_format: FinetuneFormat = FinetuneFormat.MESSAGES,
    ) -> None:
        """
        Track the function call and response in a log file, later used for finetuning.

        :param fn: Function to track.
        :param args: Arguments passed to the function.
        :param kwargs: Keyword arguments passed to the function.
        :param resp: Response returned by the function.
        :param name: Name of the function to track. Defaults to the function name.
        :param finetune_format: Format to use for finetuning. Defaults to "raw".
        """
        name = name if name else fn.__name__
        base_model = type(resp)

        if finetune_format == FinetuneFormat.MESSAGES:
            openai_function_call = openai_schema(base_model).openai_schema
            openai_kwargs = self.openai_kwargs(name, fn, args, kwargs, base_model)
            openai_kwargs["messages"].append(
                {
                    "role": "assistant",
                    "function_call": {
                        "name": base_model.__name__,
                        "arguments": resp.model_dump_json(indent=self.indent),
                    },
                }
            )
            openai_kwargs["functions"] = [openai_function_call]
            self.logger.info(json.dumps(openai_kwargs))

        if finetune_format == FinetuneFormat.RAW:
            function_body = dict(
                fn_name=name,
                fn_repr=format_function(fn),
                args=args,
                kwargs=kwargs,
                resp=resp.model_dump(),
                schema=base_model.model_json_schema(),
            )
            self.logger.info(json.dumps(function_body))

    def openai_kwargs(
        self,
        name: str,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        base_model: type[BaseModel],
    ) -> OpenAIChatKwargs:
        if self.include_code_body:
            func_def = format_function(fn)
        else:
            func_def = get_signature_from_fn(fn)

        str_args = ", ".join(map(str, args))
        str_kwargs = (
            ", ".join(f"{k}={json.dumps(v)}" for k, v in kwargs.items()) or None
        )
        call_args = ", ".join(filter(None, [str_args, str_kwargs]))

        function_body: OpenAIChatKwargs = {
            "messages": [
                {
                    "role": "system",
                    "content": f"Predict the results of this function:\n\n{func_def}",
                },
                {
                    "role": "user",
                    "content": f"Return `{name}({call_args})`",
                },
            ],
        }
        return function_body
