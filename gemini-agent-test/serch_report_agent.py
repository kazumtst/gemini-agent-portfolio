import time
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
from duckduckgo_search import DDGS

from google.adk import Agent, Runner
try:
    from google.adk.sessions import InMemorySessionService
except ImportError:
    from google.adk.session_service import InMemorySessionService

from google.genai import errors, types

# .env ファイルから環境変数を読み込む
load_dotenv()

# ==========================================
# 1. ツールの定義 (Web検索 & メール送信)
# ==========================================
def search_web(query: str) -> str:
    """
    指定されたキーワードでWeb検索を行い、検索結果のテキストを返します。
    ユーザーからの質問に答えるための情報収集が必要な場合に使用してください。
    """
    print(f"🔧 [Tool: Web検索] 実行中... 検索ワード: {query}")
    try:
        results = list(DDGS().text(query, max_results=2))
        if not results:
            return "検索結果が見つかりませんでした。"
            
        formatted_results = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return formatted_results
    except Exception as e:
        return f"検索エラーが発生しました: {e}"


def send_email(subject: str, body: str) -> str:
    """
    あらかじめ設定されたメールアドレス宛にメールを送信します。
    調査結果や要約を報告する際に使用してください。
    """
    to_email = os.getenv("TO_EMAIL")
    sender_email = os.getenv("GMAIL_ADDRESS")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not sender_email or not sender_password or not to_email:
        return "ツールエラー: .env に必要な環境変数が設定されていません。"
        
    print(f"📧 [Tool: メール送信] 実行中... 宛先={to_email}, 件名={subject}")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        
        print("✅ メール送信成功！")
        return "メールの送信が正常に完了しました。"
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")
        return f"メールの送信に失敗しました: {e}"


# ==========================================
# 2. エージェントの定義
# ==========================================
agent = Agent(
    name="research_and_email_agent",
    model="gemini-3.6-flash",
    tools=[search_web, send_email],
    instruction="""
    あなたの責務はユーザからの質問を調査し、結果を要約してメールで送ることです。
    以下のルールに従って自律的にツールを選択・実行してください。
    
    1. ユーザーから質問を受け取ったら、`search_web` ツールを使って最新情報を検索してください。
    2. 無限ループを防ぐため、Web検索の実行は【最大2回まで】とします。
    3. 得られた情報を分析し、分かりやすく簡潔に要約してください。
    4. `send_email` ツールを使用して、件名(subject)と要約本文(body)を指定し、メールを送信してください。メール送信は【1回のみ】とします。
    5. 最終的なユーザーへの返答として、「どのような内容でメールを送信したか」を簡潔に報告してください。
    """
)

# ==========================================
# 3. 実行メイン処理 (非同期化)
# ==========================================
async def main():
    print("=== 🌐 Webリサーチ & 自動送信エージェント (Google ADK版) ===")
    
    # ユーザー入力の受付
    search_query = input("[検索内容を入力]: ")
    if not search_query.strip():
        print("入力が空のため、終了します。")
        return
        
    user_prompt = f"「{search_query}」について調べて、結果を要約してメールで送信してください。"
    print(f"\n🚀 エージェントに指示を送信しました...\n")

    # ADKのセッション管理とRunnerの初期化
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name="research_app"
    )

    # ★【修正点】非同期関数なので await を付与
    session = await session_service.create_session(
        app_name="research_app",
        user_id="default_user"
    )

    # ユーザー入力をADK用の Content 形式にパッケージング
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_prompt)]
    )

    # サーバーエラー（503等）発生時のリトライ設定
    max_retries = 3
    base_delay = 5

    for attempt in range(max_retries):
        try:
            print(f"🤖 エージェント実行中... (試行 {attempt + 1}/{max_retries})")
            
            # runner.run も非同期の場合は await が必要（※同期メソッドの場合はそのまま）
            # ここでは非同期として await を付与
            event_stream = runner.run(
                user_id="default_user",
                session_id=session.id,
                new_message=user_message
            )
            
            print("\n=== 🤖 エージェントからの処理経過 & 最終報告 ===")
            for event in event_stream:
                if hasattr(event, 'content') and event.content and event.content.parts:
                    text_chunk = event.content.parts[0].text
                    if text_chunk:
                        print(text_chunk, end="")
            print()
            break

        except errors.ServerError as e:
            if e.code == 503:
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)
                    print(f"⚠️ サーバー混雑中(503)。{sleep_time}秒後に再試行します...")
                    await asyncio.sleep(sleep_time) # time.sleepの代わりにasyncio.sleepを使用
                else:
                    print("❌ 最大リトライ回数に達しました。処理を中断します。")
            else:
                print(f"❌ サーバーエラーが発生しました: {e.message}")
                break
        except Exception as e:
            print(f"❌ 予期せぬエラーが発生しました: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main())