import os
from google import genai
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む (GEMINI_API_KEY を自動認識します)
load_dotenv()

# Gemini呼び出し用のAPIクライアントを作成
client = genai.Client()

# APIを実行
chat = client.chats.create(model="gemini-3.6-flash")
response = chat.send_message("こんにちは")

# 実行結果のテキストだけを画面に表示
print(response.text)