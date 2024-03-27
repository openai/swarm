from src.utils import get_completion
from configs.prompts import EVAL_GROUNDTRUTH_PROMPT
import json
import re
import ast
from openai import OpenAI

class EvalFunction:

  def __init__(self, client, plan, task):
        self.client = client
        self.eval_function =  getattr(self, task.eval_function, None)
        self.task = task
        self.groundtruth = task.groundtruth
        self.plan = plan

  def default(self):
    response = get_completion(self.client, [{"role": "user", "content": EVAL_GROUNDTRUTH_PROMPT.format(self.plan, self.groundtruth)}])
    if response.content.lower() == 'true':
        return True
    return False
    
  def numeric(self):
    number_pattern = r'\d+'
    response = self.plan['step'][-1]
    # Find all occurrences of numbers in the sentence
    numbers = re.findall(number_pattern, response)
    print(f"Number(s) to compare: {numbers}")
    try:
        ground_truth = ast.literal_eval(self.groundtruth)
    except:
       print(f"Ground truth is not numeric: {self.groundtruth}")
       return False
    try:
        for n in numbers:
            if int(ground_truth) == int(n) or float(ground_truth) == float(n):
                return True
    except:
        print(f"Error in comparing numbers: {numbers}")
    return False

  def name(self):
    extract_name_prompt = "You will be provided with a sentence. Your goal is to extract the full names you see in the sentence. Return the names as an array of strings."
    response = self.plan['step'][-1]
    completion_result = self.client.chat.completions.create(
       model="gpt-4-turbo-preview",
       max_tokens=100,
       temperature=0,
       messages=[
        {"role": "system",
         "content": extract_name_prompt
         },
         {"role": "user", "content": f"SENTENCE:\n{response}"}]
    )
    name_extract = completion_result.choices[0].message.content
    print(f"Name extracted: {name_extract}")
    try:
       names = ast.literal_eval(name_extract)
       ground_truth = self.groundtruth
       for n in names:
          if n.lower == ground_truth.lower():
              return True
    except:
       print(f"Issue with extracted names: {name_extract}")
    return False
  
  def evaluate(self):
    return self.eval_function()