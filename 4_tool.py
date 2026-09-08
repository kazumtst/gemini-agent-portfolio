import json
import urllib.request
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .envファイルから環境変数を読み込む
load_dotenv()

# APIクライアントの作成
client = genai.Client()

input_text = "2025年7月の祝日はいつ？"

# 祝日を取得する関数定義
def get_japanese_holidays(year: int) -> dict:
    """指定された年の日本の祝日一覧を取得します"""
    url = f"https://holidays-jp.github.io/api/v1/{year}/date.json"
    with urllib.request.urlopen(url) as response:
        data = response.read()
        holidays = json.loads(data)
    return holidays

# ========================================
# 1回目の推論：ツールの使用要否と引数の確認
# ========================================
print("【推論1回目】")
print("ユーザーの入力： ", input_text)

# 自動実行(AFC)を無効化する設定
config = types.GenerateContentConfig(
    tools=[get_japanese_holidays],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)

# 1回目のリクエスト実行
response1 = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=input_text,
    config=config
)

# ツール呼び出しの要求を検出
function_call = None
if response1.function_calls:
    function_call = response1.function_calls[0]
    print("ツール要求： ", function_call.name, function_call.args)
    print()

# ========================================
# 2回目の推論：ツール実行結果を渡して最終回答
# ========================================
if function_call:
    # 1. アプリ側でツール（Python関数）を実行
    year = int(function_call.args["year"])
    holidays = get_japanese_holidays(year)
    tool_result = {
        "year": year,
        "holidays": holidays,
        "count": len(holidays)
    }
    print("【アプリから直接、ツール実行して結果を取得】")
    print(tool_result)
    print()

    # 2. 会話履歴の構築（1回目の入力 ＋ 1回目のLLM出力 ＋ ツール実行結果）
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=input_text)]
        ),
        response1.candidates[0].content,  # 1回目のLLMレスポンス (FunctionCallを含む)
        types.Content(
            role="user",
            parts=[
                types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": tool_result}
                )
            ]
        )
    ]

    # 3. ツール結果を含めて2回目の推論を実行
    response2 = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents,
        config=config
    )

    print("【推論2回目】")
    print("ユーザーの入力： （ツール実行結果）")
    print("LLMの回答： ", response2.text)
