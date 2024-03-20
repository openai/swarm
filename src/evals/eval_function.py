from src.utils import get_completion
from configs.prompts import EVALUATE_TASK_PROMPT
import json
from openai import OpenAI

class EvalFunction:

  def __init__(self, client, task, plan_log):
        self.client = client
        self.eval_function =  getattr(self, task.eval_function, None)
        self.task = task
        self.plan_log = plan_log

  def default(self):
    print(self.plan_log)
    output = get_completion(self.client, [{'role': 'user', 'content': EVALUATE_TASK_PROMPT.format(self.task.description, self.plan_log)}])
    output.content = output.content.replace("'",'"')
    try:
        return json.loads(output.content)
    except json.JSONDecodeError:
        print("An error occurred while decoding the JSON.")
        return None
    
  def numeric(self):
      output = self.default()
      return output

  def name(self):
      output = self.default()
      return output
  
  def evaluate(self):
      return self.eval_function()