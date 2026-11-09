#!/usr/bin/env python3
"""Call one tool on the project-local opt-in Blender MCP bridge."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: blender_mcp_call.py TOOL JSON_ARGS")
    params = StdioServerParameters(
        command="/home/ajuntanaga/Documents/Codex/Blender-MCP/run_blender_mcp",
        args=[],
        env={
            "BLENDER_MCP_HOST": "127.0.0.1",
            "BLENDER_MCP_PORT": "9876",
            "BLENDER_PATH": "/snap/bin/blender",
        },
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            raw_args = sys.argv[2]
            if raw_args.startswith("@script:"):
                path = Path(raw_args[8:]).resolve()
                source = path.read_text(encoding="utf-8")
                arguments = {
                    "code": (
                        f"path = {str(path)!r}\n"
                        "namespace = {'__file__': path, '__name__': '__main__'}\n"
                        f"exec(compile({source!r}, path, 'exec'), namespace)\n"
                    )
                }
            elif raw_args.startswith("@code:"):
                arguments = {"code": Path(raw_args[6:]).read_text(encoding="utf-8")}
            elif raw_args.startswith("@"):
                arguments = json.loads(Path(raw_args[1:]).read_text(encoding="utf-8"))
            else:
                arguments = json.loads(raw_args)
            response = await session.call_tool(sys.argv[1], arguments)
            if response.isError:
                raise RuntimeError(str(response.content))
            payload = response.structuredContent
            if payload is None:
                payload = [item.model_dump(mode="json") for item in response.content]
            print(json.dumps(payload, indent=2, sort_keys=True))


asyncio.run(main())
