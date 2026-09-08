```markdown
# Gemini API (google-genai) 実装サンプル集 for スタートアップ

本リポジトリは、Google の最新 AI SDK である `google-genai` を使用し、AWS などの複雑なインフラ構築（Bedrock 等）の手間をかけずに、自社プロダクトやプロトタイプへ迅速に Gemini モデルを組み込むための、シンプルかつ実用的な Python 実装コード集です。

最小限の構成で、基本的な対話からストリーミング、推論（Thinking）制御、手動 Function Calling までをステップバイステップで実装・検証できます。

---

## 🛠️ 事前準備：Gemini API キーの取得と設定

Gemini API を利用するには、APIキーが必要です。以下の手順に従って準備を行ってください。

### 1. API キーの取得
1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、ご自身の Google アカウントでログインします。
2. 「Create API key（または Get API key）」をクリックし、新規の API キーを生成します。

### 2. 環境変数の設定
セキュリティを考慮し、APIキーはソースコード内に直接書き込まず（ハードコードせず）、環境変数として管理します。

プロジェクトのルート直下に `.env` ファイルを作成し、以下のように取得した API キーを記述してください。

```env
GEMINI_API_KEY=YOUR_ACTUAL_API_KEY

```

> **⚠️ 重要（セキュリティ対策）：**
> 本リポジトリを GitHub などのパブリックリポジトリに公開する際は、`.env` ファイルがコミットに含まれないよう、必ず `.gitignore` ファイルに `.env` を追加してください。
> ```gitignore
> # .gitignore
> .env
> 
> ```
> 
> 

`google-genai` SDK は、`genai.Client()` を呼び出すだけで、自動的に環境変数 `GEMINI_API_KEY` を検知して初期化を行う安全な仕様になっています。

---

## 📂 各プログラムの概要と重要解説

本リポジトリには、番号順に以下のプログラムが含まれています。

### 1. `1_converse.py`（基本対話）

Gemini API を用いて、1往復のシンプルなテキストチャットを行う基本スクリプトです。

* **処理の流れ:**
1. `load_dotenv()` で `.env` の環境変数をロードします。
2. `genai.Client()` で、自動的にAPIキーが設定されたクライアントインスタンスを生成します。
3. `client.chats.create(model="gemini-3.6-flash")` で対話セッションを開始します。
4. `send_message("こんにちは")` でユーザー入力を送信し、応答（`response.text`）を表示します。



---

### 2. `2_stream.py`（ストリーミング対話）

ChatGPTなどのように、AIの回答を1文字ずつリアルタイムに出力し、ユーザー体験（UX）を劇的に向上させる実装です。

* **処理の流れ:**
1. `send_message_stream("...")` を使って、一度にすべての応答を待つのではなく、生成された順に逐次レスポンスを受け取ります。
2. 返却されたジェネレータから `for chunk in response:` ループを用いて部分テキスト（`chunk.text`）を取得し、`flush=True` でターミナルへ即座に描画します。



---

### 3. `3_thinking.py`（思考プロセスの制御とエラー処理）

Gemini が最終的な回答を導き出すまでの「推論（思考）の過程」を表示・制御します。また、サーバー高負荷時のエラーハンドリングを適用する基盤となります。

* **処理の流れ:**
1. `types.ThinkingConfig(thinking_budget=1024)` を使い、推論のためのトークン予算（上限）を明示的に指定します。
2. `getattr(part, "thought", None)` を用いて、モデルの応答から「推論プロセス」と「最終的な回答」を正確に識別します。
3. 推論プロセスは `<thinking>` 〜 `</thinking>` のタグで囲んでターミナルに出力し、思考のステータスを可視化します。
4. 実運用時には、混雑による 503 エラー（`google.genai.errors.ServerError`）などを想定し、指数バックオフなどの自動リトライ機構と組み合わせるのが推奨されます。



---

### 4. `4_tool.py`（手動Tool Use / Function Calling）

あえてSDKによる自動実行（Automatic Function Calling: AFC）を無効化（`disable=True`）し、自社システム側で2段階の推論とツール実行フローを完全にコントロールする実装です。

* **処理の流れ:**
1. 日本の祝日データを外部APIから取得する Python 関数 `get_japanese_holidays(year)` を定義します。
2. **【1回目の推論】**: `tools=[get_japanese_holidays]` と `automatic_function_calling=... (disable=True)` を設定し、モデルがツールを実行すべきか、どの引数を使うべきかを判定させ、`response1.function_calls` でその要求を検知します。
3. **【アプリ側での実行】**: アプリ側（Python）で実際に該当関数を呼び出し、祝日データを取得します。
4. **【2回目の推論】**: 1回目の入力、FunctionCallを含むLLMレスポンス、そして `types.Part.from_function_response` を用いて構築した「ツールの実行結果」をメッセージ履歴として再送信し、最終回答を取得します。

## 🚀 インストールと実行方法

### 1. 依存ライブラリのインストール

リポジトリをクローン後、以下のパッケージをインストールします。

```bash
pip install google-genai python-dotenv

```

### 2. スクリプトの実行

番号順に実行して動作を確認してください。

```bash
# 基本対話
python 1_converse.py

# ストリーミング対話
python 2_stream.py

# 思考プロセス制御
python 3_thinking.py

# 手動Tool Use
python 4_tool.py

```

```

```