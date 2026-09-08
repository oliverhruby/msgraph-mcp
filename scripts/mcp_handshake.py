"""MCP stdio handshake smoke: initialize a server and list its tools.

Usage:
    python scripts/mcp_handshake.py <command> [args...]
    python scripts/mcp_handshake.py uvx --from dist/msgraph_mcp_full-0.1.0-py3-none-any.whl msgraph-mcp-full

Exits non-zero if the handshake fails or fewer than one tool is listed.
Counts tools and asserts a couple of canonical read/write probes exist.
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROBES = ["list_messages", "send_mail", "create_event", "upload_file"]
MIN_TOOLS = 150


async def main(cmd, *args) -> int:
    params = StdioServerParameters(command=cmd, args=list(args))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            res = await session.list_tools()
            tools = res.tools if hasattr(res, "tools") else res
            names = [t.name for t in tools]
            print(f"TOOL_COUNT {len(names)}")
            for probe in PROBES:
                print(f"{probe} {'OK' if probe in names else 'MISSING'}")
            for probe in PROBES:
                if probe not in names:
                    return 1
            if len(names) < MIN_TOOLS:
                print(f"ERROR: only {len(names)} tools, expected >= {MIN_TOOLS}")
                return 1
            return 0


if __name__ == "__main__":
    code = asyncio.run(main(*sys.argv[1:]))
    sys.exit(code)
