#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, pretty


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/responses")
    p.add_argument("-p", "--prompt", required=True)
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--json", action="store_true", help="json_object で構造化出力")
    args = p.parse_args(argv)

    c = client()
    kwargs = {"model": args.model, "input": args.prompt}
    if args.json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = c.responses.create(**kwargs)
    print(resp.model_dump_json(indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
