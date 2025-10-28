#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone


def main() -> int:
    try:
        from fastmcp import FastMCP  # type: ignore
    except Exception as e:
        print("fastmcp パッケージが必要です。pip install fastmcp\n", e)
        return 2

    app = FastMCP("fastmcp-sample-server")

    @app.tool()
    def ping() -> str:
        """Return 'pong'"""
        return "pong"

    @app.tool()
    def time_now() -> str:
        """現在のUTC時刻を ISO8601 で返します"""
        return datetime.now(timezone.utc).isoformat()

    # stdio transport で起動
    app.run_stdio()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
