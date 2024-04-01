import os
import importlib
import json
from src.swarm.tool import Tool
from src.swarm.assistants import Assistant

def validate_tool(tool_definition):
    # Validate the tool using its schema
    Tool(**tool_definition)  # Uncomment if you have a schema to validate tools
    print(f"Validating tool: {tool_definition['function']['name']}")

def validate_all_tools(engine):
    tools_path = os.path.join(os.getcwd(), 'configs/tools')
    for tool_dir in os.listdir(tools_path):
        if '__pycache__' in tool_dir:
            continue
        tool_dir_path = os.path.join(tools_path, tool_dir)
        if os.path.isdir(tool_dir_path):
            # Validate tool.json
            tool_json_path = os.path.join(tool_dir_path, 'tool.json')
            handler_path = os.path.join(tool_dir_path, 'handler.py')
            if os.path.isfile(tool_json_path) and os.path.isfile(handler_path):
                with open(tool_json_path, 'r') as file:
                    tool_def = json.load(file)
                    tool_name_from_json = tool_def['function']['name']

                    # Check if the folder name matches the tool name in tool.json
                    if tool_name_from_json != tool_dir:
                        print(f"Mismatch in tool folder name and tool name in JSON for {tool_dir}")
                    else:
                        print(f"{tool_dir}/tool.json tool name matches folder name.")

                    # Check if the function name in handler.py matches the tool name
                    spec = importlib.util.spec_from_file_location(f"{tool_dir}_handler", handler_path)
                    tool_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(tool_module)

                    # Verify if the function exists in handler.py and matches the name
                    if hasattr(tool_module, tool_dir):
                        print(f"{tool_dir}/handler.py contains a matching function name.")
                    else:
                        print(f"{tool_dir}/handler.py does not contain a function '{tool_dir}'.")

            else:
                if not os.path.isfile(tool_json_path):
                    print(f"Missing tool.json in {tool_dir} tool folder.")
                if not os.path.isfile(handler_path):
                    print(f"Missing handler.py in {tool_dir} tool folder.")
    print('\n')

    # Function to validate all assistants
def validate_all_assistants():
    assistants_path = os.path.join(os.getcwd(), 'configs/assistants')
    for root, dirs, files in os.walk(assistants_path):
        for file in files:
            if file.endswith('assistant.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as file:
                        assistant_data = json.load(file)[0]  # Access the first dictionary in the list
                        try:
                            Assistant(**assistant_data)
                            print(f"{os.path.basename(root)} assistant validated!")
                        except:
                            Assistant(**assistant_data)
                            print(f"Assistant validation failed!")
    print('\n')
