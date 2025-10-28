#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import shlex
from typing import Optional


async def _run(server_cmd: str) -> int:
    try:
        from mcp import ClientSession  # type: ignore
        from mcp.transport.stdio import StdioServerTransport  # type: ignore
    except Exception as e:
        print("mcp パッケージが必要です。pip install mcp\n", e)
        return 2

    # server_cmd は例: "uvx some-mcp-server --flag" や "node .\\server.js"
    argv = shlex.split(server_cmd)
    transport = StdioServerTransport(argv[0], argv[1:])

    async with ClientSession(transport) as session:
        await session.start()
        await session.initialize()

        # ツール一覧
        tools = await session.list_tools()
        print("Tools:")
        for t in tools:
            print(f"- {t.name}: {t.description}")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: MCP client (stdio)")
    p.add_argument("--server-cmd", required=True, help="起動コマンド（stdio対応MCPサーバー）")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.dry_run:
        print(f"[DRY-RUN] mcp stdio connect: {args.server_cmd}")
        return 0

    return asyncio.run(_run(args.server_cmd))


if __name__ == "__main__":
    raise SystemExit(main())
