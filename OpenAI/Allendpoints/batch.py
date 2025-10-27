#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, pretty


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/batch")
    sub = p.add_subparsers(dest="action", required=True)

    pc = sub.add_parser("create", help="バッチ作成")
    pc.add_argument("--input-file-id", required=True, help="files API でアップロード済みの JSONL ファイルID")
    pc.add_argument("--endpoint", default="/v1/chat/completions")
    pc.add_argument("--completion-window", default="24h")

    pl = sub.add_parser("list", help="一覧")

    args = p.parse_args(argv)
    c = client()

    if args.action == "create":
        resp = c.batches.create(
            input_file_id=args.input_file_id,
            endpoint=args.endpoint,
            completion_window=args.completion_window,
        )
        print(pretty(resp.model_dump()))
        return 0
    if args.action == "list":
        res = c.batches.list()
        for b in res.data:
            print(b.id, b.status)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
