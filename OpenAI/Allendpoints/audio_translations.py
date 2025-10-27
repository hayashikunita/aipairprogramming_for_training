#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/audio/translations (to English)")
    p.add_argument("--file", required=True)
    p.add_argument("--model", default="whisper-1")
    args = p.parse_args(argv)

    c = client()
    with open(args.file, "rb") as f:
        resp = c.audio.translations.create(model=args.model, file=f)
    print(resp.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
