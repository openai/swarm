import json
from src.swarm.swarm import Swarm
from src.tasks.task import Task
from configs.general import Colors, test_file_path, engine, persist
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
        swarm = Swarm(tasks=[task], engine=args.engine, persist=persist)
        swarm.deploy()
    elif args.test:
        swarm = Swarm(engine='local')
        swarm.deploy(test_mode=True, test_file_path=test_file_path)
        pass
    else:
        # #We can triage requests
        swarm = Swarm(engine=args.engine, persist=persist)
        swarm.deploy()

if __name__ == "__main__":
    main()
