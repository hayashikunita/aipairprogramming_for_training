#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: Web search (DuckDuckGo)")
    p.add_argument("query", help="検索クエリ")
    p.add_argument("--limit", type=int, default=5, help="最大件数")
    p.add_argument("--safe", choices=["off", "moderate", "strict"], default="moderate")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.dry_run:
        print(f"[DRY-RUN] duckduckgo_search: query='{args.query}', limit={args.limit}, safe={args.safe}")
        return 0

    try:
        from duckduckgo_search import DDGS  # type: ignore
    except Exception as e:
        print("duckduckgo-search パッケージが必要です。pip install duckduckgo-search\n", e)
        return 2

    with DDGS() as ddgs:
        results = ddgs.text(args.query, max_results=args.limit, safesearch=args.safe)
    for i, item in enumerate(results, 1):
        title = item.get("title")
        href = item.get("href")
        snippet = item.get("body") or item.get("snippet")
        print(f"[{i}] {title}\n{href}\n{(snippet or '')[:220]}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
