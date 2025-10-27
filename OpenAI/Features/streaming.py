#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import sys
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Streaming: Chat Completions のストリーミング受信")
    p.add_argument("-p", "--prompt", required=True)
    p.add_argument("--system", default="あなたは有能な日本語アシスタントです。")
    p.add_argument("--model", default="gpt-5")
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    args = p.parse_args(argv)

    c = client()
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": args.system},
            {"role": "user", "content": args.prompt},
        ],
        "max_tokens": args.max_tokens,
        "stream": True,
    }
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    # ストリームを受け取りつつ、deltaをそのまま表示
    stream = c.chat.completions.create(**payload)
    for chunk in stream:
        try:
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                sys.stdout.write(text)
                sys.stdout.flush()
        except Exception:
            # 予期しないイベントは無視
            pass
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
