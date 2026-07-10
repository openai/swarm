import pytest
from swarm import Swarm, Agent
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
    agent = Agent()
    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    response = client.run(agent=agent, messages=messages)

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

    agent = Agent(name="Test Agent", functions=[get_weather])
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
    response = client.run(agent=agent, messages=messages)

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

    agent = Agent(name="Test Agent", functions=[get_weather])
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
    response = client.run(agent=agent, messages=messages, execute_tools=False)
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
    def transfer_to_agent2():
        return agent2

    agent1 = Agent(name="Test Agent 1", functions=[transfer_to_agent2])
    agent2 = Agent(name="Test Agent 2")

    # set mock to return a response that triggers the handoff
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[{"name": "transfer_to_agent2"}],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "I want to talk to agent 2"}]
    response = client.run(agent=agent1, messages=messages)

    assert response.agent == agent2
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT


def test_streaming_message_sender_after_handoff():
    # In streaming mode, the assistant message stored for each turn must be
    # stamped with the *active* agent's name. After a handoff, the second turn
    # is produced by agent2, so its stored sender must be "Agent 2" -- matching
    # the streamed delta's sender. Regression test for the message dict using
    # the starting agent's name instead of the active agent's.
    class _Delta:
        def __init__(self, d):
            self._d = d

        def json(self):
            return json.dumps(self._d)

    class _Chunk:
        def __init__(self, d):
            self.choices = [Mock(delta=_Delta(d))]

    class _Completions:
        def __init__(self):
            self.n = 0

        def create(self, **kwargs):
            self.n += 1
            if self.n == 1:
                return iter([_Chunk({
                    "role": "assistant", "content": "",
                    "tool_calls": [{
                        "index": 0, "id": "call_1", "type": "function",
                        "function": {"name": "transfer_to_agent2", "arguments": "{}"},
                    }],
                })])
            return iter([_Chunk({"role": "assistant", "content": "Hi from 2"})])

    class _Client:
        def __init__(self):
            self.chat = Mock(completions=_Completions())

    agent2 = Agent(name="Agent 2")

    def transfer_to_agent2():
        return agent2

    agent1 = Agent(name="Agent 1", functions=[transfer_to_agent2])

    client = Swarm(client=_Client())
    stream = client.run(
        agent=agent1,
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    delta_senders, response = [], None
    for chunk in stream:
        if isinstance(chunk, dict):
            if chunk.get("sender"):
                delta_senders.append(chunk["sender"])
            if "response" in chunk:
                response = chunk["response"]

    assistant = [m for m in response.messages if m.get("role") == "assistant"]
    # The post-handoff assistant turn belongs to agent2.
    assert assistant[-1]["sender"] == "Agent 2"
    # ... and the stored sender agrees with the streamed delta.
    assert delta_senders[-1] == "Agent 2"
