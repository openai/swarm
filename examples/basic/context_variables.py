from swarm import Swarm, Agent

client = Swarm()

# context_variables will be defined globally later
# and accessed by print_account_details directly.

def instructions():
    # This function now takes no arguments.
    # The agent's runtime should handle context for actual instruction execution
    # if needed.
    return "You are a helpful agent. Greet the user."


def print_account_details():  # Removed context_variables argument
    # Accesses global context_variables
    user_id = context_variables.get("user_id", None)
    name = context_variables.get("name", None)
    print(f"Account Details: {name} {user_id}")
    return "Success"


agent = Agent(
    name="Agent",
    instructions=instructions,  # Should now be Callable[[], str]
    functions=[print_account_details],  # Should now be List[Callable[[], str]]
)

context_variables = {"name": "James", "user_id": 123}  # Global definition

response = client.run(
    messages=[{"role": "user", "content": "Hi!"}],
    agent=agent,
    context_variables=context_variables,
)
print(response.messages[-1]["content"])

response = client.run(
    messages=[{"role": "user", "content": "Print my account details!"}],
    agent=agent,
    context_variables=context_variables,
)
print(response.messages[-1]["content"])
