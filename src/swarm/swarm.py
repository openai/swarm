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
        """
        Initialize the environment and assistants.
        """
        print("\n🐝🐝🐝 Initializing the swarm 🐝🐝🐝\n\n")
        client = OpenAI()
        if self.engine_name == 'local':
            self.engine = LocalEngine(client, tasks=self.tasks, persist=self.persist)
        elif self.engine_name == 'assistants':
            self.engine = AssistantsEngine(client, tasks=self.tasks)
        self.engine.initialize()

    def load_tasks(self):
        self.engine.load_tasks()

    def deploy(self):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        self.engine.deploy()

    def run_tests(self, test_file_paths, n_tests=1):
        """
        Run tests on the tasks specified in the test files.
        """
        self.engine.load_test_tasks(test_file_paths, n_tests)
        self.engine.run_tests()

    def add_task(self, task):
        self.engine.add_task(task)

