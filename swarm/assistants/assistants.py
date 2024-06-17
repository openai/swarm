from typing import List

from swarm import Assistant


def create_triage_assistant(
    name: str = "Triage Assistant",
    instructions: str = (
        "Determine which assistant is best suited to handle the user's request, "
        "and transfer the conversation to that assistant."
    ),
    assistants: List[Assistant] = [],
    add_backlinks: bool = True,
) -> Assistant:
    def transfer_back_to_triage() -> Assistant:
        """Only call this function if a user is asking about a topic that is not handled by the current assistant."""
        return ta

    def make_transfer_function(assistant: Assistant) -> callable:
        def transfer_to_x() -> Assistant:
            return assistant

        return transfer_to_x

    ta = Assistant(name=name, instructions=instructions)

    for assistant in assistants:
        try:
            transfer_to_x = make_transfer_function(assistant)
            transfer_to_x.__name__ = (
                f"transfer_to_{assistant.name.lower().replace(' ', '_')}"
            )
            ta.functions.append(transfer_to_x)

            if add_backlinks:
                assistant.functions.append(transfer_back_to_triage)
        except AttributeError as e:
            print(f"AttributeError processing assistant {assistant.name}: {e}")
            print("Ensure the assistant object has the required attributes.")
        except TypeError as e:
            print(f"TypeError processing assistant {assistant.name}: {e}")
            print("Check the types of the assistant's attributes and methods.")
        except Exception as e:
            print(f"Unexpected error processing assistant {assistant.name}: {e}")
            print("An unexpected error occurred. Please investigate further.")

    return ta


__all__ = ["create_triage_assistant"]
