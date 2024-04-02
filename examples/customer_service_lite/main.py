import shlex
import argparse
from src.swarm.swarm import Swarm
from src.tasks.task import Task
from configs.general import test_root, test_file, engine_name, persist
from src.validator import validate_all_tools, validate_all_assistants
from src.arg_parser import parse_args


def main():
    args = parse_args()
    try:
        validate_all_tools(engine_name)
        validate_all_assistants()
    except:
        raise Exception("Validation failed")

    swarm = Swarm(
        engine_name=engine_name, persist=persist)

    if args.test is not None:
        test_files = args.test
        if len(test_files) == 0:
            test_file_paths = [f"{test_root}/{test_file}"]
        else:
            test_file_paths = [f"{test_root}/{file}" for file in test_files]
        swarm = Swarm(engine_name='local')
        swarm.deploy(test_mode=True, test_file_paths=test_file_paths)

    elif args.input:
        # Interactive mode for adding tasks
        while True:
            print("Enter a task (or 'exit' to quit):")
            task_input = input()

            # Check for exit command
            if task_input.lower() == 'exit':
                break

            # Use shlex to parse the task description and arguments
            task_args = shlex.split(task_input)
            task_parser = argparse.ArgumentParser()
            task_parser.add_argument("description", type=str, nargs='?', default="")
            task_parser.add_argument("--iterate", action="store_true", help="Set the iterate flag for the new task.")
            task_parser.add_argument("--evaluate", action="store_true", help="Set the evaluate flag for the new task.")
            task_parser.add_argument("--assistant", type=str, default="user_interface", help="Specify the assistant for the new task.")

            # Parse task arguments
            task_parsed_args = task_parser.parse_args(task_args)

            # Create and add the new task
            new_task = Task(description=task_parsed_args.description,
                            iterate=task_parsed_args.iterate,
                            evaluate=task_parsed_args.evaluate,
                            assistant=task_parsed_args.assistant)
            swarm.add_task(new_task)

            # Deploy Swarm with the new task
            swarm.deploy()
            swarm.tasks.clear()

    else:
        # Load predefined tasks if any
        # Deploy the Swarm for predefined tasks
        swarm.load_tasks()
        swarm.deploy()

    print("\n\n🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n")


if __name__ == "__main__":
    main()
