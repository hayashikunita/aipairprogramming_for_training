#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Modalities: Text (Input/Output)")
    p.add_argument("-p", "--prompt", required=True)
    p.add_argument("--system", default="あなたは有能な日本語アシスタントです。")
    p.add_argument("--model", default="gpt-5")
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": args.prompt},
    ]
    payload = {"model": args.model, "messages": messages, "max_tokens": args.max_tokens}
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    if args.dry_run:
        import json
        print("[DRY-RUN] chat.completions.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    c = client()
    try:
        resp = c.chat.completions.create(**payload)
    except Exception as e:
        if "temperature" in payload and "temperature" in str(e).lower():
            payload.pop("temperature", None)
            resp = c.chat.completions.create(**payload)
        else:
            raise
    print((resp.choices[0].message.content or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
