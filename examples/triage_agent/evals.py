from swarm import Swarm
from agents import triage_agent, sales_agent, refunds_agent
from evals_util import evaluate_with_llm_bool, BoolEvalResult
import pytest
import json

client = Swarm()

CONVERSATIONAL_EVAL_SYSTEM_PROMPT = """
You will be provided with a conversation between a user and an agent, as well as a main goal for the conversation.
Your goal is to evaluate, based on the conversation, if the agent achieves the main goal or not.

To assess whether the agent manages to achieve the main goal, consider the instructions present in the main goal, as well as the way the user responds:
is the answer satisfactory for the user or not, could the agent have done better considering the main goal?
It is possible that the user is not satisfied with the answer, but the agent still achieves the main goal because it is following the instructions provided as part of the main goal.
"""


def conversation_was_successful(messages) -> bool:
    conversation = f"CONVERSATION: {json.dumps(messages)}"
    result: BoolEvalResult = evaluate_with_llm_bool(
        CONVERSATIONAL_EVAL_SYSTEM_PROMPT, conversation
    )
    return result.value


def run_and_get_tool_calls(agent, query):
    message = {"role": "user", "content": query}
    response = client.run(
        agent=agent,
        messages=[message],
        execute_tools=False,
    )
    return response.messages[-1].get("tool_calls")


@pytest.mark.parametrize(
    "query,function_name",
    [
        ("I want to make a refund!", "transfer_to_refunds"),
        ("I want to talk to sales.", "transfer_to_sales"),
    ],
)
def test_triage_agent_calls_correct_function(query, function_name):
    tool_calls = run_and_get_tool_calls(triage_agent, query)

    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == function_name


@pytest.mark.parametrize(
    "messages",
    [
        [
            {"role": "user", "content": "Who is the lead singer of U2"},
            {"role": "assistant", "content": "Bono is the lead singer of U2."},
        ],
        [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I assist you today?"},
            {"role": "user", "content": "I want to make a refund."},
            {"role": "tool", "tool_name": "transfer_to_refunds"},
            {"role": "user", "content": "Thank you!"},
            {"role": "assistant", "content": "You're welcome! Have a great day!"},
        ],
    ],
)
def test_conversation_is_successful(messages):
    result = conversation_was_successful(messages)
    assert result == True
