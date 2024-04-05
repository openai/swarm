import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
if os.getenv("OPENAI_ORG_ID") is None:
    client = OpenAI()
else:
    client = OpenAI(organization=os.getenv("OPENAI_ORG_ID"))

def get_chat_completions(messages, temperature=0, model="gpt-4-turbo-preview", max_tokens=300):
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Failed to get chat completions: {e}")
        return ""

def get_embeddings(text, model="text-embedding-3-small"):
    embeddings = client.embeddings.create(
      model=model,
      input=text,
      encoding_format="float"
    )
    return embeddings.data[0].embedding

def create_thread():
    thread = client.beta.threads.create()
    return thread

def submit_message(thread_id, message, role='user'):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=message
    )

def run_thread(assistant_id, thread_id):
    run = client.beta.threads.runs.create(
        assistant_id=assistant_id,
        thread_id=thread_id
    )
    return run

def get_run(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )
    return run

def submit_tool_output(thread_id, run_id, tool_call_id, output):
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=[{
            "tool_call_id": tool_call_id,
            "output": output}]
    )
    return run

def get_messages(thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order='asc'
    )
    return messages