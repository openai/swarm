def get_completion(client,
                   messages: list[dict[str, str]],
                   model: str = "gpt-4-0125-preview",
                   max_tokens=2000,
                   temperature=0.7,
                   tools=None) :
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


def is_dict_empty(d) -> bool:
    return all(not v for v in d.values())
