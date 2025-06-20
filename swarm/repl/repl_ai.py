import json
from pprint import pprint
from swarm import Swarm

def print_log(message="", end="\n", flush=False):
    """
    CUIにprintした内容をログファイルに追記保存する関数。
    end, flush などのオプション引数もサポート。
    """
    # 標準出力へ出す
    print(message, end=end, flush=flush)
    
    # ログファイルに追記
    with open("output.log", "a", encoding="utf-8") as f:
        f.write(message)
        # end="\n" であればファイルにも改行を入れる
        if end == "\n":
            f.write("\n")

def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print_log(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print_log(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print_log(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print_log()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print_log(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print_log(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print_log()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print_log(f"\033[95m{name}\033[0m({arg_str[1:-1]})")

def get_latest_content_from_response(response):
    """
    responseオブジェクトから最新メッセージのcontentを文字列で返す。
    該当メッセージが無い場合やcontentが無い場合は空文字を返す。
    """
    if not response.messages:
        return "ない"

    # 最新のメッセージ(リスト末尾)
    latest_message = response.messages[-1]
    # latest_message.get("content") が None のときは空文字""を返す
    return latest_message.get("content", "") or "ない２？"


def run_demo_loop(
    starting_agent, user, context_variables=None, stream=False, debug=False
) -> None:
    client = Swarm()
    print_log("Starting Swarm CLI 🐝")

    messages = []
    agent = starting_agent
    user_agent = user
    while True:
        user_input = None

        try:
            # LLMへ問い合わせ
            user_input = client.run(
                agent=user_agent,
                messages=messages,
                context_variables=context_variables or {},
                stream=stream,
                debug=debug,
            )
        except Exception as e:
            # エラーが起きた場合、その内容を会話履歴に挿入して再実行
            error_msg = f"An error occurred: {e}"
            print_log(error_msg)
            # LLMにエラーが起きたことを伝える(例: systemロールなど)
            messages.append({"role": "system", "content": error_msg})
            # エラー情報を踏まえて再度推論させる
            user_input = client.run(
                agent=user_agent,
                messages=messages,
                context_variables=context_variables or {},
                stream=stream,
                debug=debug,
            )

        str_user_input = get_latest_content_from_response(user_input)
        print(str_user_input)

        if str_user_input.lower() == "exit":
            print_log("Exiting the loop. Goodbye!")
            break

        messages.append({"role": "user", "content": str_user_input})
        print_log("user:" +  str_user_input)

        #ここから下tryブロックの中は編集したよ。関数のコールのときに引数のアンマッチによるエラーがおきる。LLMの挙動は不安定だからエラーが起きても止まらないようにtryに入れた。エラー時にそのメッセージを追加してもう一度トライさせてる。それでももう一回同じエラーが起きる可能性はある。
        try:
            # LLMへ問い合わせ
            response = client.run(
                agent=agent,
                messages=messages,
                context_variables=context_variables or {},
                stream=stream,
                debug=debug,
            )
        except Exception as e:
            # エラーが起きた場合、その内容を会話履歴に挿入して再実行
            error_msg = f"An error occurred: {e}"
            print_log(error_msg)
            # LLMにエラーが起きたことを伝える(例: systemロールなど)
            messages.append({"role": "system", "content": error_msg})
            # エラー情報を踏まえて再度推論させる
            response = client.run(
                agent=agent,
                messages=messages,
                context_variables=context_variables or {},
                stream=stream,
                debug=debug,
            )

        if stream:
            response = process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        messages.extend(response.messages)
        agent = response.agent
