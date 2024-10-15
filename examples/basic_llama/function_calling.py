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

def get_weather(location) -> str:
    return "{'temp':67, 'unit':'F'}"

# Define the function in the format expected by Llama 3.2
llama_tool_call = """[
    {
        "name": "get_weather",
        "description": "Get the weather for a specific location",
        "parameters": {
            "type": "object",
            "required": ["location"],
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for"
                }
            }
        }
    }
]"""

# Create the system prompt with the function definition
instructions = f"""You are a helpful agent. You can use the following function to get weather information:

{llama_tool_call}

If you need to use the function, format your response as:
[get_weather(location="<location>")]

Only use the function when necessary, and provide a natural language response after using it."""

agent = Agent(
    name="Agent",
    model="llama3.2:3b",
    instructions=instructions,
    functions=[get_weather],  # We still pass the function, but it won't be used directly by Llama 3.2
)

messages = [{"role": "user", "content": "What's the weather in NYC?"}]

response = client.run(agent=agent, messages=messages)
#print(response.messages[-1]["content"])

# Parse the response to check if the function was called
response_content = response.messages[-1]["content"]
if "[get_weather(" in response_content:
    # Extract the function call
    start = response_content.index("[get_weather(")
    end = response_content.index(")]", start) + 2
    function_call = response_content[start:end]
    
    # Execute the function
    exec(f"result = {function_call}")
    weather_data = eval("result")
    
    # Update the response with the actual weather data
    updated_response = response_content.replace(function_call, f"The weather in NYC is {weather_data}")
    print(updated_response)
else:
    print("Function was not called in the response")
