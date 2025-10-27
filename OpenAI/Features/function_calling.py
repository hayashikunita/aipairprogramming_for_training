#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
from typing import Any, Dict, List, Optional
from common import client


# デモ用の関数: 疑似天気情報を返す
# 実際のAPI呼び出しは行いません（学習用）

def get_weather(city: str) -> Dict[str, Any]:
    demo = {
        "Tokyo": {"temp_c": 24, "condition": "Cloudy"},
        "Osaka": {"temp_c": 26, "condition": "Sunny"},
        "Sapporo": {"temp_c": 18, "condition": "Rain"},
    }
    return demo.get(city, {"temp_c": 22, "condition": "Unknown"})


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "指定都市の現在の天気(ダミー)を返します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "都市名 (例: Tokyo)"}
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]


def _dispatch_tool(name: str, args: Dict[str, Any]) -> str:
    if name == "get_weather":
        return json.dumps(get_weather(**args), ensure_ascii=False)
    raise ValueError(f"unknown tool: {name}")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Function calling: tools を使った関数呼び出し")
    p.add_argument("-p", "--prompt", required=True, help="例: '東京の天気を教えて' など")
    p.add_argument("--model", default="gpt-5")
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    args = p.parse_args(argv)

    c = client()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "必要に応じて get_weather を呼び出してください。"},
        {"role": "user", "content": args.prompt},
    ]

    payload_base: Dict[str, Any] = {
        "model": args.model,
        "max_tokens": args.max_tokens,
        "tools": TOOLS,
        "tool_choice": "auto",
    }
    if not args.no_temperature:
        payload_base["temperature"] = args.temperature

    for _ in range(4):
        resp = c.chat.completions.create(messages=messages, **payload_base)
        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )
            # ローカル実行し、tool メッセージを追加
            for tc in tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _dispatch_tool(tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": result,
                    }
                )
            continue
        # ツール呼び出しが無ければ最終応答
        print((msg.content or "").strip())
        return 0

    print("(ツール呼び出しが収束しませんでした)")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
