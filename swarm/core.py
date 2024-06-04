# Standard library imports
import copy
import json
from collections import defaultdict
from typing import List

# Package/library imports
from openai import OpenAI

# Local imports
from .util import function_to_json, debug_print, merge_chunk
from .types import (
    Assistant,
    AssistantFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
)

__CTX_VARS_NAME__ = "context_variables"


class Swarm:

    def __init__(self):
        self.client = OpenAI()

    def get_chat_completion(
        self,
        assistant: Assistant,
        history: List,
        context_variables: dict,
        model_override: str,
        stream: bool,
        debug: bool,
    ) -> ChatCompletionMessage:
        context_variables = defaultdict(str, context_variables)
        instructions = (
            assistant.instructions(context_variables)
            if callable(assistant.instructions)
            else assistant.instructions
        )
        messages = [{"role": "system", "content": instructions}] + history
        debug_print(debug, "Getting chat completion for...:", messages)

        tools = [function_to_json(f) for f in assistant.functions]
        # hide context_variables from model
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)

        return self.client.chat.completions.create(
            model=model_override or assistant.model,
            messages=messages,
            tools=[function_to_json(f) for f in assistant.functions] or None,
            tool_choice=assistant.tool_choice,
            stream=stream,
        )

    def handle_function_result(self, result, debug) -> Result:
        match result:
            case Result() as result:
                return result

            case Assistant() as assistant:
                return Result(
                    value=json.dumps({"assistant": assistant.name}),
                    assistant=assistant,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. Make sure assistant functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AssistantFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], assistant=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call.function.name
            # handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(debug, f"Tool {name} not found in function map.")
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue
            args = json.loads(tool_call.function.arguments)
            debug_print(debug, f"Processing tool call: {name} with arguments {args}")

            func = function_map[name]
            # pass context_variables to assistant functions
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables
            raw_result = function_map[name](**args)
            result: Result = self.handle_function_result(raw_result, debug)

            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "tool_name": name,
                    "content": result.value,
                }
            )
            partial_response.context_variables.update(result.context_variables)
            partial_response.assistant = result.assistant

        return partial_response

    def runAndStream(
        self,
        assistant: Assistant,
        messages: List,
        context_variables: dict = None,
        model_override: str = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        ######################################
        #
        # START BLOCK 1: this block is identical to a block in run(), possibly can be refactored
        #
        active_assistant = assistant
        context_variables = copy.deepcopy(context_variables) if context_variables else {}
        history = copy.deepcopy(messages)
        init_len = len(messages)
        #
        # END BLOCK 1
        #
        ######################################

        # this loop is identical to the one in run(), possibly can be refactored
        while len(history) - init_len < max_turns and active_assistant:

            message = {
                "content": "",
                "sender": assistant.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            # this call is identical to the one in run() other than the stream flag, possibly can be refactored
            # get completion with current history, assistant
            completion = self.get_chat_completion(
                assistant=active_assistant,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=True,
                debug=debug,
            )

            yield {"delim": "start"}
            for chunk in completion:
                delta = json.loads(chunk.choices[0].delta.json())
                if delta["role"] == "assistant":
                    delta["sender"] = active_assistant.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            # I refactored this a bit to make it more readable
            raw_tool_calls = list(message.get("tool_calls", {}).values())
            message["tool_calls"] = raw_tool_calls if raw_tool_calls else None
            tool_calls = [
                    ChatCompletionMessageToolCall(
                    id=tool_call["id"],
                    function=Function(
                        arguments=tool_call["function"]["arguments"],
                        name=tool_call["function"]["name"],
                    ),
                    type=tool_call["type"],
                )
                for tool_call in raw_tool_calls
            ]

            debug_print(debug, "Received completion:", message)
            history.append(message)

            ######################################
            #
            # START BLOCK 2: this block is identical to a block in run(), possibly can be refactored
            #
            if tool_calls and execute_tools:
                # handle function calls, updating context_variables, and switching assistants
                partial_response = self.handle_tool_calls(
                    tool_calls, active_assistant.functions, context_variables, debug
                )
                history.extend(partial_response.messages)
                context_variables.update(partial_response.context_variables)
                next_assistant = partial_response.assistant
            else:
                next_assistant = None

            # It's possible that the assistant has changed after handling tools, but
            # we want to run the post_execute function on the assistant that was active.
            # This allows any Assistant to run a post_execute, regardless of whether or not
            # the last step was a tool.
            if active_assistant.post_execute:
                response = Response(
                    messages=history[init_len:], assistant=next_assistant, context_variables=context_variables
                )
                result = active_assistant.post_execute(response)
                context_variables.update(result.context_variables)
                next_assistant = result.assistant

            active_assistant = next_assistant
            if not active_assistant:
                debug_print(debug, "Ending turn.")
                break
            #
            # END BLOCK 2
            #
            ######################################

        # this yields a Response which is identical to the one returned by run(), possibly can be refactored
        yield {
            "response": Response(
                messages=history[init_len:],
                assistant=active_assistant,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        assistant: Assistant,
        messages: List,
        context_variables: dict = None,
        model_override: str = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:
        if stream:
            return self.runAndStream(
                assistant=assistant,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        ######################################
        #
        # START BLOCK 1: this block is identical to a block in runAndStream(), possibly can be refactored
        #
        active_assistant = assistant
        context_variables = copy.deepcopy(context_variables) if context_variables else {}
        history = copy.deepcopy(messages)
        init_len = len(messages)
        #
        # END BLOCK 1
        #
        ######################################

        # this loop is identical to the one in runAndStream(), possibly can be refactored
        while len(history) - init_len < max_turns and active_assistant:

            # this call is identical to the one in runAndStream() other than the stream flag, possibly can be refactored
            # get completion with current history, assistant
            completion = self.get_chat_completion(
                assistant=active_assistant,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            message = completion.choices[0].message
            debug_print(debug, "Received completion:", message)
            message.sender = active_assistant.name
            history.append(json.loads(message.model_dump_json()))  # to avoid OpenAI types (?)
            tool_calls = message.tool_calls

            ######################################
            #
            # START BLOCK 2: this block is identical to a block in runAndStream(), possibly can be refactored
            #
            if tool_calls and execute_tools:
                # handle function calls, updating context_variables, and switching assistants
                partial_response = self.handle_tool_calls(
                    message.tool_calls, active_assistant.functions, context_variables, debug
                )
                history.extend(partial_response.messages)
                context_variables.update(partial_response.context_variables)
                next_assistant = partial_response.assistant
            else:
                next_assistant = None

            # It's possible that the assistant has changed after handling tools, but
            # we want to run the post_execute function on the assistant that was active.
            # This allows any Assistant to run a post_execute, regardless of whether or not
            # the last step was a tool.
            if active_assistant.post_execute:
                response = Response(
                    messages=history[init_len:], assistant=next_assistant, context_variables=context_variables
                )
                result = active_assistant.post_execute(response)
                context_variables.update(result.context_variables)
                next_assistant = result.assistant

            active_assistant = next_assistant
            if not active_assistant:
                debug_print(debug, "Ending turn.")
                break
            #
            # END BLOCK 2
            #
            ######################################

        # this returns a Response which is identical to the one yielded by runAndStream(), possibly can be refactored
        return Response(
            messages=history[init_len:],
            assistant=active_assistant,
            context_variables=context_variables,
        )
