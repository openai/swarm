TRIAGE_MESSAGE_PROMPT = "Given the following message: {}, select which assistant of the following is best suited to handle it: {}. Respond with JUST the name of the assistant, nothing else"
TRIAGE_SYSTEM_PROMPT = "You are an assistant who triages requests and selects the best assistant to handle that request."
EVAL_GROUNDTRUTH_PROMPT = "Given the following completion: {}, and the expected completion: {}, select whether the completion and expected completion are the same in essence. Correctness does not mean they are the same verbatim, but that the ANSWER is the same. For example: 'The answer, after calculating, is 4' and '4' would be the same. But 'it is 5' and 'the answer is 12' would be different. Respond with ONLY 'true' or 'false'"
EVAL_ASSISTANT_PROMPT = "Given the following assistant name: {}, and the expected assistant name: {}, select whether the assistants are the same. Minor formatting differences, or extra characters are OK, but the words should be the same. Respond with ONLY 'true' or 'false'"
EVAL_PLANNING_PROMPT = "Given the following plan: {}, and the expected plan: {}, select whether the plan and expected plan are the same in essence. Correctness does not mean they are the same verbatim, but that the content is the same with just minor formatting differences. Respond with ONLY 'true' or 'false'"
ITERATE_PROMPT = "Your task to complete is {}. You previously generated the following plan: {}. The steps completed, and the output of those steps, are here: {}. IMPORTANT: Given the outputs of the previous steps, use that to create a revised plan, using the following planning prompt."
EVALUATE_TASK_PROMPT = """Your task was {}. The steps you completed, and the output of those steps, are here: {}. IMPORTANT: Output the following, 'true' or 'false' if you successfully completed the task. Even if your plan changed from original plan, evaluate if the new plan and output
correctly satisfied the given task. Additionally, output a message for the user, explaining whya task was successfully completed, or why it failed. Example:
Task: "Tell a joke about cars. Translate it to Spanish"
Original Plan: [{{tool: "tell_joke", args: {{input: "cars"}}, {{tool: "translate", args: {{language: "Spanish"}}]
Steps Completed: [{{tool: "tell_joke", args: {{input: "cars", output: "Why did the car stop? It ran out of gas!"}}, {{tool: "translate", args: {{language: "Spanish", output: "¿Por qué se detuvo el coche? ¡Se quedó sin gas!"}}]
OUTPUT: ['true','The joke was successfully told and translated to Spanish.']
MAKE SURE THAT OUTPUT IS a list, bracketed by square brackets, with the first element being either 'true' or 'false', and the second element being a string message."""

# IMPORTANT: If you are missing
# any information, or do not have all the required arguments for the tools you are planning, just return your response in double quotes.
# to tell user what information you would need for the request.
#local_engine_vars
LOCAL_PLANNER_PROMPT = """
You are a planner for the Swarm framework.
Your job is to create a properly formatted JSON plan step by step, to satisfy the task given.
Create a list of subtasks based off the [TASK] provided. Your FIRST THOUGHT should be, do I need to call a tool here to answer
or fulfill the user's request. First, think through the steps of the plan necessary. Make sure to carefully look over the tools you are given access to to decide this.
If you are confident that you do not need a tool to respond, either just in conversation or to ask for clarification or more information, respond to the prompt in a concise, but conversational, tone in double quotes. Do not explain that you do not need a tool.
If you DO need tools, create a list of subtasks. Each subtask must be from within the [AVAILABLE TOOLS] list. DO NOT use any tools that are not in the list.
Make sure you have all information needed to call the tools you use in your plan.
Base your decisions on which tools to use from the description and the name and arguments of the tool.
Always output the arguments of the tool, even when arguments is an empty dictionary. MAKE SURE YOU USE ALL REQUIRED ARGUMENTS.
The plan should be as short as possible.

For example:

[AVAILABLE TOOLS]
{{
  "tools": [
    {{
      "type": "function",
      "function": {{
        "name": "lookup_contact_email",
        "description": "Looks up a contact and retrieves their email address",
        "parameters": {{
          "type": "object",
          "properties": {{
            "name": {{
              "type": "string",
              "description": "The name to look up"
            }}
          }},
          "required": ["name"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "email_to",
        "description": "Email the input text to a recipient",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to email"
            }},
            "recipient": {{
              "type": "string",
              "description": "The recipient's email address. Multiple addresses may be included if separated by ';'."
            }}
          }},
          "required": ["input", "recipient"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "translate",
        "description": "Translate the input to another language",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to translate"
            }},
            "language": {{
              "type": "string",
              "description": "The language to translate to"
            }}
          }},
          "required": ["input", "language"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "summarize",
        "description": "Summarize input text",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to summarize"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "joke",
        "description": "Generate a funny joke",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to generate a joke about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "brainstorm",
        "description": "Brainstorm ideas",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to brainstorm about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "poe",
        "description": "Write in the style of author Edgar Allen Poe",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to write about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }}
  ]
}}

[TASK]
"Tell a joke about cars. Translate it to Spanish"

[OUTPUT]
[
    {{"tool": "joke","args":{{"input": "cars"}}}},
    {{"tool": "translate", "args": {{"language": "Spanish"}}
  ]

[TASK]
"Tomorrow is Valentine's day. I need to come up with a few date ideas. She likes Edgar Allen Poe so write using his style. E-mail these ideas to my significant other. Translate it to French."

[OUTPUT]
[{{"tool": "brainstorm","args":{{"input": "Valentine's Day Date Ideas"}}}},
    {{"tool": "poe", "args": {{}}}},
    {{"tool": "email_to", "args": {{"recipient": "significant_other@example.com"}},
    {{"tool": "translate", "args": {{"language": "French"}}]

[AVAILABLE TOOLS]
{tools}

[TASK]
{task}

[OUTPUT]
"""
