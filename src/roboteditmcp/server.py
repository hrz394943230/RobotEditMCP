"""MCP server for Robot configuration management."""

import logging

from mcp.server import Server
from mcp.types import TextContent, Tool

from roboteditmcp.client import RobotClient
from roboteditmcp.config import config
from roboteditmcp.logging_config import setup_logging
from roboteditmcp.tools import (
    handle_draft_tool,
    handle_metadata_tool,
    handle_online_tool,
    handle_template_tool,
    register_draft_tools,
    register_metadata_tools,
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
        all_tools.extend(register_metadata_tools(self.client))

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
                    # Draft tools
                    "list_drafts": handle_draft_tool,
                    "get_draft": handle_draft_tool,
                    "create_draft": handle_draft_tool,
                    "update_draft": handle_draft_tool,
                    "delete_draft": handle_draft_tool,
                    "batch_create_drafts": handle_draft_tool,
                    "release_draft": handle_draft_tool,
                    "get_factory_struct": handle_draft_tool,
                    "trigger_draft_action": handle_draft_tool,
                    # Online tools
                    "list_online_configs": handle_online_tool,
                    "get_online_config": handle_online_tool,
                    "get_online_action_detail": handle_online_tool,
                    "trigger_online_action": handle_online_tool,
                    # Template tools
                    "list_templates": handle_template_tool,
                    "get_template": handle_template_tool,
                    "apply_template": handle_template_tool,
                    "save_as_template": handle_template_tool,
                    "delete_template": handle_template_tool,
                    # Metadata tools
                    "list_scenes": handle_metadata_tool,
                    "list_factories": handle_metadata_tool,
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
