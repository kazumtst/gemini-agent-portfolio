import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .envファイルから環境変数を読み込む
load_dotenv()

# クライアント作成
client = genai.Client()

# チャットセッションを作成（思考設定をconfigに指定）
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=1024,  # 思考トークン数
        ),
    ),
)

# メッセージ送信
response = chat.send_message("このプログラムを実行後、推論しているステータス時にはターミナルに<thinking>タグが出るようにするにはどうすればいい")

# 思考プロセスと最終回答を分けて表示
if response.candidates and response.candidates[0].content.parts:
    for part in response.candidates[0].content.parts:
        thought_val = getattr(part, "thought", None)

        # パターンA: part.thought が bool値 (True) で、part.text に思考文が入るケース
        if isinstance(thought_val, bool) and thought_val:
            print("<thinking>")
            print(part.text)
            print("</thinking>\n")

        # パターンB: part.thought 自体に思考テキスト（文字列）が入っているケース
        elif isinstance(thought_val, str) and thought_val.strip():
            print("<thinking>")
            print(thought_val)
            print("</thinking>\n")

        # 通常の最終回答テキスト
        elif part.text:
            print(part.text)
