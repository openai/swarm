from unittest.mock import MagicMock
from swarm.types import ChatCompletionMessage, ChatCompletionMessageToolCall, Function
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
import json


def create_mock_response(message, function_calls=[], model="gpt-4o"):
    role = message.get("role", "assistant")
    content = message.get("content", "")
    tool_calls = (
        [
            ChatCompletionMessageToolCall(
                id="mock_tc_id",
                type="function",
                function=Function(
                    name=call.get("name", ""),
                    arguments=json.dumps(call.get("args", {})),
                ),
            )
            for call in function_calls
        ]
        if function_calls
        else None
    )

    return ChatCompletion(
        id="mock_cc_id",
        created=1234567890,
        model=model,
        object="chat.completion",
        choices=[
            Choice(
                message=ChatCompletionMessage(
                    role=role, content=content, tool_calls=tool_calls
                ),
                finish_reason="stop",
                index=0,
            )
        ],
    )


class MockOpenAIClient:
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()

    def set_response(self, response: ChatCompletion):
        """
        Set the mock to return a specific response.
        :param response: A ChatCompletion response to return.
        """
        self.chat.completions.create.return_value = response

    def set_sequential_responses(self, responses: list[ChatCompletion]):
        """
        Set the mock to return different responses sequentially.
        :param responses: A list of ChatCompletion responses to return in order.
        """
        self.chat.completions.create.side_effect = responses

    def assert_create_called_with(self, **kwargs):
        self.chat.completions.create.assert_called_with(**kwargs)


# Initialize the mock client
client = MockOpenAIClient()

# Set a sequence of mock responses
client.set_sequential_responses(
    [
        create_mock_response(
            {"role": "assistant", "content": "First response"},
            [
                {
                    "name": "process_refund",
                    "args": {"item_id": "item_123", "reason": "too expensive"},
                }
            ],
        ),
        create_mock_response({"role": "assistant", "content": "Second"}),
    ]
)

# This should return the first mock response
first_response = client.chat.completions.create()
print(
    first_response.choices[0].message
)  # Outputs: role='agent' content='First response'

# This should return the second mock response
second_response = client.chat.completions.create()
print(
    second_response.choices[0].message
)  # Outputs: role='agent' content='Second response'
