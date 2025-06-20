from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# ===== 外部LLMハンドラー登録用グローバル変数 =====
llm_handler = None

def set_llm_handler(handler):
    """
    外部LLM側の処理を行う関数を登録する。
    handler: ユーザー入力（文字列）を受け取り、LLMからの応答文字列を返す関数
    """
    global llm_handler
    llm_handler = handler

# 全クライアント間で共有するチャット履歴（簡易実装：本番では DB 等に置き換え検討）
messages = []

@app.route('/')
def index():
    # 初回アクセス時に現在のメッセージを渡す
    return render_template('index.html', messages=messages)

@socketio.on('send_message')
def handle_send_message(data):
    """
    クライアントからユーザー入力メッセージを受信。
    data は { 'message': '入力テキスト' } の形を想定。
    """
    user_message = data.get('message', '').strip()
    if user_message:
        # ユーザーメッセージを履歴に追加
        msg_data = { 'sender': 'User', 'message': user_message }
        messages.append(msg_data)
        # クライアント全体へブロードキャスト
        emit('new_message', msg_data, broadcast=True)
        
        # ===== LLM連携部分 =====
        if llm_handler is not None:
            response = llm_handler(user_message)
        else:
            #response = f"LLM の応答: {user_message}"
            response = f"LLM の応答: {user_message}"
        
        llm_msg = { 'sender': 'LLM', 'message': response }
        messages.append(llm_msg)
        emit('new_message', llm_msg, broadcast=True)

@socketio.on('external_llm')
def handle_external_llm(data):
    """
    外部から LLM のメッセージを送るためのイベントハンドラ（デモ用）。
    """
    llm_msg = { 'sender': 'LLM', 'message': "これは外部から送られたLLMのメッセージです。" }
    messages.append(llm_msg)
    emit('new_message', llm_msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
