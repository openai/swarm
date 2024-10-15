from swarm.core import Swarm, Agent
import ollama
from typing import List, Dict, Any
import json
from colorama import Fore, Style, init

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


# FUNCTIONS
def transfer_to_spanish_agent():
    """Transfer spanish speaking users immediately."""
    return spanish_agent

def get_weather(location) -> str:
    return "{'temp':67, 'unit':'F'}"

def print_account_details(context_variables: dict):
    user_id = context_variables.get("user_id", None)
    name = context_variables.get("name", None)
    return f"Account Details: {name} {user_id}"

llama_tool_call = """[
    {
        "name": "transfer_to_spanish_agent",
        "description": "Transfer the conversation to a Spanish-speaking agent",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_weather",
        "description": "Get the weather for a specific location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "print_account_details",
        "description": "Print account details for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "context_variables": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The user's ID"
                        },
                        "name": {
                            "type": "string",
                            "description": "The user's name"
                        }
                    }
                }
            },
            "required": ["context_variables"]
        }
    }
]"""

# AGENTS
english_agent = Agent(
    name="English Agent",
    model="llama3.2:3b",
    instructions="You only speak English.",
    functions=[transfer_to_spanish_agent, get_weather, print_account_details],
)

spanish_agent = Agent(
    name="Spanish Agent",
    model="llama3.2:3b",
    instructions="You only speak Spanish.",

)
def instructions(context_variables):
    context = context_variables.copy()
    tool_call = context.pop('llama_tool_call', '')
    name = context.get("name", "User")
    return f"""You only speak English. Your user's name is {name}. You can use the following functions when necessary:

    {tool_call}
    These are the context variables, could be important to use in certain functions: {context}
    To use a function, format your response as follows:
    [function_name({{"param1": "value1", "param2": "value2"}})]

    Guidelines:
    1. Only use functions when they are directly relevant to the user's request.
    2. Provide a natural language response after using a function.
    3. If the user speaks Spanish or requests Spanish assistance, use the transfer_to_spanish_agent function.
    4. For weather requests, use the get_weather function with the specified location.
    5. To display account details, use the print_account_details function with the appropriate context variables.

    Remember to ALWAYS respond in English, unless using the transfer_to_spanish_agent function."""

context_variables = {
    "name": "edward hicksford", 
    "user_id": "@citizenhicks",
    "llama_tool_call": llama_tool_call
}

def check_for_tool_call(messages, context_variables):
    last_message = messages[-1]["content"]
    
    # Check for transfer_to_spanish_agent
    if "to_spanish_agent" in last_message:
        transfer_agent = transfer_to_spanish_agent()
        result = client.run(agent=transfer_agent, messages=messages[:-1])
        return result.messages[-1]["content"], "Spanish Agent"
    
    # Check for get_weather
    elif "[get_weather(" in last_message:
        start = last_message.index("[get_weather(") + len("[get_weather(")
        end = last_message.index(")]", start)
        call_args = last_message[start:end]
        # Extract the location from the call arguments
        location = call_args.split("=")[1].strip('"')
        weather = get_weather(location)
        return f"Weather in {location}: {weather}", "English Agent"
    
    # Check for print_account_details
    elif "[print_account_details(" in last_message:
        context_variables_ = context_variables.copy()
        context_variables_.pop('llama_tool_call', None)
        result = print_account_details(context_variables_)
        return f"{result}", "English Agent"
    
    # If no function call is detected, return the message as is
    else:
        return last_message, "English Agent"


messages = []
english_agent.instructions = instructions
agent = english_agent
while True:
    user_input = input(f"{Fore.BLUE}> {Style.RESET_ALL}")
    messages.append({"role": "user", "content": user_input})

    response = client.run(agent=agent, 
                          messages=messages,
                          context_variables=context_variables)
    messages.append({"role": "assistant", "content": response.messages[-1]["content"]})
    
    # Use the updated check_for_tool_call function
    result, role = check_for_tool_call(messages, context_variables)
    print(f"{role}: {result}\n")
    
