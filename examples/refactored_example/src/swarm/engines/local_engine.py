import importlib
import json
import os
from src.utils import get_completion, is_dict_empty, Colors, parse_text
from src.swarm.assistants import Assistant
from src.swarm.tool import Tool
from src.tasks.task import EvaluationTask
from src.runs.run import Run

DEFAULT_SYSTEM_PROMPT = 'You are a helpful assistant.'

def filter_tools(tools, assistants):
    """
    Filter tools to keep only those used by assistants
    """
    assistant_tools = []
    for assistant in assistants:
       for t in assistant['tools']:
           tool_definition = next((tool for tool in tools if tool['name'] == t), None)
           if tool_definition:
                assistant_tools.append(tool_definition)
    return assistant_tools


class LocalEngine:
    def __init__(self, client, tasks, settings, persist=False):
        self.client = client
        self.visible_assistants = []
        self.assistants = []
        self.last_assistant = None
        self.persist = persist
        self.tasks = tasks
        self.tool_functions = []
        self.global_context = {}
        self.max_iterations = settings['max_iterations']
        self.prompts = {}
        self.root_assistant = {}
        self.model = ''

    def get_tool(self, tool_name):
        for t in self.tool_functions:
            if t.name == tool_name:
                return t
        else:
            print(f'\n{Colors.WARNING}Tool not found:{Colors.ENDC} {Colors.BOLD}{tool_name}{Colors.ENDC}')
            return None

    def parse_assistants(self, assistants, swarm):
        for assistant in assistants:
            assistant['system_prompt'] = parse_text(assistant['system_prompt'])
            assistant['tools'] = [self.get_tool(t) for t in assistant['tools']]
            if 'display_name' not in assistant:
                assistant['display_name'] = assistant['name']
            if 'model' not in assistant:
                assistant['model'] = swarm['default_model']

            assistant_obj = Assistant(**assistant)
            assistant_obj.initialize_history()
            self.assistants.append(assistant_obj)

    def parse_tools(self, tools):
        for tool in tools:
            tool_obj = Tool(**tool)
            self.tool_functions.append(tool_obj)

    def load_tools(self, swarm, assistants):
        tools = []
        try:
            tools_array = swarm['tools']
            for t in tools_array:
                if t[:4] == 'file':
                    tools.extend(parse_text(t, mode='json'))
                else:
                    tools.append(json.loads(t))            
        except Exception as e:
            print(f"Error loading tools: {e}")
        
        tools_filtered = filter_tools(tools, assistants)
        self.parse_tools(tools_filtered)

    def load_all_assistants(self, swarm):
        assistants = []
        try:
            assistants_array = swarm['assistants']
            for a in assistants_array:
                if a[:4] == 'file':
                    assistants.extend(parse_text(a, mode='json'))
                else:
                    assistants.append(json.loads(a))
        except Exception as e:
            print(f"Error loading assistants: {e}")
        
        root_assistant = {
            'name': 'root',
            'tools': [],
            'system_prompt': DEFAULT_SYSTEM_PROMPT,
            'display_name': 'User interface',
            'model': swarm['interface_model']
        }

        self.root_assistant = Assistant(**root_assistant)
        self.root_assistant.initialize_history()
        self.load_tools(swarm, assistants)
        self.parse_assistants(assistants, swarm)


    def update_visible_assistants(self, current_assistant):
        """
        Update the visible assistants based on the current assistant.
        """
        visible_assistants = [current_assistant]
        visible_assistants_names = []
        if current_assistant.name != 'root':
            parent_assistant = self.get_assistant(current_assistant)
            if 'sub_assistants' in parent_assistant:
                visible_assistants_names = parent_assistant['sub_assistants']
            
        for assistant in self.assistants:
            if current_assistant.name == 'root':
                if assistant.root_assistant:
                    visible_assistants.append(assistant)
            else:
                if assistant.name in visible_assistants_names:
                    visible_assistants.append(assistant)
        if len(visible_assistants) == 0:
            print(f"{Colors.WARNING}No visible assistants found.{Colors.ENDC}")
        self.visible_assistants = visible_assistants

    def load_prompts(self, swarm):
        prompts = {}
        try:
            for key, value in swarm['prompts'].items():
                prompts[key] = parse_text(value)
        except Exception as e:
            print(f"Error loading prompts: {e}")
        self.prompts = prompts

    def initialize_and_display_assistants(self, swarm):
            """
            Loads all assistants and displays their information.
            """
            self.model = swarm['interface_model']
            self.load_all_assistants(swarm)
            self.update_visible_assistants(self.root_assistant)
            self.initialize_global_history()

            for asst in self.assistants:
                print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
                print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
                if asst.tools:
                    print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {[tool.name if tool else 'tool not found' for tool in asst.tools]} \n')
                else:
                    print(f"{Colors.OKGREEN}Tools:{Colors.ENDC} No tools \n")


    def get_assistant(self, triage):

        for assistant in self.assistants:
            if assistant.name in triage:
                return assistant

        return self.root_assistant

    def triage_request(self, message):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
     
        triage_message = [{"role": "system", "content": self.prompts['triage']}]
        assistants = [{'name': assistant.name, 'instructions': assistant.system_prompt, 'tools': assistant.tools} for assistant in self.visible_assistants]
        triage_message.append(
            {
                "role": "user",
                "content": f"USER PROMPT: {message}\n\nAvailable assistants: {assistants}"
            }
        )
        triage_response = get_completion(self.client, triage_message, self.model).content
        print(f"Triage response: {triage_response}")
        assistant = self.get_assistant(triage_response)
        print(f"Selected assistant: {assistant.display_name}")
        return assistant

    def initiate_run(self, task, assistant,test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        run = Run(assistant, task.description, self.client)

        #Update assistant with current task and run
        assistant.current_task_id = task.id
        assistant.runs.append(run)


        #Get planner
        planner = assistant.planner
        plan = run.initiate(planner)
        plan_log = {'step': [], 'step_output': []}
        if not isinstance(plan, list):
            plan_log['step'].append('response')
            plan_log['step'].append(plan)
            assistant.add_assistant_message(f"Response to user: {plan}")
            print(f"{Colors.HEADER}Response:{Colors.ENDC} {plan}")

            #add global context
            self.store_context_globally(assistant)
            return plan_log, plan_log

        original_plan = plan.copy()
        iterations = 0

        while plan and iterations< self.max_iterations:
            if isinstance(plan,list):
              step = plan.pop(0)
            else:
                return "Error generating plan", "Error generating plan"
            assistant.add_tool_message(step)
            human_input_flag = next((tool.human_input for tool in assistant.tools if tool.function.name == step['tool']), False)
            if step['tool']:
                print(f"{Colors.HEADER}Running Tool:{Colors.ENDC} {step['tool']}")
                if human_input_flag:
                    print(f"\n{Colors.HEADER}Tool {step['tool']} requires human input:{Colors.HEADER}")
                    print(f"{Colors.GREY}Tool arguments:{Colors.ENDC} {step['args']}\n")

                    user_confirmation = input(f"Type 'yes' to execute tool, anything else to skip: ")
                    if user_confirmation.lower() != 'yes':
                        assistant.add_assistant_message(f"Tool {step['tool']} execution skipped by user.")
                        print(f"{Colors.GREY}Skipping tool execution.{Colors.ENDC}")
                        plan_log['step'].append('tool_skipped')
                        plan_log['step_output'].append(f'Tool {step["tool"]} execution skipped by user! Task not completed.')
                        continue
                    assistant.add_assistant_message(f"Tool {step['tool']} execution approved by user.")
            tool_output = self.handle_tool_call(assistant, step, test_mode)
            plan_log['step'].append(step)
            plan_log['step_output'].append(tool_output)

            if task.iterate and not is_dict_empty(plan_log) and plan:
               iterations += 1
               new_task = self.prompts['iterate'].format(task.description, original_plan, plan_log)
               plan = run.generate_plan(new_task)
            # Store the output for the next iteration

            self.store_context_globally(assistant)

        return original_plan, plan_log

    def handle_tool_call(self,assistant, tool_call, test_mode=False):
        tool_name = tool_call['tool']
        tool_dir = os.path.join(os.getcwd(), 'configs/tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')

        # Dynamically import the handler function from the handler.py file
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f"{tool_name}_handler", handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name)
            # Call the handler function with arguments
            try:
                tool_response = tool_handler(**tool_call['args'])
            except:
                return 'Failed to execute tool'

            try:
                # assistant.add_assistant_message(tool_response.content)
                return tool_response.content
            except:
                # assistant.add_assistant_message(tool_response)
                return tool_response

        print('No tool file found')
        return 'No tool file found'

    def run_task(self, task, test_mode):
            """
            Processes a given task.
            """

            if not test_mode:
                print(
            f"{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            else:
                print(
            f"{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            #Maintain assistant if persist flag is true
            if self.persist and self.last_assistant is not None:
                assistant = self.last_assistant
            else:
                assistant = self.get_assistant(task.assistant)
                assistant.current_task_id = task.id
                assistant.add_user_message(task.description)

            #triage based on current assistant
            selected_assistant = self.triage_request(task.description)
            self.update_visible_assistants(selected_assistant)
            if test_mode:
                task.assistant = selected_assistant.name if selected_assistant else "None"
            if not selected_assistant:
                if not test_mode:
                    print(f"No suitable assistant found for the task: {task.description}")
                return None

            # Run the request with the determined or specified assistant
            original_plan, plan_log = self.initiate_run(task, selected_assistant,test_mode)

            #set last assistant
            self.last_assistant = selected_assistant

            #if evaluating the task
            if task.evaluate:
                output = assistant.evaluate(self.client,task, plan_log)
                if output is not None:
                    success_flag = False
                    if not isinstance(output[0],bool):
                     success_flag = False if output[0].lower() == 'false' else bool(output[0])
                    message = output[1]
                    if success_flag:
                        print(f'\n\033[93m{message}\033[0m')
                    else:
                        print(f"{Colors.RED}{message}{Colors.ENDC}")
                    #log
                    assistant.add_assistant_message(message)
                else:
                    message = "Error evaluating output"
                    print(f"{Colors.RED}{message}{Colors.ENDC}")
                    assistant.add_assistant_message(message)

            return original_plan, plan_log


    def run_tests(self):
        total_groundtruth = 0
        total_planning = 0
        total_assistant = 0
        groundtruth_pass = 0
        planning_pass = 0
        assistant_pass = 0
        for task in self.tasks:
            original_plan, plan_log = self.run_task(task, test_mode=True)

            if task.groundtruth:
                total_groundtruth += 1
                # Assuming get_completion returns a response object with a content attribute
                response = get_completion(self.client, [{"role": "user", "content": EVAL_GROUNDTRUTH_PROMPT.format(original_plan, task.groundtruth)}])
                if response.content.lower() == 'true':
                    groundtruth_pass += 1
                    print(f"{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")

                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")


            elif task.expected_plan:
                total_planning += 1
                # Assuming get_completion returns a response object with a content attribute
                response = get_completion(self.client, [{"role": "user", "content": EVAL_PLANNING_PROMPT.format(original_plan, task.expected_plan)}])

                if response.content.lower() == 'true':
                    planning_pass += 1
                    print(f"{Colors.OKGREEN}✔ Planning test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")

                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned.  {Colors.ENDC}{Colors.OKBLUE}Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

            else:
                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

        if total_groundtruth > 0:
            print(f"\n{Colors.OKGREEN}Passed {groundtruth_pass} groundtruth tests out of {total_groundtruth} tests. Success rate: {groundtruth_pass / total_groundtruth * 100}%{Colors.ENDC}\n")
        if total_planning > 0:
            print(f"{Colors.OKGREEN}Passed {planning_pass} planning tests out of {total_planning} tests. Success rate: {planning_pass / total_planning * 100}%{Colors.ENDC}\n")
        if total_assistant > 0:
            print(f"{Colors.OKGREEN}Passed {assistant_pass} assistant tests out of {total_assistant} tests. Success rate: {assistant_pass / total_assistant * 100}%{Colors.ENDC}\n")
        print("Completed testing the swarm\n\n")

    def deploy(self, client, swarm, test_mode=False, test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        self.client = client
        self.load_prompts(swarm)
        if test_mode and test_file_path:
            print("\nTesting the swarm\n\n")
            self.load_test_tasks(test_file_path)
            self.initialize_and_display_assistants(swarm)
            self.run_tests()
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation(test=True)
        else:
            print("\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n")
            self.initialize_and_display_assistants(swarm)
            print("\n" + "-" * 100 + "\n")
            for task in self.tasks:
                print('Task',task.id)
                print(f"{Colors.BOLD}Running task{Colors.ENDC}")
                self.run_task(task, test_mode)
                print("\n" + "-" * 100 + "\n")
            #save the session
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation()
             #assistant.print_conversation()

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

    def store_context_globally(self, assistant):
        self.global_context['history'].append({assistant.name:assistant.context['history']})

    def initialize_global_history(self):
        self.global_context['history'] = []
