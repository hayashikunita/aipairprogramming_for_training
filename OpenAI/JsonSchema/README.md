# JSON Schema を用いた応答の構造化サンプル

このフォルダには、OpenAI Chat Completions API の `response_format: json_schema` を使って、モデルに厳密な JSON を生成させる学習用スクリプトが含まれます。

- `jsonSchema_v1.py`: 内蔵スキーマ（todo, contact）での基本サンプル
- `jsonSchema_v2.py`: 外部スキーマ読込対応（--schema-file）。内蔵に `invoice` スキーマを同梱

- 内蔵スキーマ: `todo`, `contact`
- `--dry-run` で送信ペイロードのみ表示（APIキー不要）
- 返却JSONは Python の `jsonschema` で検証（インストールされていれば）
- 一部モデルで `temperature` 非対応の可能性に備え、`--no-temperature` で送信抑止と自動フォールバック

## セットアップ

```powershell
cd "c:\Users\toush\Desktop\works\hayashi_work\program\AIpairprogramming_for_training\OpenAI\JsonSchema"
pip install -r requirements.txt

# APIキー（PowerShell）
$env:OPENAI_API_KEY = "sk-..."
```

## 使い方（v1）

- ToDo スキーマで生成
```powershell
python .\jsonSchema_v1.py -p "今日のタスクを3件、期限と優先度付きで出力" --schema todo --dry-run
# 実行
python .\jsonSchema_v1.py -p "今日のタスクを3件、期限と優先度付きで出力" --schema todo
```

- 連絡先スキーマで生成
```powershell
python .\jsonSchema_v1.py -p "田中太郎さんの連絡先を出力" --schema contact --dry-run
```

- temperature を送らない（非対応モデル対策）
```powershell
python .\jsonSchema_v1.py -p "テスト" --schema todo --no-temperature --dry-run

## 使い方（v2）

- 内蔵スキーマ（invoice）
```powershell
python .\jsonSchema_v2.py -p "請求書を1件、通貨JPYで、3明細を含めて出力" --schema invoice --dry-run
```

- 外部スキーマ（schema.json を読み込む）
```powershell
python .\jsonSchema_v2.py -p "スキーマに従ってデータを出力" --schema-file .\schema.json --dry-run
```
```

## 備考
- JSON Schema は Draft 2020-12 の記法に沿っています。
- スキーマを増やしたい場合は `SCHEMAS` 辞書に追加してください。
- Responses API でも `response_format: {type: 'json_schema', json_schema: {...}}` が利用可能です。必要であれば同等の関数を追加します。
