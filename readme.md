<div align="center">

# 🐝🐝🐝 Swarm 🐝🐝🐝

Swarm is a flexible framework for building, scaling, and orchestrating a single or multi-assistant system with access to tools. Swarm is an open source repo maintained by the OpenAI Solutions team, and is not an official OpenAI product. We want to make Swarm as useful and impactful as possible, so feedback and contributions are strongly encouraged!


</div>

## Table of Contents

- [Project Structure](#project-structure)
- [Setting up](#set-up)
- [Deploying the Swarm](#deploying-the-swarm)
- [Running tests](#running-tests-test_promptsjsonl)
- [Sample configuration](#sample-configuration)
- [Quickstart](#quickstart)

## Project Structure

The Swarm frameworks allows you to create a system of one or multiple agents, with access to tools, to plan and complete tasks. *Note:* Swarm only supports Python currently!

The `configs` directory is where you'll define your assistants and tools. Do not modify the `src` directory.

In `configs`, you will find the following:

- `assistants/`: Contains configuration for each AI assistant.

  - `assistant.json`: Configuration for a specific assistant, including the list of tools it uses and any sub-assistants.

- `tools/`: Contains subdirectories for each tool.

  - Each tool has a subfolder (e.g., `initiate_refund`) and contains:
    - `handler.py`: Python script with the function to execute the tool's task.
    - `tool.json`: JSON file with the tool's metadata, including name, description, and parameters.

- `swarm_tasks.json`: Contains the tasks for the Swarm to complete (see example [here](#example-tasks)).

As a default, your Swarm will have a `user_interface` assistant with access to the `respond_to_user` tool.
To create additional assistants, add a new folder for each assistant in the `configs/assitants/` directory with the desired assistant name, and outline the specs of the assistant in an `assistant.json` file in that folder (see example [here](#sample-configuration)).

To add new tools, add a new folder with the desired tool name to the `configs/tools` folder with a `handler.py` and `tool.json` file (see example [here](#example-tooljson)).

In `logs`, we store the session logs, which contain information about all runs from a Swarm deployment, including the tasks executed and their outcomes.

- Every session is logged and stored in this subfolder as `session_{timestamp}`.

Finally, in `tests`, we have the evaluations to run against our Swarm system (see example [here](#example-test_promptsjsonl)).


## Setting up

### 1. Defining assistants and tools

- An assistant will be initialized for every subfolder in the `assistants` folder based on the `assistant.json` specifications.
  - The name of the assistant is the name of the subfolder.
- Every tool should have a subfolder in the `tools` folder. Define the tool schema in the `tool.json` file and the associated Python function in the `handler.py` file.
  - Set `human_input` flag to true if you want user approval before executing the tool.
- In the `swarm_tasks.json` file, you can define a series of tasks you want the assistants to complete. Tasks can have a designated assistant, or default to the `user_interface` assistant.
- Once you have created the list of tasks in the `swarm_tasks.json` file and have the desired assistants and tools in their respective folders, setup is complete.

### 2. Defining tasks

In `swarm_tasks.json`, users can define tasks for the swarm to execute by creating Task objects. Each task can specify the following parameters:

- **Description**: A description of the task to be performed.
- **Assistant (Optional)**: The name of the assistant to assign the task to. Default is `user_interface` assistant.
- **Iterate (Optional)**: A boolean indicating whether the output of each step should be fed as input to the next step in the plan. Use when tasks require plans with interdependent steps. Default is False.
  - `max_iterations` in `configs/general.py` determines how many times to repeat a step before failing the Task. Default is 5.
- **Evaluate (Optional)**: A boolean indicating whether task should be evaluated to determine if it was successfully completed. Default is False.

### 3. Engine options

_(Note: Swarm only supports the local engine for now by default. Compatable version with Assistants API coming soon.)_


The Swarm framework supports only a local engine now.

- `local_engine`: Uses ChatCompletions and native objects for planning and task execution and stores memory locally.
- _(Coming soon)_ `assistants_engine`: Built on top of the Assistants API, utilizing the API's planning and execution capabilities.

To specify the engine, use the CLI option `--engine` followed by the engine name (e.g., `--engine local`). The default engine is `local`.

## Deploying the Swarm

### Running tasks

The Swarm framework provides a CLI for deploying the swarm, and running tasks.

To deploy the swarm and run all the tasks defined in `swarm_tasks.py` file, simply run the command:

```bash
python3 main.py
```
You can also create and deploy tasks using the CLI by running the following command:

```bash
python3 main.py --input
```

which will start a Swarm session in which you can enter tasks manually. Just write the task description in quotes,with any of the following desired arguments

- **--assistant**: (Optional) The name of the assistant you want to assign the task to. Defaults to "user_interface" if not specified.
- **--evaluate**: (Optional) Flag to indicate whether the task should be evaluated. Default is false.
- **--iterate**: (Optional) Flag to indicate whether the task should iterate. Default is false.

E.g.: `"Send an email summarizing George Washington's wikipedia page to Jason Smith" --iterate --evaluate`

## Running tests `test_prompts.jsonl`

The framework supports three types of evaluations, stored in test_prompts.jsonl. Evals can be any combination of the following types.

- **Groundtruth evals:** Evaluate response accuracy, applicable for assistants using respond_to_user. The output and groundtruth do not need to be exact string matches.
- **Assistant evals:** Test accuracy of request triage and routing to the appropriate assistant.
- **Planning evals:** Evaluate sequential planning of assistants with multiple tools.

You can run tests by using the following command (e.g., `python3 main.py --test`). Test logs will be stored in the `test_runs/` subdirectory of `tests/`.

## Sample configuration

### Example `assistant.json`

Here we have a sample `assistant.json` in the `user_interface` folder. This configuration allows for a hierarchical system of agents, where the `user_interface` assistant can delegate tasks to sub-assistants like `help_center`.

```json
[
  {
    "model": "gpt-4-0125-preview",
    "description": "You are a user interface assistant that handles all interactions with the user. Call this assistant for general questions and when no other assistant is correct for the user query.",
    "log_flag": false,
    "tools": ["respond_to_user"],
    "assistants": ["help_center"],
    "planner": "sequential"
  }
]
```
Note: All Swarm assistants use a sequential planner by default. Feel free to customize your planner in the `configs/prompts.py` file. **More planners coming soon!**

### Example `tool.json`

Here, we define the function following [OpenAI's function calling conventions](https://platform.openai.com/docs/guides/function-calling), with a function name, parameters, and optional description or required field. Also, we can add an optional boolean field `human_input`, which if true requires human confirmation before executing that tool (default is false).

```json
{
  "type": "function",
  "function": {
    "name": "query_docs",
    "description": "Tool to get information about OpenAI products to help users. This JUST querys the data, it does not respond to user.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "A detailed description of what the user wants to know."
        }
      },
      "required": ["query"]
    }
  },
  "human_input": false
}
```

### Example `main.py`

Here we can optionally validate that our tools and assistants are properly defined and adhere to our Pydantic models. Then, we can define a list of Tasks, and initialize the Swarm!

```python
    validate_all_tools()
    validate_all_assistants()
    # #We can triage requests
    swarm = Swarm(engine='local')
```

### Example `Tasks`

In the `swarm_tasks.json`, we define tasks in a JSON format, with the description, and then optional flags such as iterate, evaluate, and assistant. These are automatically loaded and converted to Task() objects when the Swarm is deployed.

```json
[
  {
    "description": "How many free tokens do I get when I sign up for an OpenAI account? Send an email to me@gmail.com containing that answer",
    "iterate": true,
    "evaluate": true
  },
  {
    "description": "What is the square root of 16?"
  }
]
```

### Example `test_prompts.jsonl`

In the `tests` folder, we have our test prompts as described [above](#running-tests-test_promptsjsonl).

```json
{"text": "What is 5+5?", "groundtruth":"10"}
{"text": "Explain the DALL-E editor interface?", "expected_assistant": "help_center"}
{"text": "Explain how to delete my OpenAI key, then email me those instructions to \"me@test.com\"", "expected_plan":[{"tool": "query_docs", "args": {"query": "How to delete OpenAI API key"}},{"tool": "send_email", "args": {"message": "To delete your API key, navigate to the API keys section of the openai.com website, and click \"Revoke key\""},"email_address":"me@test.com"}], "expected_assistant": "help_center"}
```

### Example `session`

Every time we deploy a `Swarm` with a series of tasks, we log the session. Here are the examples logs of
a session where two task was completed.

```json
[
  {
    "task_id": "a4dcfc1c-f91a-4185-b197-997cf003fa02",
    "role": "user",
    "content": "How many free tokens do I get when I sign up for an OpenAI account? Send an email to me@gmail.com containing that answer"
  },
  {
    "task_id": "a4dcfc1c-f91a-4185-b197-997cf003fa02",
    "role": "assistant",
    "content": "Selecting sub-assistant: help_center"
  },
  {
    "task_id": "a4dcfc1c-f91a-4185-b197-997cf003fa02",
    "tool": {
      "tool": "query_docs",
      "args": { "query": "free tokens for new OpenAI account sign up" }
    }
  },
  {
    "task_id": "a4dcfc1c-f91a-4185-b197-997cf003fa02",
    "tool": {
      "tool": "send_email",
      "args": {
        "message": "As an 'Explore' free trial API user, you receive an initial credit of $5 that expires after three months if this is your first OpenAI account. Upgrading to the pay-as-you-go plan will increase your usage limit to $120/month.",
        "email_address": "me@gmail.com"
      }
    }
  }
]
```

## Quickstart

This repository includes three examples of Swarm in action, located in the `examples/` folder:

1. [Customer service](./examples/customer_service/):

- A customer service swarm with a `user_interface` assistant, and a `help_center` assistant with several tools. In this example, some OAI documentation articles are included and stored in a Qdrant VectorDB.
- To run, navigate to `customer_service` folder in `examples/` and run the following:

```python
docker-compose up -d
python3 prep_data.py
python3 main.py
```

2. [Customer service lite](./examples/customer_service_lite/)

- A simplified version of the customer service swarm, featuring just one `user_interface` assistant with access to several tools. While able to manage multi-assistant systems, Swarm can be used effectively for single-assistant systems. In this example, some OAI documentation articles are included and stored in a Qdrant VectorDB.
- To run, navigate to `customer_service_lite` folder in `examples/` and run the following:
```python
docker-compose up -d
python3 prep_data.py
python3 main.py
```

3. [Personal shopper](./examples/personal_shopper/)

- A multi-assistant framework with a `user_interface`, a `refund` assistant, and a `returns` assistant. In this example, we use a Sqlite3 database with customer information and transaction data.
- To run, navigate to `personal_shopper` folder in `examples/` and run the following:

```python
python3 main.py
```
