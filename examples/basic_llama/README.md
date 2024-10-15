# Swarm basic - Ollama examples

This folder contains basic examples demonstrating core Swarm capabilities. the original basic examples are modified to work with Ollama. These examples show the simplest implementations of Swarm, with one input message, and a corresponding output. The `simple_loop_no_helpers` has a while loop to demonstrate how to create an interactive Swarm session.

### Examples

1. **agent_handoff.py**

   - Demonstrates how to transfer a conversation from one agent to another.
   - **Usage**: Transfers Spanish-speaking users from an English agent to a Spanish agent.

2. **bare_minimum.py**

   - A bare minimum example showing the basic setup of an agent.
   - **Usage**: Sets up an agent that responds to a simple user message.

3. **context_variables.py**

   - Shows how to use context variables within an agent.
   - **Usage**: Uses context variables to greet a user by name and print account details.

4. **function_calling.py**

   - Demonstrates how to define and call functions from an agent.
   - **Usage**: Sets up an agent that can respond with weather information for a given location.

5. **simple_loop_no_helpers.py**
   - An example of a simple interaction loop without using helper functions.
   - **Usage**: Sets up a loop where the user can continuously interact with the agent, printing the conversation.

6. **all_in_one.py**
   - A more complex example that demonstrates how to use all the features above in one go.
   - **Usage**: Sets up an agent that can transfer conversations, provide weather information, and print account details.

## Running the Examples

To run any of the examples, use the following command:

```shell
python3 <example_name>.py
```
