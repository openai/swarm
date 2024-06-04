from typing import (
    Callable,
    List,
    Optional,
    Union,
)

# Third-party imports
from pydantic import BaseModel

AssistantFunction = Callable[[], (Union[str, "Assistant", dict, "Result"])]


class Assistant(BaseModel):
    name: str = "Assistant"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[], str]] = "You are a helpful assistant."
    functions: List[AssistantFunction] = []
    tool_choice: str = None
    # messages, context_variables, assistant --> could be a Response object
    post_execute: Optional[Callable[["Response"], "Result"]] = None


class ToolAssistant(Assistant):
    """
    A tool assistant is an assistant that only has one tool function and does not use the model
    """
    def __init__(
            self,
            *,
            name: str,
            model: str = "gpt-4o",
            tool_method: Callable[[dict], "Result"],
    ):
        super().__init__(
            name=name,
            model=model,
            functions=[tool_method],
            instructions="Invoke the only tool function you are provided.  Do nothing else.",
            tool_choice="required",
            post_execute=None,
        )


class Response(BaseModel):
    messages: List = []
    assistant: Optional[Assistant] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an assistant function.

    Attributes:
        value (str): The result value as a string.
        assistant (Assistant): The assistant instance, if applicable.
        context_variables (dict): A dictionary of context variables.
        status (str): The status of the result.
    """

    value: str = ""
    assistant: Optional[Assistant] = None
    context_variables: dict = {}
