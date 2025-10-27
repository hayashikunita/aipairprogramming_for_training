#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, save_b64_png


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/images/edits")
    p.add_argument("--image", required=True, help="元画像のパス (PNG推奨)")
    p.add_argument("--mask", default=None, help="マスク画像 (透明部を編集)")
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", default="gpt-image-1")
    p.add_argument("--output", default="image_edit.png")
    args = p.parse_args(argv)

    c = client()
    with open(args.image, "rb") as img:
        files = {"image": img}
        if args.mask:
            with open(args.mask, "rb") as m:
                resp = c.images.edits(model=args.model, image=img, mask=m, prompt=args.prompt)
        else:
            resp = c.images.edits(model=args.model, image=img, prompt=args.prompt)
    b64 = resp.data[0].b64_json
    if not b64:
        print("画像が返りませんでした")
        return 2
    save_b64_png(b64, args.output)
    print(f"saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
