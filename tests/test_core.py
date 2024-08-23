import pytest
from swarm import Swarm, Assistant
from tests.mock_client import MockOpenAIClient, create_mock_response
from unittest.mock import Mock
import json

DEFAULT_RESPONSE_CONTENT = "sample response content"


@pytest.fixture
def mock_openai_client():
    m = MockOpenAIClient()
    m.set_response(
        create_mock_response({"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT})
    )
    return m


def test_run_with_simple_message(mock_openai_client: MockOpenAIClient):
    assistant = Assistant()
    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    response = client.run(assistant=assistant, messages=messages)

    # assert response content
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT


def test_tool_call(mock_openai_client: MockOpenAIClient):
    expected_location = "San Francisco"

    # set up mock to record function calls
    get_weather_mock = Mock()

    def get_weather(location):
        get_weather_mock(location=location)
        return "It's sunny today."

    assistant = Assistant(name="Test Assistant", functions=[get_weather])
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]

    # set mock to return a response that triggers function call
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[
                    {"name": "get_weather", "args": {"location": expected_location}}
                ],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    response = client.run(assistant=assistant, messages=messages)

    get_weather_mock.assert_called_once_with(location=expected_location)
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT


def test_execute_tools_false(mock_openai_client: MockOpenAIClient):
    expected_location = "San Francisco"

    # set up mock to record function calls
    get_weather_mock = Mock()

    def get_weather(location):
        get_weather_mock(location=location)
        return "It's sunny today."

    assistant = Assistant(name="Test Assistant", functions=[get_weather])
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]

    # set mock to return a response that triggers function call
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[
                    {"name": "get_weather", "args": {"location": expected_location}}
                ],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    response = client.run(assistant=assistant, messages=messages, execute_tools=False)
    print(response)

    # assert function not called
    get_weather_mock.assert_not_called()

    # assert tool call is present in last response
    tool_calls = response.messages[-1].get("tool_calls")
    assert tool_calls is not None and len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["function"]["name"] == "get_weather"
    assert json.loads(tool_call["function"]["arguments"]) == {
        "location": expected_location
    }


def test_handoff(mock_openai_client: MockOpenAIClient):
    def transfer_to_assistant2():
        return assistant2

    assistant1 = Assistant(name="Test Assistant 1", functions=[transfer_to_assistant2])
    assistant2 = Assistant(name="Test Assistant 2")

    # set mock to return a response that triggers the handoff
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[{"name": "transfer_to_assistant2"}],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "I want to talk to assistant 2"}]
    response = client.run(assistant=assistant1, messages=messages)

    assert response.assistant == assistant2
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT
