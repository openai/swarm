from swarm import Swarm, Assistant

client = Swarm()

english_assistant = Assistant(
    name="English Assistant",
    instructions="You only speak English.",
)

spanish_assistant = Assistant(
    name="Spanish Assistant",
    instructions="You only speak Spanish.",
)


def transfer_to_spanish_assistant():
    """Transfer spanish speaking users immediately."""
    return spanish_assistant


english_assistant.functions.append(transfer_to_spanish_assistant)

messages = [{"role": "user", "content": "Hola. ¿Como estás?"}]
response = client.run(assistant=english_assistant, messages=messages)

print(response.messages[-1]["content"])
