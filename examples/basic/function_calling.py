from swarm import Swarm, Assistant

client = Swarm()


def get_weather(location) -> str:
    return "{'temp':67, 'unit':'F'}"


assistant = Assistant(
    name="Assistant",
    instructions="You are a helpful assistant.",
    functions=[get_weather],
)

messages = [{"role": "user", "content": "What's the weather in NYC?"}]

response = client.run(assistant=assistant, messages=messages)
print(response.messages[-1]["content"])
