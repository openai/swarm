# Standard library imports
from typing import List, Union, Callable

# Local imports
from .types import Agent


def create_triage_agent(
    name: str,
    instructions: Union[str, Callable[[], str]],
    agents: List[Agent],
    add_backlinks: bool = False,
) -> Agent:
    """
    Creates a triage agent that can route conversations to multiple sub-agents.

    This helper function dynamically generates transfer functions for each provided
    agent and optionally adds backlink functions to route back to the triage agent.

    Args:
        name: The name of the triage agent.
        instructions: Instructions for the triage agent (string or callable).
        agents: List of agents that the triage agent can transfer to.
        add_backlinks: If True, adds a transfer function to each sub-agent
                       to route back to the triage agent.

    Returns:
        A configured Agent with transfer functions for all sub-agents.

    Example:
        >>> sales_agent = Agent(name="Sales Agent", instructions="Handle sales")
        >>> refunds_agent = Agent(name="Refunds Agent", instructions="Handle refunds")
        >>> triage = create_triage_agent(
        ...     name="Triage Agent",
        ...     instructions="Route users to the right agent",
        ...     agents=[sales_agent, refunds_agent],
        ...     add_backlinks=True
        ... )
    """
    transfer_functions = []

    def create_transfer_function(agent: Agent) -> Callable:
        """Creates a transfer function for the given agent."""

        def transfer_func():
            """Transfer to {agent_name}."""
            return agent

        # Set function name and docstring dynamically
        agent_name_slug = agent.name.lower().replace(" ", "_")
        transfer_func.__name__ = f"transfer_to_{agent_name_slug}"
        transfer_func.__doc__ = f"Transfer the conversation to the {agent.name}."
        return transfer_func

    # Create transfer functions for all sub-agents
    for agent in agents:
        transfer_func = create_transfer_function(agent)
        transfer_functions.append(transfer_func)

    # Create the triage agent
    triage_agent = Agent(
        name=name,
        instructions=instructions,
        functions=transfer_functions,
    )

    # Add backlinks if requested
    if add_backlinks:

        def transfer_to_triage():
            """Transfer back to the triage agent."""
            return triage_agent

        # Add the backlink function to each sub-agent
        for agent in agents:
            # Create a new list to avoid mutating the original
            agent.functions = list(agent.functions) + [transfer_to_triage]

    return triage_agent
