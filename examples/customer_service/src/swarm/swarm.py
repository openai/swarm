import json
from openai import OpenAI
from src.tasks.task import Task,EvaluationTask
from src.swarm.engines.assistants_engine import AssistantsEngine
from src.swarm.engines.local_engine import LocalEngine
from configs.general import Colors, tasks_path

class Swarm:
    def __init__(self,engine_name,tasks=[], persist=False):
        self.tasks = tasks
        self.engine_name = engine_name
        self.engine = None
        self.persist = persist

    def initialize(self):
        """Prepare resources and initialize the environment."""
        client = OpenAI()
        if self.engine_name == 'assistants':
            self.engine = AssistantsEngine(client, self.tasks)
        elif self.engine_name == 'local':
            self.engine = LocalEngine(client, self.tasks, persist=self.persist)
        # Initialize the engine (e.g., load tools, prepare assistants)
        print("\n🐝🐝🐝 Initializing the swarm 🐝🐝🐝\n\n")

        self.engine.initialize()



    def deploy(self,test_mode=False,test_file_paths=None):
        print("\nDeploying the swarm\n\n")
        self.engine.deploy()

    def load_tasks(self):
        self.tasks = []
        with open(tasks_path, 'r') as file:
            tasks_data = json.load(file)
            for task_json in tasks_data:
                task = Task(description=task_json['description'],
                            iterate=task_json.get('iterate', False),
                            evaluate=task_json.get('evaluate', False),
                            assistant=task_json.get('assistant', 'user_interface'))
                self.tasks.append(task)

    def load_test_tasks(self, test_file_paths):
        self.tasks = []  # Clear any existing tasks
        for f in test_file_paths:
            with open(f, 'r') as file:
                for line in file:
                    test_case = json.loads(line)
                    task = EvaluationTask(description=test_case['text'],
                                assistant=test_case.get('assistant', 'user_interface'),
                                groundtruth=test_case.get('groundtruth',None),
                                expected_plan=test_case.get('expected_plan',None),
                                expected_assistant=test_case['expected_assistant'],
                                iterate=test_case.get('iterate', False),  # Add this
                                evaluate=test_case.get('evaluate', False),
                                eval_function=test_case.get('eval_function', 'default')
                                )
                    self.tasks.append(task)

    def add_task(self, task):
        self.tasks.append(task)

