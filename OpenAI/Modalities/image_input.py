#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import base64
import mimetypes
from typing import Optional
from common import client


def _read_image_as_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Modalities: Image (Input only)")
    p.add_argument("--prompt", required=True, help="画像に対する指示文")
    p.add_argument("--image", default=None, help="ローカル画像パス")
    p.add_argument("--image-url", dest="image_url", default=None, help="リモート画像URLまたは data URL")
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    # 画像の URL を決定
    url: Optional[str] = None
    redacted = False
    if args.image_url:
        url = args.image_url
    elif args.image:
        try:
            data_url = _read_image_as_data_url(args.image)
            url = data_url
            redacted = True  # dry-run表示では伏せる
        except Exception as e:
            print(f"画像読み込みエラー: {e}")
            return 2
    else:
        print("--image か --image-url のいずれかを指定してください")
        return 2

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": args.prompt},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        }
    ]
    payload = {"model": args.model, "messages": messages, "max_tokens": args.max_tokens}
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    if args.dry_run:
        import json
        preview = payload.copy()
        if redacted:
            # 実データURLは冗長なので伏せる
            preview = {
                **payload,
                "messages": [
                    {
                        **messages[0],
                        "content": [
                            messages[0]["content"][0],
                            {"type": "image_url", "image_url": {"url": "<data-url-redacted>"}},
                        ],
                    }
                ],
            }
        print("[DRY-RUN] chat.completions.create payload (image input):")
        print(json.dumps(preview, ensure_ascii=False, indent=2))
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
