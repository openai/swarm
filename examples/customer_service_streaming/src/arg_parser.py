import argparse

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
