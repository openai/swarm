![Swarm Logo](https://github.com/openai/swarm-core/assets/25421602/a1961113-e3b5-4341-9208-665a5e7959ee)

# Swarm

A lightweight, stateless multi-assistant orchestration framework.

## Install

```shell
#TODO make this swarm.git when we roll out
pip install git+ssh://git@github.com/openai/swarm-core.git
```

## Usage

```python
from swarm import Swarm, Assistant

client = Swarm()

def transfer_to_assistant_b():
    return assistant_b


assistant_a = Assistant(
    name="Assistant A",
    instructions="You are a helpful assistant.",
    functions=[transfer_to_assistant_b],
)

assistant_b = Assistant(
    name="Assistant B",
    instructions="Only speak in Haikus.",
)

response = client.run(
    assistant=assistant_a,
    messages=[{"role": "user", "content": "I want to talk to assistant B."}],
)

print(response.messages[-1]["content"])
```

```
Hope glimmers brightly,
New paths converge gracefully,
What can I assist?
```

# Overview

Swarm focuses on making assistant **coordination** and **execution** lightweight, highly controllable, and easily testable. It accomplishes this by introudcing a single new, yet familiar, primitive: an `Assistant`.

A Swarm `Assistant` can:

- Execute tools and take multiple steps
- Read/write context variables in its instructions and functions
- Hand off a conversation to another `Assistant`

These primitives are powerful enough to express rich dynamics between tools and networks of assistants, allowing you to build scalable, real-world solutions while avoiding a steep learning curve.

> [!NOTE]  
> Swarm Assistants are not related to Assistants in the Assistants API. They are defined similarly for convenience, but are otherwise completely unrelated. Swarm is entirely powered by the Chat Completions API.

# Why Swarm

Swarm is lightweight, scalable, and highly customizable by design. It is best suited for situations dealing with a large number of independent capabilities and instructions that are difficult to encode into a single prompt.

Unlike the Assistants API, which enables hosted threads and memory management, Swarm runs (almost) entirely on the client and, much like the Chat Completions API, does not store state between calls. This gives developers transparency and fine-grained control over context, steps, and tool calls.

# Examples

Check out `/examples` for inspiration! Learn more about each one in its README.

- `basic`: Simple examples of fundamentals like setup, function calling, handoffs, and context variables
- `triage_assistant`: Simple example of setting up a basic triage step to hand off to the right assistant
- `weather_assistant`: Simple example of function calling
- `airline`: A multi-assistant setup for handling different customer service requests in an airline context
- `support_bot`: A customer service bot which includes a user interface assistant and a help center assistant with several tools
- `personal_shopper`: A personal shopping assistant that can help with making sales and refunding orders

# Documentation

<img width="969" alt="Screenshot 2024-05-22 at 6 52 04 PM" src="https://github.com/openai/swarm-core/assets/25421602/565ccb40-bdf7-4947-92a1-ae41d16a4c8e">

## Running Swarm

Start by instancaiting a Swarm client (which internally just instanciates an `OpenAI` client).

```python
from swarm import Swarm

client = Swarm()
```

### `client.run()`

Swarm's `run()` function is analogous to the `chat.completions.create()` function in the Chat Completions API – it takes `messages` and returns `messages` and saves no state between calls. Importantly, however, it also handles Assistant function execution, hand-offs, context variable references, and can take multiple turns before returning to the user.

At it's core, Swarm's `client.run()` implements the following loop:

1. Get a completion from the current Assistant
2. Execute tool calls and append results
3. Switch Assistant if necessary
4. Update context variables, if necessary
5. If no new function calls, return

#### Arguments

| Argument              | Type        | Description                                                                                                                                            | Default        |
| --------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| **assistant**         | `Assistant` | The (initial) assistant to be called.                                                                                                                  | (required)     |
| **messages**          | `List`      | A list of message objects, identical to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages) | (required)     |
| **context_variables** | `dict`      | A dictionary of additional context variables, available to functions and Assistant instructions                                                        | `{}`           |
| **max_turns**         | `int`       | The maximum number of conversational turns allowed                                                                                                     | `float("inf")` |
| **model_override**    | `str`       | An optional string to override the model being used by an Assistant                                                                                    | `None`         |
| **execute_tools**     | `bool`      | If `False`, interrupt execution and immediately returns `tool_calls` message when an Assistant tries to call a function                                | `True`         |
| **stream**            | `bool`      | If `True`, enables streaming responses                                                                                                                 | `False`        |
| **debug**             | `bool`      | If `True`, enables debug logging                                                                                                                       | `False`        |

Once `client.run()` is finished (after potentially multiple calls to assistants and tools) it will return a `Response` containing all the relevant updated state. Specifically, the new `messages`, the last `Assistant` to be called, and the most up-to-date `context_variables`. You can pass these values (plus new user messages) in to your next execution of `client.run()` to continue the interaction where it left off – much like `chat.completions.create()`. (The `run_demo_loop` function implements an example of a full execution loop in `/swarm/repl/repl.py`.)

#### `Response` Fields

| Field                 | Type        | Description                                                                                                                                                                                                                                                                      |
| --------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **messages**          | `List`      | A list of message objects generated during the conversation. Very similar to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages), but with a `sender` field indicating which `Assistant` the message originated from. |
| **assistant**         | `Assistant` | The last assistant to handle a message.                                                                                                                                                                                                                                          |
| **context_variables** | `dict`      | The same as the input variables, plus any changes.                                                                                                                                                                                                                               |

## Assistants

An `Assistant` simply encapsulates a set of `instructions` with a set of `functions` (plus some additional settings below), and has the capability to hand off execution to other another `Assistant`. 

While it's tempting to personify an `Assistant` as "someone who does X", it can also be used to represent a very specific workflow or step defined by a set of `instructions` and `functions` (e.g. a set of steps, a complex retrieval, single step of data transformation, etc). This allows `Assistant`s to be composed into a network of "agents", "workflows", and "tasks", all represented by the same primitive.

### `Assistant` Fields

| Field            | Type                     | Description                                                                       | Default                          |
| ---------------- | ------------------------ | --------------------------------------------------------------------------------- | -------------------------------- |
| **name**         | `str`                    | The name of the assistant.                                                        | `"Assistant"`                    |
| **model**        | `str`                    | The model to be used by the assistant.                                            | `"gpt-4o"`                       |
| **instructions** | `str` or `func() -> str` | Instructions for the assistant, can be a string or a callable returning a string. | `"You are a helpful assistant."` |
| **functions**    | `List`                   | A list of functions that the assistant can call.                                  | `[]`                             |
| **tool_choice**  | `str`                    | The tool choice for the assistant, if any.                                        | `None`                           |

### Instructions

`Assistant` `instructions` are directly converted into the `system` prompt of a conversation (as the first message). Only the `instructions` of the active `Assistant` will be present at any given time (e.g. if there is an `Assistant` handoff, the `system` prompt will change, but the chat history will not.)

```python
assistant = Assistant(
   instructions="You are a helpful assistant."
)
```

The `instructions` can either be a regular `str`, or a function that returns a `str`. The function can optionally receive a `context_variables` parameter, which will be populated by the `context_variables` passed into `client.run()`.

```python
def instructions(context_variables):
   user_name = context_variables["user_name"]
   return f"Help the user, {user_name}, do whatever they want."

assistant = Assistant(
   instructions=instructions
)
response = client.run(
   assistant=assistant,
   messages=[{"role":"user", "content": "Hi!"}],
   context_variables={"user_name":"John"}
)
print(response.messages[-1]["content"])
```

```
Hi John, how can I assist you today?
```

### Functions

- Swarm `Assistant`s can call python functions directly.
- Function should usually return a `str` (values will be attempted to be cast as a `str`).
- If a function returns an `Assistant`, execution will be transfered to that `Assistant`.
- If a function defines a `context_variables` parameter, it will be populated by the `context_variables` passed into `client.run()`.

```python
def greet(context_variables, language):
   user_name = context_variables["user_name"]
   greeting = "Hola" if language.lower() == "spanish" else "Hello"
   print(f"{greeting}, {user_name}!")
   return "Done"

assistant = Assistant(
   functions=[print_hello]
)

client.run(
   assistant=assistant,
   messages=[{"role": "user", "content": "Usa greet() por favor."}],
   context_variables={"user_name": "John"}
)
```

```
Hola, John!
```

- If an `Assistant` function call has an error (missing function, wrong argument, error) an error response will be appended to the chat so the `Assistant` can recover gracefully.
- If multiple functions are called by the `Assistant`, they will be executed in that order.

#### Handoffs and Updating Context Variables

An `Assistant` can hand off to another `Assistant` by returning it in a `function`.

```python
sales_assistant = Assistant(name="Sales Assistant")

def talk_to_sales():
   print("Hello, World!")
   return "Done"

assistant = Assistant(functions=[talk_to_sales])

response = client.run(assistant, [{"role":"user", "content":"Transfer me to sales."}])
print(response.assistant.name)
```

```
Sales Assistant
```

It can also update the `context_variables` by returning a more complete `Result` object. This can also contain a `value` and an `assistant`, in case you want a single function to return a value, update the assistant, and update the context variables (or any subset of the three).

```python
sales_assistant = Assistant(name="Sales Assistant")

def talk_to_sales():
   print("Hello, World!")
   return Result(
       value="Done",
       assistant=sales_assistant,
       context_variables={"department": "sales"}
   )

assistant = Assistant(functions=[talk_to_sales])

response = client.run(
   assistant=assistant,
   messages=[{"role": "user", "content": "Transfer me to sales"}],
   context_variables={"user_name": "John"}
)
print(response.assistant.name)
print(response.context_variables)
```

```
Sales Assistant
{'department': 'sales', 'user_name': 'John'}
```

> [!NOTE]
> If an `Assistant` tries to hand-off to multiple `Assistant`s, the last one will be used.

#### Function Schemas

Swarm automatically converts functions into a JSON Schema that is passed into Chat Completions `tools`.

- Docstrings are turned into the function `description`.
- Parameters without default values are set to `required`.
- Type hints are mapped to the parameter's `type` (and default to `string`).
- Per-parameter descriptions are not explicitly supported, but should work similarly if just added in the docstring. (In the future Google-style docstring argument parsing may be added.)

```python
def greet(name, age: int, location: str = "New York"):
   """Greets the user. Make sure to get their name and age before calling.

   Args:
      name: Name of the user.
      age: Age of the user.
      location: Best place on earth.
   """
   print(f"Hello {name}, glad you are {age} in {location}!")
```

```javascript
{
   "type": "function",
   "function": {
      "name": "greet",
      "description": "Greets the user. Make sure to get their name and age before calling.\n\nArgs:\n   name: Name of the user.\n   age: Age of the user.\n   location: Best place on earth.",
      "parameters": {
         "type": "object",
         "properties": {
            "name": {
               "type": "string",
               "description": "Name of the user."
            },
            "age": {
               "type": "integer",
               "description": "Age of the user."
            },
            "location": {
               "type": "string",
               "description": "Best place on earth."
            }
         },
         "required": ["name", "age"]
      }
   }
}
```

### Streaming

```python
stream = client.run(assistant, messages, stream=True)
for chunk in stream:
   print(chunk)
```

Uses the same events as [Chat Completions API streaming](https://platform.openai.com/docs/api-reference/streaming). See `process_and_print_streaming_response` in `/swarm/repl/repl.py` as an example.

Two new event types have been added:

- `{"delim":"start"}` and `{"delim":"start"}`, to signal each time an `Assistant` handles a single message (response or function call). This helps identify switches between `Assistant`s.
- `{"response": Response}` will return a `Response` object at the end of a stream with the aggregated (complete) resopnse, for convenience.

## Utils

Use the `run_demo_loop` to test out your swarm! This will run a REPL on your command line. Supports streaming.

```python
from swarm.repl import run_demo_loop
...
run_demo_loop(assistant, stream=True)
```
