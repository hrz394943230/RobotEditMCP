"""RobotEditMCP - MCP server for Robot configuration management."""

__version__ = "0.1.0"

from roboteditmcp.config import config
from roboteditmcp.client import RobotClient
from roboteditmcp.server import RobotEditMCPServer

__all__ = [
    "config",
    "RobotClient",
    "RobotEditMCPServer",
]
