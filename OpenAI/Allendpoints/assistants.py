#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from typing import Optional
from common import client, pretty


def _get_assistants_iface(c):
    # SDK の世代により beta/非beta が異なる可能性があるため両対応
    try:
        return c.assistants
    except AttributeError:
        return c.beta.assistants  # type: ignore[attr-defined]


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="v1/assistants")
    sub = p.add_subparsers(dest="action", required=True)

    pc = sub.add_parser("create", help="アシスタント作成")
    pc.add_argument("--name", required=True)
    pc.add_argument("--instructions", default="あなたは有能なアシスタントです。")
    pc.add_argument("--model", default="gpt-4o-mini")

    pl = sub.add_parser("list", help="一覧")

    args = p.parse_args(argv)
    c = client()
    a = _get_assistants_iface(c)

    if args.action == "create":
        resp = a.create(name=args.name, instructions=args.instructions, model=args.model)
        print(pretty(resp.model_dump()))
        return 0
    if args.action == "list":
        res = a.list()
        for asst in res.data:
            print(asst.id, getattr(asst, "name", "(no-name)"))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
