# OpenAI API 全エンドポイント 学習用CLI

このフォルダには、OpenAI API の主要エンドポイントを一括で試せる CLI `openai_all_cli.py` が含まれます。

- models: モデル一覧
- chat: チャット生成
- completions: 旧/レガシー Completions（非推奨）
- edits: 旧/レガシー Edits（非推奨）
- embeddings: 埋め込み
- images: 画像生成
- transcribe: 音声→テキスト
- translate: 音声→英訳
- moderations: モデレーション
- files: ファイル upload/list/delete
- finetune: 微調整 create/list
- usage: 利用量（参考・非公式）

共通オプション:
- `--dry-run` 送信ペイロードのみ表示（APIを呼ばない）
- `--no-temperature` temperature を送信しない

## セットアップ

```powershell
# 依存をまだ入れていない場合（gpt-5配下の requirements を流用）
pip install -r ..\gpt-5\requirements.txt

# 音声/usage で requests を使う場合（一部参考実装）
pip install requests

# APIキー設定（PowerShell）
$env:OPENAI_API_KEY = "sk-..."    # セッション限定
setx OPENAI_API_KEY "sk-..."      # 永続（再起動後）
```

## 使用例

- モデル一覧
```powershell
python .\openai_all_cli.py models --dry-run
python .\openai_all_cli.py models
```

- チャット
```powershell
python .\openai_all_cli.py chat -p "Pythonのリスト内包表記を例で説明して" --dry-run
python .\openai_all_cli.py chat -p "Pythonのリスト内包表記を例で説明して"
```

- 埋め込み
```powershell
python .\openai_all_cli.py embeddings --text "自然言語処理とは何か？" --dry-run
```

- 画像生成（保存先は --output）
```powershell
python .\openai_all_cli.py images --prompt "a futuristic cityscape at night" --output night.png --dry-run
```

- 音声文字起こし / 翻訳（ファイル必須）
```powershell
python .\openai_all_cli.py transcribe --file .\audio_sample.mp3 --dry-run
python .\openai_all_cli.py translate  --file .\japanese_audio.mp3 --dry-run
```

- モデレーション
```powershell
python .\openai_all_cli.py moderations --text "I want to hurt someone." --dry-run
```

- ファイル操作
```powershell
# アップロード
python .\openai_all_cli.py files upload --file .\data.jsonl --purpose fine-tune --dry-run
# 一覧
python .\openai_all_cli.py files list --dry-run
# 削除
python .\openai_all_cli.py files delete --file-id file_abc123 --dry-run
```

- 微調整
```powershell
python .\openai_all_cli.py finetune create --training-file file_abc123 --model gpt-4o-mini --dry-run
python .\openai_all_cli.py finetune list --dry-run
```

- 利用量（参考実装）
```powershell
python .\openai_all_cli.py usage --dry-run
```

## 注意点
- completions / edits はレガシーです。新規は chat を推奨します。
- モデル名は環境や時期により変わります。`--model` オプションや環境変数（OPENAI_CHAT_MODEL など）で切り替えてください。
- usage はベータ/非公式で将来変更の可能性があります。
