# GPT-5 学習用サンプル

このフォルダには、OpenAI の GPT-5 を想定した Python サンプル `sample_script.py` が含まれます。

- シンプルなチャット応答: `chat`
- JSON 形式の出力: `json`
- 関数ツール呼び出しデモ: `tools`
- ネットワーク不要の動作確認: `--dry-run`
- 一部モデル向け: `--no-temperature`（temperature を送信しない）

## セットアップ

1) 依存関係のインストール

```powershell
# カレントディレクトリをこのフォルダにしてから
pip install -r requirements.txt
```

2) OpenAI API キー設定 (PowerShell)

```powershell
# セッション限定
$env:OPENAI_API_KEY = "sk-..."

# 永続設定（再起動後有効）
setx OPENAI_API_KEY "sk-..."
```

必要に応じてモデル名を環境変数で上書きできます:

```powershell
$env:OPENAI_GPT5_MODEL = "gpt-5"
```

## 使い方

- 基本チャット

```powershell
python .\sample_script.py chat -p "Pythonでファイルを読み込む最小例を教えて"
```

- JSON 形式での出力（テーブル型の要約など）

```powershell
python .\sample_script.py json -p "今日のToDoを3件、titleとpriorityのJSONで出力"
```

- ツール呼び出しデモ（現在時刻をツールで取得）

```powershell
python .\sample_script.py tools -p "今の東京の時刻を教えて"
```

- 送信内容の確認だけしたい場合（APIキー不要）

```powershell
python .\sample_script.py chat  -p "テスト" --dry-run
python .\sample_script.py json  -p "テスト" --dry-run
python .\sample_script.py tools -p "テスト" --dry-run

### temperature が使えない/無視されるモデルについて

一部のモデルでは `temperature` パラメータがサポート外、または無視される場合があります。

- 明示的に送らない: `--no-temperature`
- 自動フォールバック: API が `temperature` に関するエラーを返した場合、このスクリプトは `temperature` を外して自動で再試行します。

必要に応じて `--temperature 0.0` で決定性を高められます（サポートされるモデルのみ）。
```

## 備考
- このスクリプトは OpenAI Python SDK v1 系を想定しています。
- 一部の機能（JSONモードやツール呼び出し）の挙動はモデル・SDKバージョンにより差異が出ることがあります。
- Windows のタイムゾーン名は IANA 形式（例: `Asia/Tokyo`）を使います。無効な場合は UTC にフォールバックします。
