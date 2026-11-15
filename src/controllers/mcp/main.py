import asyncio
import sys

import anyio

from src.controllers.mcp.server import mcp


def _new_event_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return asyncio.new_event_loop()


if __name__ == "__main__":
    anyio.run(
        mcp.run_async,
        backend_options={"loop_factory": _new_event_loop},
    )
