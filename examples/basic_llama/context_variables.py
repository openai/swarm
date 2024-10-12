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

def instructions(context_variables):
    context = context_variables.copy()
    tool_call = context.pop('llama_tool_call', '')
    name = context.get("name", "User")
       # Create the system prompt with the function definition
    return f"""You are a helpful agent. Greet the user by name ({name}). You can use the following function to print account details:

    {tool_call}

    If you need to use the function, format your response as. please note that the context variables is already given to you! 
    You just need to the information EXACTLY as below:
    [print_account_details({context})]

    Only use the function when necessary when using it ONLY RETURN THE FUNCTION CALL, and provide a natural language response after using it."""


def print_account_details(context_variables: dict):
    user_id = context_variables.get("user_id", None)
    name = context_variables.get("name", None)
    print(f"Account Details: {name} {user_id}")
    return "Success"

llama_tool_call = """[
    {
        "name": "print_account_details",
        "description": "Print the account details for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the user"
                },
                "user_id": {
                    "type": "integer",
                    "description": "The user ID"
                }
            },
            "required": ["name", "user_id"]
        }
    }
]"""

context_variables = {
    "name": "James", 
    "user_id": 123,
    "llama_tool_call": llama_tool_call
}
agent = Agent(
    name="Agent",
    model="llama3.2:3b",
    instructions=instructions,
    functions=[print_account_details],
)


response = client.run(
    messages=[{"role": "user", "content": "Hi! what are my account details?"}],
    agent=agent,
    context_variables=context_variables,
)

# Execute the function call
if "[print_account_details(" in response.messages[-1]["content"]:
    result = print_account_details(context_variables)
    print(result)

#print(response.messages[-1]["content"])