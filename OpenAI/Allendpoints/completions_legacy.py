#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/completions (legacy)")
    p.add_argument("-p", "--prompt", required=True)
    p.add_argument("--model", default="gpt-3.5-turbo-instruct")
    p.add_argument("--max-tokens", type=int, default=256)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    args = p.parse_args(argv)

    c = client()
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "max_tokens": args.max_tokens,
    }
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    resp = c.completions.create(**payload)  # type: ignore[attr-defined]
    print((resp.choices[0].text or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
