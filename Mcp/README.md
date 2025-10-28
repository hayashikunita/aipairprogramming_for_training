# MCP サンプルサーバ（Python / stdio）

このフォルダには、Model Context Protocol (MCP) の最小サンプルサーバを収録しています。stdio 経由で起動し、`ping` と `time_now` の2つのツールを提供します。

## セットアップ

```powershell
pip install mcp
```

## 起動（stdio サーバ）

```powershell
python .\Mcp\server.py
```

このコマンドはサーバープロセスとして標準入出力を待機します。通常はクライアント（例: `OpenAI/Tools/mcp_client.py`）から起動されます。

### FastMCP 版の起動

```powershell
python .\Mcp\fast_server.py
```

`fastmcp` を使用した簡潔な定義のサンプルです（下記 requirements を参照）。

## ツール一覧

- ping: 'pong' を返します（入力なし）
- time_now: 現在のUTC時刻を ISO8601 で返します（入力なし）

## クライアントからの接続例（同リポジトリのツールを使用）

`OpenAI/Tools/mcp_client.py` は stdio 経由で任意の MCP サーバーに接続し、ツール一覧を取得します。

```powershell
python .\OpenAI\Tools\mcp_client.py --server-cmd "python .\Mcp\server.py" --dry-run
python .\OpenAI\Tools\mcp_client.py --server-cmd "python .\Mcp\server.py"

# FastMCP 版
python .\OpenAI\Tools\mcp_client.py --server-cmd "python .\Mcp\fast_server.py" --dry-run
python .\OpenAI\Tools\mcp_client.py --server-cmd "python .\Mcp\fast_server.py"
```

出力例（期待値）:

```
Tools:
- ping: Return 'pong'
- time_now: Return current time in ISO8601 (UTC)
```

## 注意事項

- 本サンプルは最小実装です。ツールの引数検証やエラー整形などは必要に応じて拡張してください。
- stdio 以外のトランスポート（WebSocket 等）を使う場合は、対応するトランスポート実装に切り替えてください。

## 依存関係（requirements）

```text
mcp>=0.1.0
fastmcp>=0.1.0
```

