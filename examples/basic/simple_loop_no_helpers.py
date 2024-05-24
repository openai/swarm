from swarm import Swarm, Assistant

client = Swarm()

my_assistant = Assistant(
    name="Assistant",
    instructions="You are a helpful assistant.",
)


def pretty_print_messages(messages):
    for message in messages:
        if message["content"] is None:
            continue
        print(f"{message['sender']}: {message['content']}")


messages = []
assistant = my_assistant
while True:
    user_input = input("> ")
    messages.append({"role": "user", "content": user_input})

    response = client.run(assistant=assistant, messages=messages)
    messages = response.messages
    assistant = response.assistant
    pretty_print_messages(messages)
