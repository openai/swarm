import json
import os
from src.utils import get_completion
from configs.general import Colors
from configs.prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_MESSAGE_PROMPT, EVALUATE_TASK_PROMPT
import time
from src.swarm.assistants import Assistant
from src.tasks.task import EvaluationTask
from openai import OpenAI
import importlib


class AssistantsEngine:
    def __init__(self,client,tasks):
        self.client = client
        self.assistants = []
        self.tasks = tasks
        self.thread = self.initialize_thread()


    def initialize_thread(self):
        # Create a Thread for the user's conversation
        thread = self.client.beta.threads.create()
        return thread

    def reset_thread(self):
        # Create a Thread for the user's conversation
        self.thread = self.client.beta.threads.create()

    def load_all_assistants(self):
        base_path = 'assistants'
        tools_base_path = 'tools'

        # Load individual tool definitions from the tools directory
        tool_defs = {}
        for tool_dir in os.listdir(tools_base_path):
            if '__pycache__' in tool_dir:
                continue
            tool_dir_path = os.path.join(tools_base_path, tool_dir)
            if os.path.isdir(tool_dir_path):
                tool_json_path = os.path.join(tool_dir_path, 'tool.json')
                if os.path.isfile(tool_json_path):
                    with open(tool_json_path, 'r') as file:
                        # Assuming the JSON file contains a list of tool definitions
                        tool_def = json.load(file)
                        tool_defs[tool_def['function']['name']] = tool_def['function']
        # Load assistants and their tools
        for assistant_dir in os.listdir(base_path):
            if '__pycache__' in assistant_dir:
                continue
            assistant_config_path = os.path.join(base_path, assistant_dir, "assistant.json")
            if os.path.exists(assistant_config_path):
                with open(assistant_config_path, "r") as file:
                    assistant_config = json.load(file)[0]

                    assistant_name = assistant_config.get('name', assistant_dir)
                    log_flag = assistant_config.pop('log_flag', False)

                    # List of tool names from the assistant's config
                    assistant_tools_names = assistant_config.get('tools', [])

                    # Build the list of tool definitions for this assistant
                    assistant_tools = [tool_defs[name] for name in assistant_tools_names if name in tool_defs]

                    # Create or update the assistant instance
                    existing_assistants = self.client.beta.assistants.list()
                    loaded_assistant = next((a for a in existing_assistants if a.name == assistant_name), None)

                    if loaded_assistant:
                        assistant_tools = [{'type': 'function', 'function': tool_defs[name]} for name in assistant_tools_names if name in tool_defs]
                        assistant_config['tools'] = assistant_tools
                        assistant_config['name']=assistant_name

                        loaded_assistant = self.client.beta.assistants.create(**assistant_config)
                        print(f"Assistant '{assistant_name}' created.\n")

                    asst_object = Assistant(name=assistant_name, log_flag=log_flag, instance=loaded_assistant, tools=assistant_tools)
                    self.assistants.append(asst_object)


    def initialize_and_display_assistants(self):
            """
            Loads all assistants and displays their information.
            """
            self.load_all_assistants()

            for asst in self.assistants:
                print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
                print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
                if asst.instance and hasattr(asst.instance, 'tools'):
                    print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {asst.instance.tools} \n')
                else:
                    print(f"{Colors.OKGREEN}Tools:{Colors.ENDC} Not available \n")


    def get_assistant(self, assistant_name):

        for assistant in self.assistants:
            if assistant.name == assistant_name:
                return assistant
        print('No assistant found')
        return None

    def triage_request(self, message, test_mode):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
        #determine the appropriate assistant for the message
        assistant_name = self.determine_appropriate_assistant(message)
        assistant = self.get_assistant(assistant_name)

        if assistant:
            print(
            f"{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}"
            )
            assistant.add_assistant_message('Selected Assistant: '+assistant.name)
            return assistant
        #else
        if not test_mode:
            print('No assistant found')
        return None


    def determine_appropriate_assistant(self, message):
        triage_message = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
        triage_message.append(
            {
                "role": "user",
                "content": TRIAGE_MESSAGE_PROMPT.format(message, [asst.instance for asst in self.assistants]),
            }
        )
        response = get_completion(self.client, triage_message)
        return response.content


    def run_request(self, request, assistant,test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=request
        )

        # Initialize run
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=assistant.instance.id
        )

        # Monitor the run status in a loop
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )

            if run.status in ["queued", "in_progress"]:
                time.sleep(2)  # Wait before checking the status again
                if not test_mode:
                    print('waiting for run')
            elif run.status == "requires_action":
                tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                self.handle_tool_call(tool_call, run)
                # Re-submitting the tool outputs and continue the loop

            elif run.status in ["completed","expired", "cancelling", "cancelled", "failed"]:
                if not test_mode:
                    print(f'\nrun {run.status}')
                break

        if assistant.log_flag:
            self.store_messages()
        # Retrieve and return the response (only if completed)
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        assistant_response = next((msg for msg in messages.data if msg.role == 'assistant' and msg.content), None)


        if assistant_response:
            assistant_response_text = assistant_response.content[0].text.value
            if not test_mode:
                print(f"{Colors.RED}Response:{Colors.ENDC} {assistant_response_text}", "\n")
            return assistant_response_text
        return "No response from the assistant."


    def handle_tool_call(self, tool_call, run):
        tool_name = tool_call.function.name
        tool_dir = os.path.join(os.getcwd(), 'tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')

        # Dynamically import the handler function from the handler.py file
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f"{tool_name}_handler", handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name+ '_assistants')

            # Prepare the arguments for the handler function
            handler_args = {'tool_id': tool_call.id}
            tool_args = json.loads(tool_call.function.arguments)
            for arg_name, arg_value in tool_args.items():
                if arg_value is not None:
                    handler_args[arg_name] = arg_value

            # Call the handler function with arguments
            print(f"{Colors.HEADER}Running Tool:{Colors.ENDC} {tool_name}")
            print(handler_args)
            tool_response = tool_handler(**handler_args)

            # Submit the tool response back to the thread
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"result": tool_response}),
                    }
                ],
            )
        else:
            print(f"No handler found for tool {tool_name}")

    def store_messages(self, filename="threads/thread_data.json"):

        thread = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        # Extract the required fields from each message in the thread
        messages = []
        for message in thread.data:
            role = message.role
            run_id = message.run_id
            assistant_id = message.assistant_id
            thread_id = message.thread_id
            created_at = message.created_at
            content_value = message.content[0].text.value
            messages.append({
                'role': role,
                'run_id': run_id,
                'assistant_id': assistant_id,
                'thread_id': thread_id,
                'created_at': created_at,
                'content': content_value
            })
        try:
            with open(filename, 'r') as file:
                existing_threads = json.load(file)

        except:
            existing_threads = []


        # Convert the OpenAI object to a serializable format (e.g., a dictionary)
        # Append new threads
        existing_threads.append(messages)
        # Save back to the file
        try:
            with open(filename, 'w') as file:
                json.dump(existing_threads, file, indent=4)
        except Exception as e:
            print(f"Error while saving to file: {e}")


    def run_task(self, task,test_mode):
            """
            Processes a given task. If the assistant is set to 'auto', it determines the appropriate
            assistant using triage_request. Otherwise, it uses the specified assistant.
            """
            if not test_mode:
                print(
            f"{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            else:
                print(
            f"{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )

            if task.assistant == 'auto':
                # Triage the request to determine the appropriate assistant
                assistant = self.triage_request(task.description,test_mode)
            else:
                # Fetch the specified assistant
                assistant = self.get_assistant(task.assistant)
                print(
                f"{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}"
                )

            if test_mode:
                task.assistant = assistant.name if assistant else "None"
            if not assistant:
                if not test_mode:
                    print(f"No suitable assistant found for the task: {task.description}")
                return None

            # Run the request with the determined or specified assistant
            self.reset_thread()
            return self.run_request(task.description, assistant,test_mode)

    def deploy(self, client,test_mode=False,test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        #Initialize swarm first
        self.client = client
        if test_mode and test_file_path:
            print("\nTesting the swarm\n\n")
            self.load_test_tasks(test_file_path)
        else:
            print("\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n")

        self.initialize_and_display_assistants()
        total_tests = 0
        groundtruth_tests = 0
        assistant_tests = 0
        for task in self.tasks:
            output = self.run_task(task,test_mode)

            if test_mode and hasattr(task, 'groundtruth'):
                total_tests += 1

                response = get_completion(self.client,[{"role":"user","content":EVALUATE_TASK_PROMPT.format(output,task.groundtruth)}])

                if response.content=='True':
                    groundtruth_tests += 1
                    print(f"{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}")

                if task.assistant==task.expected_assistant:
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                    assistant_tests += 1
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

        if test_mode:
            print(f"\n{Colors.OKGREEN}Passed {groundtruth_tests} groundtruth tests out of {total_tests} tests. Success rate: {groundtruth_tests/total_tests*100}%{Colors.ENDC}\n")
            print(f"{Colors.OKGREEN}Passed {assistant_tests} assistant tests out of {total_tests} tests. Success rate: {groundtruth_tests/total_tests*100}%{Colors.ENDC}\n")
            print("Completed testing the swarm\n\n")
        else:
            print("🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n")



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
