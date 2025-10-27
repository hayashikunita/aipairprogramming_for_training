#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
from typing import Optional

API_URL = "https://api.openai.com/v1/videos"


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/videos (参考: REST)")
    p.add_argument("--model", required=True, help="動画生成対応モデル")
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", default="video_job.json", help="応答を保存")
    args = p.parse_args(argv)

    try:
        import requests  # type: ignore
    except Exception:
        print("requests が必要です。pip install requests")
        return 2

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 未設定")
        return 2

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": args.model, "prompt": args.prompt}
    r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    try:
        data = r.json()
    except Exception:
        data = {"status_code": r.status_code, "text": r.text}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
