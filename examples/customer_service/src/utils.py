import json

CONFIGS_PATH = 'configs'

def get_completion(client,
    messages: list[dict[str, str]],
    model: str = "gpt-4-0125-preview",
    max_tokens=2000,
    temperature=0.7,
    tools=None):

    # Prepare the request parameters
    request_params = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if tools and isinstance(tools, list):
        request_params["tools"] = tools  # Tools are already in dictionary format

    # Make the  PI call
    completion = client.chat.completions.create(**request_params)

    return completion.choices[0].message

def is_dict_empty(d):
    return all(not v for v in d.values())

def parse_text(text, mode='txt'):
    if text[:4] == 'file':
        file_path = text.replace('file:', '')
        #print(f"Loading text from file: {file_path}")
        with open(f"{CONFIGS_PATH}/{file_path}", 'r') as f:
            if mode == 'json':
                return json.load(f)
            else:
                return f.read()
    return text
        