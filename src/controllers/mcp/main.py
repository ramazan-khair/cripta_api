import asyncio
import sys

from src.controllers.mcp.server import mcp


def _new_event_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return asyncio.new_event_loop()


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=_new_event_loop) as runner:
        runner.run(mcp.run_async())
