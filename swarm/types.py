from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional

# Third-party imports
from pydantic import BaseModel

AssistantFunction = Callable[[], Union[str, "Assistant", dict]]


class Assistant(BaseModel):
    name: str = "Assistant"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[], str]] = "You are a helpful assistant."
    functions: List[AssistantFunction] = []
    tool_choice: str = None
    parallel_tool_calls: bool = True


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
    """

    value: str = ""
    assistant: Optional[Assistant] = None
    context_variables: dict = {}
