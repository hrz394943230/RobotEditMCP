"""MCP server for Robot configuration management."""

import logging

from mcp.server import Server
from mcp.types import TextContent, Tool

from roboteditmcp.client import RobotClient
from roboteditmcp.config import config
from roboteditmcp.logging_config import setup_logging
from roboteditmcp.tools import (
    handle_draft_tool,
    handle_online_tool,
    handle_template_tool,
    register_draft_tools,
    register_online_tools,
    register_template_tools,
)

logger = logging.getLogger(__name__)


class RobotEditMCPServer:
    """MCP server for Robot configuration management."""

    def __init__(self):
        """Initialize the MCP server."""
        # Setup logging
        setup_logging()
        logger.info("Initializing RobotEditMCP server")

        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            logger.error(f"Configuration validation failed: {error_msg}")
            raise ValueError(f"Configuration error: {error_msg}")

        # Create Robot API client
        self.client = RobotClient()

        # Create MCP server
        self.server = Server("roboteditmcp")

        # Register all tools
        self._register_tools()

        logger.info("RobotEditMCP server initialized successfully")

    def _register_tools(self):
        """Register all MCP tools."""
        all_tools = []
        all_tools.extend(register_draft_tools(self.client))
        all_tools.extend(register_online_tools(self.client))
        all_tools.extend(register_template_tools(self.client))

        logger.info(f"Registered {len(all_tools)} tools")

        # Register tool handler
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return all_tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")

            try:
                # Route to appropriate handler based on tool category
                tool_categories = {
                    # Draft tools (12 tools)
                    "draft_get_scenes": handle_draft_tool,
                    "draft_get_factories": handle_draft_tool,
                    "draft_get_factory_struct": handle_draft_tool,
                    "draft_list": handle_draft_tool,
                    "draft_get": handle_draft_tool,
                    "draft_create": handle_draft_tool,
                    "draft_update": handle_draft_tool,
                    "draft_delete": handle_draft_tool,
                    "draft_batch_create": handle_draft_tool,
                    "draft_release": handle_draft_tool,
                    "draft_save_as_template": handle_draft_tool,
                    "draft_trigger_action": handle_draft_tool,
                    # Online tools (7 tools)
                    "online_get_scenes": handle_online_tool,
                    "online_get_factories": handle_online_tool,
                    "online_get_factory_struct": handle_online_tool,
                    "online_list": handle_online_tool,
                    "online_get": handle_online_tool,
                    "online_get_action_detail": handle_online_tool,
                    "online_trigger_action": handle_online_tool,
                    # Template tools (7 tools)
                    "template_get_scenes": handle_template_tool,
                    "template_get_factories": handle_template_tool,
                    "template_get_factory_struct": handle_template_tool,
                    "template_list": handle_template_tool,
                    "template_get": handle_template_tool,
                    "template_apply": handle_template_tool,
                    "template_delete": handle_template_tool,
                }

                if name not in tool_categories:
                    raise ValueError(f"Unknown tool: {name}")

                handler = tool_categories[name]
                result = await handler(name, arguments, self.client)

                # Return formatted result
                return [
                    TextContent(
                        type="text",
                        text=str(result) if not isinstance(result, str) else result,
                    )
                ]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                raise

    def get_server(self) -> Server:
        """Get the MCP server instance."""
        return self.server

    def close(self):
        """Close the server and cleanup resources."""
        logger.info("Closing RobotEditMCP server")
        self.client.close()
