#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Iterable, Optional


def iter_files(root: Path, glob: Optional[str]) -> Iterable[Path]:
    if glob:
        yield from root.rglob(glob)
    else:
        yield from root.rglob("*")


def search_in_file(path: Path, pattern: Optional[re.Pattern[str]]) -> Iterable[tuple[int, str]]:
    if not pattern:
        return []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if pattern.search(line):
                    yield (i, line.rstrip("\n"))
    except Exception:
        return []


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: File search (name/content)")
    p.add_argument("--root", default=".", help="検索ルート")
    p.add_argument("--glob", default=None, help="ファイル名のglob (例: **/*.py)")
    p.add_argument("--query", default=None, help="内容検索の正規表現")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    pattern = re.compile(args.query, re.IGNORECASE) if args.query else None

    if args.dry_run:
        print(f"[DRY-RUN] file_search: root={root}, glob={args.glob}, query={args.query}")
        return 0

    for path in iter_files(root, args.glob):
        if not path.is_file():
            continue
        if pattern:
            hits = list(search_in_file(path, pattern))
            if hits:
                print(f"\n{path}")
                for (ln, text) in hits[:50]:
                    print(f"  {ln:>5}: {text[:200]}")
        else:
            print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
