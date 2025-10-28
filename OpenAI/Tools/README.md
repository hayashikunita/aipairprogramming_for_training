# Tools サンプル

このフォルダには次のツール系ミニスクリプトを収録しています。各スクリプトは `--dry-run` を備え、まず安全に挙動を確認できます。モデルはオプションで差し替え可能です。

- Web search: `web_search.py`（DuckDuckGo）
- File search: `file_search.py`（ローカルファイル名/内容検索）
- Image generation: `image_generation.py`（Images API）
- Code interpreter: `code_interpreter.py`（Assistants API）
- Computer use: `computer_use.py`（Responses API, プレビュー）
- MCP: `mcp_client.py`（Model Context Protocol クライアント: stdio）

## 準備

PowerShell 例:

```powershell
pip install -r .\OpenAI\Tools\requirements.txt
$env:OPENAI_API_KEY = "sk-..."
```

## Web search

```powershell
python .\OpenAI\Tools\web_search.py "python datetime timezone" --limit 5 --dry-run
python .\OpenAI\Tools\web_search.py "python datetime timezone" --limit 5
```

備考: サードパーティの `duckduckgo-search` を使用（APIキー不要）。

## File search

```powershell
python .\OpenAI\Tools\file_search.py --root . --glob "**/*.py" --query "client\(\)" --dry-run
python .\OpenAI\Tools\file_search.py --root . --glob "**/*.py" --query "client\(\)"
```

## Image generation

```powershell
python .\OpenAI\Tools\image_generation.py "a cute corgi in watercolor" --size 512x512 --dry-run
python .\OpenAI\Tools\image_generation.py "a cute corgi in watercolor" --size 512x512 --out .\corgi.png
```

オプション: `--model`（既定: gpt-image-1）, `--size`（256/512/1024）, `--format`（png/b64_json）, `--out`

## Code interpreter（Assistants API）

```powershell
python .\OpenAI\Tools\code_interpreter.py "CSVを読み込み、売上上位5商品を棒グラフにして説明"
```

実行の流れ: Assistant作成（code_interpreter有効）→Thread作成→Run→完了待ち→応答表示。

## Computer use（Responses API, preview）

```powershell
python .\OpenAI\Tools\computer_use.py "ブラウザでOpenAIのブログを開いて最新記事を要約" --dry-run
```

注: Computer Use は限定プレビュー機能です。実行には対応アカウント/モデルが必要です。`--allow-run` を付けても環境によっては失敗します（既定はプレビューのみ）。

## MCP クライアント

stdio対応のMCPサーバーに接続し、ツール一覧を取得します。

```powershell
python .\OpenAI\Tools\mcp_client.py --server-cmd "uvx some-mcp-server --stdio" --dry-run
python .\OpenAI\Tools\mcp_client.py --server-cmd "uvx some-mcp-server --stdio"
```

`mcp` パッケージが必要です。サーバーコマンド例はご利用のMCPサーバーに合わせてください。

## 個人情報マスク付きの実行動画について

Windows では以下いずれかの方法が手軽です:

- Xbox Game Bar: Win+G → 録画開始（設定でマイク/システム音や解像度を調整）
- OBS Studio: ソースに「ウィンドウキャプチャ」を追加し、録画対象を限定。
- ffmpeg: 画面全体を録画し、後処理でモザイク（例: 右下1/4にPixellate）

録画後のマスク（OBSフィルタ or ffmpeg）例:

```powershell
# 画面録画（例: 1920x1080, 30fps）
# ffmpeg の gdigrab/desktop capture は環境依存です。OBSを推奨。

# 後処理で右下をモザイク（おおまかな例）
# ffmpeg -i input.mp4 -filter_complex "[0:v]split=2[v0][v1];[v1]crop=iw/2:ih/2:iw/2:ih/2,boxblur=10[mask];[v0][mask]overlay=main_w/2:main_h/2[out]" -map "[out]" -map 0:a? -c:a copy output_masked.mp4
```

実録に使うコマンドは本READMEの各サンプル（`--dry-run`→本実行）をご利用ください。録画対象はターミナルとエディタに限定すると個人情報の露出を抑えられます。

