import json
from openai import OpenAI
from src.tasks.task import Task,EvaluationTask
from src.swarm.engines.assistants_engine import AssistantsEngine
from src.swarm.engines.local_engine import LocalEngine
from configs.general import Colors, tasks_path

class Swarm:
    def __init__(self,engine,tasks=[],persist=False):
        self.tasks = tasks
        self.engine = engine
        self.persist = persist
        if not tasks:
            self.load_tasks()

    def deploy(self, test_mode=False,test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        client = OpenAI()
        #Initialize swarm first
        if self.engine == 'assistants':
            print(f"{Colors.GREY}Selected engine: Assistants{Colors.ENDC}")
            self.engine = AssistantsEngine(client,self.tasks)
            self.engine.deploy(client,test_mode,test_file_path)

        elif self.engine =='local':
            print(f"{Colors.GREY}Selected engine: Local{Colors.ENDC}")
            self.engine = LocalEngine(client,self.tasks, self.persist)
            self.engine.deploy(client,test_mode,test_file_path)

    def load_tasks(self):
        self.tasks = []
        with open(tasks_path, 'r') as file:
            tasks_data = json.load(file)
            for task_json in tasks_data:
                task = Task(description=task_json['description'],
                            iterate=task_json.get('iterate', False),
                            evaluate=task_json.get('evaluate', False),
                            assistant=task_json.get('assistant', 'user_interface'))
                print(task.description)
                self.tasks.append(task)

    def load_test_tasks(self, test_file_path):
        self.tasks = []  # Clear any existing tasks
        with open(test_file_path, 'r') as file:
            for line in file:
                test_case = json.loads(line)
                task = EvaluationTask(description=test_case['text'],
                            assistant=test_case.get('assistant', 'auto'),
                            groundtruth=test_case['groundtruth'],
                            expected_assistant=test_case['expected_assistant'])
                self.tasks.append(task)
