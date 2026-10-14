from google.adk import Agent
from google.genai.errors import APIError, ServerError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


# 1. ツール関数に @retry デコレータを付与
@retry(
    # 503エラー(ServerError) や 429エラー(APIError) 発生時にリトライ
    retry=retry_if_exception_type((ServerError, APIError)),
    stop=stop_after_attempt(3),  # 最大3回試行
    wait=wait_random_exponential(min=1, max=10),  # 1秒〜10秒の間でランダムに待機
    reraise=True,
)
def get_live_weather_forecast(location: str) -> dict:
    """指定された場所のリアルタイム天気予報を取得します。

    Args:
        location: 都市名や地域名（例: "東京都新宿区"）

    Returns:
        temperature と forecast を含む辞書
    """
    # 実際のWeb API呼び出しロジックなどをここに記述
    return {"temperature": "22C", "forecast": "Cloudy"}


# 2. Agent定義（安定性の高いモデルを指定）
root_agent = Agent(
    name="weather_concierge",
    # 混雑しやすいモデル（3.6など）で503が出る場合は、一時的に 2.5-flash 等に切り替えるのも有効です
    model="gemini-3.6-flash",
    instruction="ユーザーの地域の天気を調べ、それに合わせた活動を提案してください。",
    tools=[get_live_weather_forecast],
)