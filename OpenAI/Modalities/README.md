# Modalities サンプル

このフォルダでは入力モダリティごとの最小サンプルを提供します。ここだけで Text / Image / Audio / Video が完結します。モデル名はオプションで変更できるので、必要に応じて入れ替えるだけでOKです。

- Text: 入出力（Chat Completions）
- Image: 入力のみ（画像＋指示→テキスト応答）
- Audio: 入力（音声→文字起こし／英訳／要約／QA）
- Video: 入力（動画→音声トラックを文字起こし／英訳／要約／QA）

事前準備（共通）

```powershell
pip install openai
$env:OPENAI_API_KEY = "sk-..."
```

## Text 入出力

ファイル: `text_io.py`

```powershell
python .\text_io.py -p "Pythonで辞書を反復する最小例は？" --dry-run
python .\text_io.py -p "Pythonで辞書を反復する最小例は？"
```

オプション: `--model` `--system` `--max-tokens` `--temperature` `--no-temperature` `--dry-run`

## Image 入力のみ

ファイル: `image_input.py`

ローカル画像を使う例（data URL で送信／dry-run では伏せ字表示）

```powershell
python .\image_input.py --prompt "この画像の要約を日本語で" --image .\sample.png --dry-run
```

リモート画像URLを使う例

```powershell
python .\image_input.py --prompt "この画像の要約を日本語で" --image-url "https://example.com/sample.jpg" --dry-run
```

オプション: `--image` または `--image-url` のいずれか必須、`--model`（既定: gpt-4o-mini）、`--max-tokens`、`--temperature`、`--no-temperature`、`--dry-run`

## Audio 入力

ファイル: `audio_input.py`

用途: 音声ファイル（mp3/mp4/mpeg/mpga/m4a/wav/webmなど）を文字起こし/英訳し、必要なら要約やQAまで実行します。

```powershell
# 文字起こし（日本語維持）
python .\audio_input.py --file .\sample.m4a --task transcribe --dry-run
python .\audio_input.py --file .\sample.m4a --task transcribe

# 英訳（日本語→英語）
python .\audio_input.py --file .\sample.m4a --task translate

# 要約（文字起こし→Chatで要約）
python .\audio_input.py --file .\sample.m4a --task summarize --chat-model gpt-5

# 質問応答（文字起こし→ChatでQA）
python .\audio_input.py --file .\sample.m4a --task qa --prompt "主要な意思決定ポイントを3つ挙げて" --chat-model gpt-5
```

主要オプション: `--file`（必須）, `--task`（transcribe/translate/summarize/qa）, `--model`（音声モデル。既定: whisper-1）, `--chat-model`（要約/QAで使用。既定: gpt-5）, `--system`, `--max-tokens`, `--temperature`, `--no-temperature`, `--dry-run`

ヒント: `--model whisper-1` は広く使えます。必要に応じて `gpt-4o-mini-transcribe` に差し替えてください（アカウントで有効な場合）。

## Video 入力

ファイル: `video_input.py`

用途: 動画ファイル（mp4/mpeg/mov/webmなど）の音声トラックを使って文字起こし/英訳し、必要なら要約やQAまで実行します（追加ツール不要）。

```powershell
# 文字起こし
python .\video_input.py --file .\movie.mp4 --task transcribe --dry-run
python .\video_input.py --file .\movie.mp4 --task transcribe

# 要約
python .\video_input.py --file .\movie.mp4 --task summarize --chat-model gpt-5

# 質問応答
python .\video_input.py --file .\movie.mp4 --task qa --prompt "プレゼンの結論は？" --chat-model gpt-5
```

主要オプション: `--file`（必須）, `--task`, `--model`（音声モデル。既定: whisper-1）, `--chat-model`, `--system`, `--max-tokens`, `--temperature`, `--no-temperature`, `--dry-run`

注意: 動画→テキストは、動画の音声トラックを Whisper/Transcribe API で処理します。映像の内容（画面テキストや図）を直接解析するわけではありません。映像の要約が必要で音声情報だけでは不十分な場合は、キーフレームのスクリーンショットを `image_input.py` で解析する方法も検討してください。
