#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List


async def main() -> int:
    try:
        # mcp >= 0.1 系の想定API
        from mcp.server import Server  # type: ignore
        from mcp.server.stdio import stdio_server  # type: ignore
        from mcp.types import Tool, TextContent  # type: ignore
    except Exception as e:
        print("mcp パッケージが必要です。pip install mcp\n", e)
        return 2

    server = Server("sample-mcp-server")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="ping",
                description="Return 'pong'",
                input_schema={"type": "object", "properties": {}},
            ),
            Tool(
                name="time_now",
                description="Return current time in ISO8601 (UTC)",
                input_schema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        if name == "ping":
            return [TextContent(type="text", text="pong")]
        if name == "time_now":
            now = datetime.now(timezone.utc).isoformat()
            return [TextContent(type="text", text=now)]
        raise Exception(f"Unknown tool: {name}")

    async with stdio_server() as (read, write):
        await server.run(read, write)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
