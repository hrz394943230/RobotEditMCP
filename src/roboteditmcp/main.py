"""Main entry point for RobotEditMCP."""

import asyncio
import logging

from mcp.server.stdio import stdio_server

from roboteditmcp.logging_config import setup_logging
from roboteditmcp.server import RobotEditMCPServer

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the MCP server."""
    # Setup logging
    setup_logging()
    logger.info("Starting RobotEditMCP server")

    try:
        # Create server instance
        mcp_server = RobotEditMCPServer()

        # Run server using stdio transport
        async def run_server():
            async with stdio_server() as (read_stream, write_stream):
                await mcp_server.get_server().run(
                    read_stream,
                    write_stream,
                    mcp_server.get_server().create_initialization_options(),
                )

        asyncio.run(run_server())

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("RobotEditMCP server stopped")


if __name__ == "__main__":
    main()
