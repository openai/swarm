import argparse
from src.swarm.swarm import Swarm
from src.tasks.task import Task
from configs.general import test_root, test_file, engine_name, persist
from src.validator import validate_all_tools, validate_all_assistants
from src.arg_parser import parse_args, parse_task_input

def main():
    args = parse_args()
    try:
        validate_all_tools(engine_name)
        validate_all_assistants()
    except:
        raise Exception("Validation failed")

    swarm = Swarm(
        engine_name=engine_name, persist=persist)
    swarm.initialize()  # Initialize the engine

    if args.test is not None:
        test_files = args.test
        if len(test_files) == 0:
            test_file_paths = [f"{test_root}/{test_file}"]
        else:
            test_file_paths = [f"{test_root}/{file}" for file in test_files]
        swarm.load_test_tasks(test_file_paths=test_file_paths)
        swarm.deploy(test_mode=True)

    elif args.input:
        # Interactive mode for adding tasks
        while True:
            print("Enter a task (or 'exit' to quit):")
            task_input = input()

            # Check for exit command
            if task_input.lower() == 'exit':
                break

            parsed_args = parse_task_input(task_input)
            new_task = Task(description=parsed_args['description'],
                            iterate=parsed_args['iterate'],
                            evaluate=parsed_args['evaluate'],
                            assistant=parsed_args['assistant'])
            swarm.add_task(new_task)

            # Deploy Swarm with the new task
            swarm.deploy()

    else:
        # Load predefined tasks if any
        # Deploy the Swarm for predefined tasks
        swarm.load_tasks()
        swarm.deploy()

    print("\n\n🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n")


if __name__ == "__main__":
    main()
