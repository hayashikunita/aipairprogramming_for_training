#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from typing import Optional

from common import client, pretty


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: Computer Use (Responses API) - preview stub")
    p.add_argument("task", help="PC操作でやってほしいこと（例: ブラウザで特定サイトにアクセスして情報を要約）")
    p.add_argument("--model", default="gpt-5")
    p.add_argument("--allow-run", action="store_true", help="実行を許可（プレビューのみが既定）")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    payload = {
        "model": args.model,
        "input": args.task,
        # 将来的なComputer/Browser/Bashなどのツール指定（プレビュー用途）
        "tools": [
            {"type": "computer"},
            {"type": "browser"},
            {"type": "bash"},
            {"type": "code_interpreter"},
        ],
    }

    if args.dry_run or not args.allow_run:
        print("[DRY-RUN] responses.create payload (computer-use preview):")
        print(pretty(payload))
        if not args.allow_run:
            print("\n注: Computer Use は限定プレビューのため、ここでは実行を抑止しています。--allow-run を付与しても権限が無い環境では失敗します。")
        return 0

    c = client()
    try:
        resp = c.responses.create(**payload)
    except Exception as e:
        print("Computer Use 実行でエラーが発生しました。権限や対応リージョン/モデルをご確認ください。\n", e)
        return 1

    print(pretty(resp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
