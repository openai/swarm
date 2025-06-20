import re
from typing import Optional

# 以下は types.py に定義されているものと同様のインポート例です
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

def extract_substring_regex(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    """
    text から start_marker と end_marker に挟まれた部分を非貪欲で抽出する。
    見つからなければ None を返す。
    """
    pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return None

def conversion_codestral(content: str) -> Optional[ChatCompletionMessageToolCall]:
    """
    content が以下の形式の場合：
        [TOOL_REQUEST]{"name": "transfer_to_triage_agent", "arguments":{}}[END_TOOL_REQUEST]
    ツールリクエストとみなし、内容をパースして以下のオブジェクトを生成して返す：
        ChatCompletionMessageToolCall(
            id='',
            function=Function(arguments='{}', name='transfer_to_triage_agent'),
            type='function'
        )
    前後の空白・改行を除去し、正しい形式でなければ None を返す。
    """
    content = content.strip()
    if not (content.startswith("[TOOL_REQUEST]") and content.endswith("[END_TOOL_REQUEST]")):
        return None

    prefix_len = len("[TOOL_REQUEST]")
    suffix_len = len("[END_TOOL_REQUEST]")
    middle = content[prefix_len:-suffix_len].strip()

    # "name" と "arguments" の値を抽出する（非貪欲マッチ）
    name_pattern = r'"name"\s*:\s*"([^"]+)"'
    args_pattern = r'"arguments"\s*:\s*(\{.*?\})'
    name_match = re.search(name_pattern, middle)
    args_match = re.search(args_pattern, middle)

    if not name_match or not args_match:
        return None

    function_name = name_match.group(1)
    arguments_str = args_match.group(1)

    tool_call_obj = ChatCompletionMessageToolCall(
        id='',
        function=Function(arguments=arguments_str, name=function_name),
        type='function'
    )
    return tool_call_obj

def conversion_for_tool_use(chat_response, model_name):
    """
    chat_response: ChatCompletionオブジェクト
    model_name: モデル名（string）

    以下を行う：
      1) "before:" と chat_response を表示
      2) model_name が "codestral-22b-v0.1" なら:
         - chat_response.choices[0].message.content を文字列として取得する
         - その中に [TOOL_REQUEST] と [END_TOOL_REQUEST] が存在していれば、その部分を抜き出す
         - 抜き出した部分（複数存在する場合も対応）を含む完全な文字列を conversion_codestral に渡し、ツールリクエストをオブジェクト化する
         - 変換に成功したら、message.content はそのまま残し、tool_calls リストに変換結果オブジェクトを追加する
      3) "after:" と chat_response を表示
      4) 加工後のオブジェクトを return
    """
    #print("before:")
    #print(chat_response)

    if model_name == "codestral-22b-v0.1":
        if not chat_response.choices:
            return chat_response

        # message.content の取得（メッセージ本文はそのまま保持する）
        content_str = chat_response.choices[0].message.content
        if content_str:
            # [TOOL_REQUEST] と [END_TOOL_REQUEST] が本文内に存在する場合、その部分を抽出する
            # 複数存在する場合にも対応するため、findall を使用
            tool_requests = re.findall(r'\[TOOL_REQUEST\](.*?)\[END_TOOL_REQUEST\]', content_str, re.DOTALL)
            for extracted in tool_requests:
                full_tool_request = f"[TOOL_REQUEST]{extracted}[END_TOOL_REQUEST]"
                converted_obj = conversion_codestral(full_tool_request)
                if converted_obj:
                    # tool_calls リストにオブジェクトを追加する
                    if not hasattr(chat_response.choices[0].message, "tool_calls") or chat_response.choices[0].message.tool_calls is None:
                        chat_response.choices[0].message.tool_calls = []
                    chat_response.choices[0].message.tool_calls.append(converted_obj)

    #print("after:")
    #print(chat_response)
    return chat_response