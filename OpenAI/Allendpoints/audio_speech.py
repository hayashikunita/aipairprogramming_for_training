#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/audio/speech (Text-to-Speech)")
    p.add_argument("--text", required=True)
    p.add_argument("--model", default="gpt-4o-mini-tts")
    p.add_argument("--voice", default="alloy")
    p.add_argument("--format", default="mp3")
    p.add_argument("--output", default="speech.mp3")
    args = p.parse_args(argv)

    c = client()
    # ストリーミングでファイル保存（SDK推奨パターン）
    with c.audio.speech.with_streaming_response.create(
        model=args.model,
        voice=args.voice,
        input=args.text,
        format=args.format,
    ) as response:
        response.stream_to_file(args.output)
    print(f"saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
