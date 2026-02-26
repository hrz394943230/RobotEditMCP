"""Metadata tools for scenes and factories."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_metadata_tools(client: RobotClient) -> list[Tool]:
    """
    Register all metadata tools.

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # 19. list_scenes
        Tool(
            name="list_scenes",
            description="""List all available scene types.

Returns a list of scene names like:
["ROBOT", "LLM", "CHAIN", ...]

Use this as the starting point for exploring the Robot configuration system.
After getting scenes, use list_factories() to see factory types for each scene.""",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 20. list_factories
        Tool(
            name="list_factories",
            description="""List all factory types for a given scene and configuration type.

Parameters:
- scene: Scene type (required)
- type: Configuration type - "draft", "online", or "template" (default "draft")

Returns FactoryListResponse with factory_names list like:
["RobotBrainDraftSetting", "LLMProviderDraftSetting", ...]

Use this to discover what factory types are available for a specific scene.""",
            inputSchema={
                "type": "object",
                "required": ["scene"],
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')",
                    },
                    "type": {
                        "type": "string",
                        "description": "Configuration type - 'draft', 'online', or 'template'",
                        "enum": ["draft", "online", "template"],
                        "default": "draft",
                    },
                },
            },
        ),
    ]


async def handle_metadata_tool(
    tool_name: str, arguments: dict, client: RobotClient
) -> Any:
    """
    Handle metadata tool calls.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        client: Robot API client instance

    Returns:
        Tool result
    """
    handlers = {
        "list_scenes": lambda: client.list_scenes(),
        "list_factories": lambda: client.list_factories(
            scene=arguments["scene"],
            type=arguments.get("type", "draft"),
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
