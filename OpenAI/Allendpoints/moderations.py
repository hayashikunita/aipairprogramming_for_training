#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, pretty


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/moderations")
    p.add_argument("--text", required=True)
    p.add_argument("--model", default="omni-moderation-latest")
    args = p.parse_args(argv)

    c = client()
    resp = c.moderations.create(model=args.model, input=args.text)
    print(pretty(resp.model_dump()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
