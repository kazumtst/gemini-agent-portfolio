# 必要なライブラリをインポート
import os
from google import genai
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Bedrock呼び出し用のAPIクライアントを作成
client = genai.Client()

# Converse Stream APIを実行
chat = client.chats.create(model="gemini-3.6-flash")
response = chat.send_message_stream("いろは歌を詠んで")


# ストリーミングレスポンスを取得して逐次表示
for chunk in response:
    print(chunk.text, end="", flush=True)
print()
