from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

import json
from pprint import pprint
from swarm import Swarm
import re

import sys

# translator_deep.py から翻訳関数をインポート
from .translator_deep import translate_text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# ===== グローバル変数 =====
messages = []
client = None
agent = None
context_variables=None
debug=False
user_simulation = False
user_agent = None
flg_user_simulation_start = False

# 翻訳有無を制御するグローバル変数（default: False）
translation_enabled = False

@app.route('/')
def index():
    # 初回アクセス時に現在のメッセージを渡す
    global messages
    return render_template('index.html', messages=messages)

@socketio.on('send_message')
def handle_send_message(data):
    """
    クライアントからユーザー入力メッセージを受信。
    data は { 'message': '入力テキスト' } の形を想定。
    """
    global messages, client, agent, context_variables, debug, flg_user_simulation_start, user_agent
    user_message = data.get('message', '').strip()
    
    if user_message:
        llm_response(user_message, False)
        if user_simulation:
            flg_user_simulation_start = True
        
        while flg_user_simulation_start:
            user_simulation_response = query_llm_with_retry(
                client=client,
                agent=user_agent,
                messages=swap_user_and_assistant_roles(messages),
                context_variables=context_variables,
                stream=False,
                debug=debug,
            )
            user_input = get_latest_content_from_response(user_simulation_response)
            #pprint(user_input)
            llm_response(user_input, True, user_agent.name)

        

@socketio.on('stop_user_simulation')
def handle_stop_user_simulation(data):
    """
    AI対話を中断するためのユーザーリクエスト
    """
    global flg_user_simulation_start
    flg_user_simulation_start = False
    print_log("AI対話を中断しました", end="\n", str_sender="system", flg_emit=True)
#if __name__ == '__main__':
def runSocketIO():
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

def llm_response(user_message, user_simulation=False, sender=""):
    """
    ユーザーの入力を受け取り、以下の処理を行う。
      1. クライアントには元のユーザー入力（日本語）をブロードキャスト
      2. 翻訳が有効な場合、ユーザー入力を日本語→英語に翻訳してLLMに渡す
         （無効の場合はそのまま使用）
      3. LLMからの応答（英語）を取得し、翻訳が有効なら英語→日本語に翻訳後にブロードキャスト
    """
    global messages, client, agent, context_variables, debug, flg_user_simulation_start, user_agent, translation_enabled

    # ユーザーメッセージを履歴に追加＆クライアントへブロードキャスト（日本語そのまま）
    # クライアント全体へブロードキャスト
    if user_simulation:
        print_log(user_message, end="\n", str_sender='User Simulation:'+sender, flg_emit=True)
    else:
        print_log(user_message, end="\n", str_sender='User', flg_emit=True)
    if user_message.lower() == "exit":
        print_log("Exiting the loop. Goodbye!", end="\n", str_sender='system', flg_emit=True)
        sys.exit(0)

    # 翻訳が有効なら日本語→英語に変換、それ以外はそのまま使用
    if translation_enabled:
        eng_user_message = translate_text(user_message, src='ja', dest='en')
    else:
        eng_user_message = user_message

    #print(f"LLMへ送信するメッセージ: {eng_user_message}")
    messages.append({"role": "user", "content": re.sub(r'<think>.*?</think>', '', eng_user_message, flags=re.DOTALL)})
    #pprint(messages)

    # ===== LLM連携部分 =====
    response = query_llm_with_retry(
        client=client,
        agent=agent,
        messages=messages,
        context_variables=context_variables,
        stream=False,
        debug=debug,
    )

    # 翻訳が有効なら、最新のassistant応答のみを英語→日本語に翻訳したコピーを生成
    if translation_enabled:
        latest_msg = response.messages[-1]
        translated_content = None
        if latest_msg.get("role") == "assistant" and latest_msg.get("content"):
            content = latest_msg["content"]
            if len(content) > 5000:
                # 5000文字を超える場合は最初の5000文字だけ翻訳し、注意文を追加
                to_translate = content[:5000]
                try:
                    translated_content = translate_text(to_translate, src='en', dest='ja')
                except Exception as e:
                    translated_content = f"[翻訳エラー: {e}]"
                translated_content += "\n[注意: 元のテキストは5000文字を超えているため、全文の翻訳は完了していません]"
            else:
                try:
                    translated_content = translate_text(content, src='en', dest='ja')
                except Exception as e:
                    translated_content = f"[翻訳エラー: {e}]"
        # response.messagesはそのまま保持し、pretty_print用のコピーのみ作成
        translated_messages = response.messages.copy()
        if translated_content is not None:
            latest_msg_copy = translated_messages[-1].copy()
            latest_msg_copy["content"] = translated_content
            translated_messages[-1] = latest_msg_copy
    else:
        translated_messages = response.messages

    # 翻訳済み（またはそのまま）のメッセージ群を表示
    pretty_print_messages(translated_messages)

    # 内部データは常に英語で保持
    print("ReasoningタイプのLLMのthinkを消しているんだが本当にそれでいいか再考が必要")
    response.messages[-1]["content"] = re.sub(r'<think>.*?</think>', '', response.messages[-1]["content"], flags=re.DOTALL)

    messages.extend(response.messages)
    #pprint(messages)
    agent = response.agent
    # ===== LLM連携部分 =====

def swap_user_and_assistant_roles(messages):
    """
    messages（リスト）の各要素が辞書として
    {
       'role': 'system' or 'user' or 'assistant',
       'content': ...,
       ...
    }
    のような構造を想定。

    - role='user' は 'assistant' に変換
    - role='assistant' は 'user' に変換
    - role='system' はそのまま

    また、各メッセージから 'content' と 'role' 以外の情報を削除する。

    変換した新しいリストを返す。
    """
    swapped_messages = []
    for msg in messages:
        role = msg.get("role")
        if role == "user":
            role = "assistant"
        elif role == "assistant":
            role = "user"
        new_msg = {
            "role": role,
            "content": msg.get("content", "")
        }
        swapped_messages.append(new_msg)
    return swapped_messages


def print_log(message="", end="\n", str_sender="User", flg_emit=True):
    """
    CUIにprintした内容をログファイルに追記保存する関数。
    end, flush などのオプション引数もサポート。
    """
    # emit処理用にANSIエスケープコードを＜と＞に置換
    if flg_emit:
        message_emit = message.replace("\033[95m", "【").replace("\033[0m", "】")
        msg_data = { 'sender': str_sender, 'message': message_emit }
        emit('new_message', msg_data, broadcast=True)

    # ログファイルにはオリジナルのmessageをそのまま追記
    with open("output.log", "a", encoding="utf-8") as f:
        f.write(message)
        if end == "\n":
            f.write("\n")


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print_log(f"\033[94m{message['sender']}\033[0m:", end=" ", str_sender=message['sender'], flg_emit=False)

        # print response, if any
        if message["content"]:
            print_log(message["content"], str_sender=message['sender'])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print_log()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print_log(f"\033[95m{name}\033[0m({arg_str[1:-1]})", str_sender=message['sender'])

def get_latest_content_from_response(response):
    """
    responseオブジェクトから最新メッセージのcontentを文字列で返す。
    該当メッセージが無い場合やcontentが無い場合は空文字を返す。
    """
    if not response.messages:
        return "error! LLMのレスポンスにmessagesがありません"

    # 最新のメッセージ(リスト末尾)
    latest_message = response.messages[-1]
    # latest_message.get("content") が None のときは空文字""を返す
    return latest_message.get("content", "") or "error! LLMのレスポンスが空文字列です"

def query_llm_with_retry(client, agent, messages, context_variables=None, stream=False, debug=False):
    """
    LLMに問い合わせを行い、エラーが発生した場合に再試行する関数。
    
    Args:
        client: Swarm クライアントオブジェクト。
        agent: 使用するエージェント。
        messages: 現在の会話履歴。
        context_variables: コンテキスト変数（デフォルトは None）。
        stream: ストリームモードの有無（デフォルトは False）。
        debug: デバッグモードの有無（デフォルトは False）。

    Returns:
        response: LLMからの応答。
    """
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
        # エラーが発生した場合
        error_msg = f"An error occurred: {e}"
        print(error_msg)
        # エラー内容を会話履歴に追加
        print_log(message=error_msg, end="\n", str_sender="system", flg_emit=True)
        # 再試行
        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )
    return response

def run_demo_loop(starting_agent, ctxariables=None, booldebug=False, booluser_simulation=False, useragent=None, use_translation: bool = False) -> None:
    """
    LLMデモのメインループを起動する関数。
    
    Args:
      starting_agent: 使用するエージェント
      ctxariables: コンテキスト変数（任意）
      booldebug: デバッグモードの有無（任意）
      booluser_simulation: ユーザーシミュレーションの有無（任意）
      useragent: ユーザーエージェント（任意）
      use_translation: 翻訳を有効にするかどうか（True: 英訳/和訳を実施、False: 生テキストのまま） ※デフォルトはFalse
    """
    global client, agent, context_variables, debug, user_simulation, user_agent, translation_enabled
    client = Swarm()
    agent = starting_agent
    context_variables = ctxariables
    debug = booldebug
    user_simulation = booluser_simulation
    user_agent = useragent
    translation_enabled = use_translation  # 翻訳機能のON/OFFを設定

    runSocketIO()
