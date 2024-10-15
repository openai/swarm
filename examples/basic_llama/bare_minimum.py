from swarm.core import Swarm, Agent
import ollama
from typing import List, Dict, Any
import json

class OllamaWrapper:
    def __init__(self, client):
        self.client = client
        self.chat = self.ChatCompletions(client)

    class ChatCompletions:
        def __init__(self, client):
            self.client = client
            self.completions = self

        def create(self, **kwargs):
            # Map Swarm parameters to Ollama parameters
            ollama_kwargs = {
                "model": kwargs.get("model"),
                "messages": kwargs.get("messages"),
                "stream": kwargs.get("stream", False),
            }
            
            response = self.client.chat(**ollama_kwargs)
            
            # Wrap the Ollama response to match OpenAI's structure
            class WrappedResponse:
                def __init__(self, ollama_response):
                    self.choices = [
                        type('Choice', (), {
                            'message': type('Message', (), {
                                'content': ollama_response['message']['content'],
                                'role': ollama_response['message']['role'],
                                'tool_calls': None,  # Ollama doesn't support tool calls
                                'model_dump_json': lambda: json.dumps({
                                    'content': ollama_response['message']['content'],
                                    'role': ollama_response['message']['role'],
                                })
                            })
                        })
                    ]

            return WrappedResponse(response)

    def __getattr__(self, name):
        return getattr(self.client, name)

# Initialize Ollama client
ollama_client = ollama.Client(host="http://localhost:11434")

# Wrap Ollama client
wrapped_client = OllamaWrapper(ollama_client)

# Initialize Swarm with wrapped client
client = Swarm(client=wrapped_client)

agent = Agent(
    model="llama3.2:3b",
    name="Agent",
    instructions="You are a helpful agent.",
)

messages = [{"role": "user", "content": "Hi!"}]
response = client.run(agent=agent, messages=messages)

print(response.messages[-1]["content"])
