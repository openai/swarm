from swarm import Swarm, Agent
from typing import Optional

client = Swarm()

my_agent = Agent(
    name="Agent",
    instructions="You are a helpful agent.",
)


def pretty_print_messages(messages):
    for message in messages:
        if message["content"] is None:
            continue
        print(f"{message['sender']}: {message['content']}")


messages = []
agent: Optional[Agent] = my_agent  # Explicitly type agent
while True:
    user_input = input("> ")
    messages.append({"role": "user", "content": user_input})

    if agent is None:
        print("Agent is None, cannot continue. Exiting loop.")
        break
    # At this point, mypy should infer agent is of type Agent

    response = client.run(agent=agent, messages=messages)
    messages = response.messages
    agent = response.agent  # This can be Agent | None
    
    if agent is None:
        # If agent becomes None after the run, we exit before 
        # the next iteration's check.
        print("Agent is None post-run, exiting.")
        break
        
    pretty_print_messages(messages)
