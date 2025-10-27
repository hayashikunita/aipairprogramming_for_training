#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, save_b64_png


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/images/generations")
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", default="gpt-image-1")
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--quality", default="standard")
    p.add_argument("--output", default="image.png")
    args = p.parse_args(argv)

    c = client()
    resp = c.images.generate(model=args.model, prompt=args.prompt, size=args.size, quality=args.quality, n=1)
    b64 = resp.data[0].b64_json
    if not b64:
        print("画像が返りませんでした")
        return 2
    save_b64_png(b64, args.output)
    print(f"saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
