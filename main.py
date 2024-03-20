import json
from src.swarm.swarm import Swarm
from src.tasks.task import Task
from configs.general import Colors, test_root, test_file, engine
from src.validator import validate_all_tools, validate_all_assistants
from src.arg_parser import parse_args


def main():
    args = parse_args()

    #Run validation
    try:
        validate_all_tools(args.engine)
        validate_all_assistants()
    except ValueError as e:
        print(f"Validation Error: {e}")

    if args.create_task:
        task = Task(description=args.create_task, assistant=args.assistant or "user_interface",
                     evaluate=args.evaluate or False, iterate=args.iterate or False)
        swarm = Swarm(tasks=[task], engine=args.engine)
        swarm.deploy()
    elif args.test:
        test_files = args.test
        if len(test_files) == 0:
            test_file_paths = [f"{test_root}/{test_file}"]
        else:
            test_file_paths = [f"{test_root}/{file}" for file in test_files]    
        swarm = Swarm(engine='local')
        swarm.deploy(test_mode=True, test_file_paths=test_file_paths)
        pass
    else:
        # #We can triage requests
        swarm = Swarm(engine=args.engine)
        swarm.deploy()

if __name__ == "__main__":
    main()
