#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import asyncio
import json
import os
from typing import Optional

WS_URL = "wss://api.openai.com/v1/realtime"


async def _run(model: str, say: Optional[str]) -> int:
    try:
        import websockets  # type: ignore
    except Exception:
        print("websockets が必要です。pip install websockets")
        return 2

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 未設定")
        return 2

    url = f"{WS_URL}?model={model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }
    async with websockets.connect(url, extra_headers=headers) as ws:
        if say:
            # 簡易的にテキスト発話イベントを送る例
            await ws.send(json.dumps({
                "type": "response.create",
                "response": {"instructions": say}
            }))
        # 1メッセージだけ受信して終了
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(msg)
        except asyncio.TimeoutError:
            print("(受信タイムアウト: 接続確認のみ)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/realtime (WebSocket 参考)")
    p.add_argument("--model", required=True)
    p.add_argument("--say", default=None, help="簡易的に送る指示テキスト")
    args = p.parse_args(argv)

    return asyncio.run(_run(args.model, args.say))


if __name__ == "__main__":
    raise SystemExit(main())
