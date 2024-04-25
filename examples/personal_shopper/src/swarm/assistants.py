from pydantic import BaseModel
from typing import Any, Optional
from configs.prompts import EVALUATE_TASK_PROMPT
from configs.general import Colors
from src.utils import get_completion
import json
import time


class Assistant(BaseModel):
    log_flag: bool
    name: Optional[str] = None
    instance: Optional[Any] = None
    tools: Optional[list] = None
    current_task_id: str = None
    sub_assistants: Optional[list] = None
    runs: list = []
    context: Optional[dict] = {}
    planner: str = 'sequential' #default to sequential


    def initialize_history(self):
        self.context['history'] = []

    def add_user_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'user','content':message})

    def add_assistant_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'assistant','content':message})

    def add_tool_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'user','tool':message})

    def print_conversation(self):
        print(f"\n{Colors.GREY}Conversation with Assistant: {self.name}{Colors.ENDC}\n")

        # Group messages by run_id
        messages_by_task_id = {}
        for message in self.context['history']:
            task_id = message['task_id']
            if task_id not in messages_by_task_id:
                messages_by_task_id[task_id] = []
            messages_by_task_id[task_id].append(message)

        # Print messages for each run_id
        for task_id, messages in messages_by_task_id.items():
            print(f"{Colors.OKCYAN}Task ID: {task_id}{Colors.ENDC}")
            for message in messages:
                if 'role' in message and message['role'] == 'user':
                    print(f"{Colors.OKBLUE}User:{Colors.ENDC} {message['content']}")
                elif 'tool' in message:
                    tool_message = message['tool']
                    tool_args = ', '.join([f"{arg}: {value}" for arg, value in tool_message['args'].items()])
                    print(f"{Colors.OKGREEN}Tool:{Colors.ENDC} {tool_message['tool']}({tool_args})")
                elif 'role' in message and message['role'] == 'assistant':
                    print(f"{Colors.HEADER}Assistant:{Colors.ENDC} {message['content']}")
            print("\n")

    def evaluate(self, client, task, plan_log):
        '''Evaluates the assistant's performance on a task'''
        output = get_completion(client, [{'role': 'user', 'content': EVALUATE_TASK_PROMPT.format(task.description, plan_log)}])
        output.content = output.content.replace("'",'"')
        try:
            return json.loads(output.content)
        except json.JSONDecodeError:
            print("An error occurred while decoding the JSON.")
            return None

    def save_conversation(self,test=False):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        if not test:
            filename = f'logs/session_{timestamp}.json'
        else:
            filename = f'tests/test_runs/test_{timestamp}.json'

        with open(filename, 'w') as file:
            json.dump(self.context['history'], file)

    def pass_context(self,assistant):
        '''Passes the context of the conversation to the assistant'''
        assistant.context['history'] = self.context['history']
