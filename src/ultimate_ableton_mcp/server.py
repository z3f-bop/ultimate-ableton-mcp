"""FastMCP server — registers 7 operation-dispatched tools for Ableton Live."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .connection import get_connection, shutdown_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("ultimate-ableton-mcp")


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Connect on startup, disconnect on shutdown."""
    try:
        conn = get_connection()
        logger.info("Ableton connection ready (%s:%d)", conn.host, conn.port)
    except Exception as e:
        logger.warning("Could not connect on startup: %s", e)
    yield {}
    shutdown_connection()
    logger.info("Server shut down")


mcp = FastMCP(
    "UltimateAbletonMCP",
    instructions="Ableton Live integration — 7 operation-dispatched tools",
    lifespan=lifespan,
)

# Import tool modules AFTER mcp is defined (they import mcp from here)
from . import tools  # noqa: E402, F401


def main():
    mcp.run()


if __name__ == "__main__":
    main()
