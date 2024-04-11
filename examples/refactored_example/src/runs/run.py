from configs.prompts import LOCAL_PLANNER_PROMPT
from src.utils import get_completion
import json

class Run:
    def __init__(self,assistant,request,client):
        self.assistant = assistant
        self.request = request
        self.client = client
        self.status = None
        self.response = None


    def initiate(self, prompts, planner):
        self.status = 'in_progress'
        if planner=='sequential':
            plan = self.generate_plan(prompts)
            return plan
        else:
            return None

    def generate_plan(self, prompts, task=None):
        if not task:
            task = self.request

        completion = get_completion(self.client,[
            {'role': 'system', 'content': prompts['planner']},
            {'role':'user','content':f"[AVAILABLE TOOL]\n{self.assistant.tools}\n\n[TASK]\n{task}"}]
            )
        response_string = completion.content
        print(response_string)
        #Parse out just list in case
        try: # see if plan
            start_pos = response_string.find('[')
            end_pos = response_string.rfind(']')

            if start_pos != -1 and end_pos != -1 and start_pos < end_pos:
                response_truncated = response_string[start_pos:end_pos+1]
                response_formatted = json.loads(response_truncated)
                return response_formatted
            else:
                try:
                    response_formatted = json.loads(response_string)
                    return response_formatted
                except:
                    return "Response not in correct format"
        except:
            return response_string
