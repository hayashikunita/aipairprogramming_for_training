## Features サンプル

このフォルダには OpenAI API の代表的な機能を試す学習用スクリプトが含まれます。

- Streaming … `streaming.py`（Chat Completions のストリーミング受信）
- Function calling … `function_calling.py`（tools でローカル関数を呼び出し）
- Structured outputs … `structured_outputs.py`（JSON出力: json_object / json_schema）
- Fine-tuning … `fine_tuning.py`（jobs create / list）
- Distillation … `distillation.py`（Teacher で合成データを作成し JSONL 化）

共通準備（PowerShell）

```powershell
pip install openai
$env:OPENAI_API_KEY = "sk-..."
```

## Streaming

```powershell
python .\streaming.py -p "Pythonでファイルを読む最小例を教えて"
```

## Function calling

```powershell
python .\function_calling.py -p "東京の天気を教えて"
```

- get_weather(city) をツールとしてモデルが呼び出し、ローカルで実行 → 結果を tool メッセージで渡して最終回答。

## Structured outputs

```powershell
# JSON Schema で厳密出力
python .\structured_outputs.py -p "価格付きの商品を3つ提案して(日本語で)"

# json_object の簡易モード
python .\structured_outputs.py -p "ToDoを3件" --use-json-object
```

## Fine-tuning

```powershell
# file-id は files API でアップロード済みの JSONL のID
python .\fine_tuning.py create --training-file file_abc123 --model gpt-4o-mini
python .\fine_tuning.py list
```

## Distillation（知識蒸留・合成データ作成）

```powershell
# prompts.txt: 1行=1プロンプト
python .\distillation.py --prompts .\prompts.txt --teacher-model gpt-5 --output dataset.jsonl
```

- 生成された `dataset.jsonl` を files API でアップロード後、`fine_tuning.py` でジョブを作成して学習に回せます。
- 実運用ではプロンプト/応答の品質・偏りを確認し、必要な前処理を行ってください。
