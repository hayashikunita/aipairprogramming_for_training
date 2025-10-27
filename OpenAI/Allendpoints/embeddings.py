#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/embeddings")
    p.add_argument("--text", required=True)
    p.add_argument("--model", default="text-embedding-3-large")
    args = p.parse_args(argv)

    c = client()
    resp = c.embeddings.create(model=args.model, input=args.text)
    vec = resp.data[0].embedding
    print(len(vec), vec[:8])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
