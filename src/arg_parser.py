import argparse
import shlex

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["local", "assistants"], default="local", help="Choose the engine to use.")
    parser.add_argument("--test", nargs='*', help="Run the tests.")
    parser.add_argument("--create-task", type=str, help="Create a new task with the given description.")
    parser.add_argument("task_description", type=str, nargs="?", default="", help="Description of the task to create.")
    parser.add_argument("--assistant", type=str, help="Specify the assistant for the new task.")
    parser.add_argument("--evaluate", action="store_true", help="Set the evaluate flag for the new task.")
    parser.add_argument("--iterate", action="store_true", help="Set the iterate flag for the new task.")
    parser.add_argument("--input", action="store_true", help="If we want CLI")

    return parser.parse_args()

def parse_task_input(task_input):
    """
    Parses the input string from CLI for task creation, extracting details such as description,
    flags for iteration and evaluation, and the specified assistant.
    """
    # Use shlex to parse the task description and arguments like a shell
    task_args = shlex.split(task_input)

    # Create a parser for the task arguments
    task_parser = argparse.ArgumentParser()
    task_parser.add_argument("description", type=str, nargs='?', default="", help="Description of the task to create.")
    task_parser.add_argument("--iterate", action="store_true", help="Set the iterate flag for the new task.")
    task_parser.add_argument("--evaluate", action="store_true", help="Set the evaluate flag for the new task.")
    task_parser.add_argument("--assistant", type=str, default="user_interface", help="Specify the assistant for the new task.")

    # Parse the arguments
    parsed_args = task_parser.parse_args(task_args)

    # Return the parsed arguments as a dictionary or as a Task object
    return {
        "description": parsed_args.description,
        "iterate": parsed_args.iterate,
        "evaluate": parsed_args.evaluate,
        "assistant": parsed_args.assistant
    }
