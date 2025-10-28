#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import base64
from pathlib import Path
from typing import Optional

from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: Image generation")
    p.add_argument("prompt", help="画像生成プロンプト")
    p.add_argument("--model", default="gpt-image-1")
    p.add_argument("--size", default="1024x1024", choices=["256x256", "512x512", "1024x1024"])
    p.add_argument("--format", default="png", choices=["png", "b64_json"])
    p.add_argument("--out", default="out.png", help="保存先 (format=png時)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.dry_run:
        print(f"[DRY-RUN] images.generate: model={args.model}, size={args.size}, format={args.format}, prompt='{args.prompt}'")
        return 0

    c = client()
    resp = c.images.generate(model=args.model, prompt=args.prompt, size=args.size)
    data = resp.data[0]

    if args.format == "png":
        # SDKは直接PNGバイナリではなく、b64_jsonを返すことが多い
        if getattr(data, "b64_json", None):
            img_b64 = data.b64_json
        else:
            # 将来の互換フィールド
            img_b64 = getattr(data, "image_base64", None)
        if not img_b64:
            raise RuntimeError("画像データが取得できませんでした。")
        Path(args.out).write_bytes(base64.b64decode(img_b64))
        print(f"saved: {args.out}")
    else:
        # b64_jsonをそのまま表示（長いので先頭のみ）
        img_b64 = data.b64_json
        print((img_b64 or "")[:120] + "...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
