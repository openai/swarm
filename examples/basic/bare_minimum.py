from swarm import Swarm, Assistant

client = Swarm()

assistant = Assistant(
    name="Assistant",
    instructions="You are a helpful assistant.",
)

messages = [{"role": "user", "content": "Hi!"}]
response = client.run(assistant=assistant, messages=messages)

print(response.messages[-1]["content"])
