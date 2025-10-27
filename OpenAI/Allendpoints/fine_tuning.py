#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, pretty


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/fine-tuning")
    sub = p.add_subparsers(dest="action", required=True)

    pc = sub.add_parser("create", help="ジョブ作成")
    pc.add_argument("--training-file", required=True, help="file-id (files APIでアップロード済み)")
    pc.add_argument("--model", required=True, help="微調整対象モデル")

    pl = sub.add_parser("list", help="ジョブ一覧")

    args = p.parse_args(argv)

    c = client()
    if args.action == "create":
        resp = c.fine_tuning.jobs.create(training_file=args.training_file, model=args.model)
        print(pretty(resp.model_dump()))
        return 0
    if args.action == "list":
        jobs = c.fine_tuning.jobs.list()
        for j in jobs.data:
            print(j.id, j.status, j.model)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
