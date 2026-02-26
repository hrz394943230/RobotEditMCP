"""Online configuration management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_online_tools(client: RobotClient) -> list[Tool]:
    """
    Register all online configuration management tools.

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # 10. list_online_configs
        Tool(
            name="list_online_configs",
            description="""List production environment configurations with optional filters.

Returns a list of OnlineFactorySettingDto with complete information including config_schema and tfs_actions.

Filters:
- scene: Filter by scene type
- factoryName: Filter by factory type
- settingName: Filter by configuration name""",
            inputSchema={
                "type": "object",
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Filter by scene type",
                    },
                    "factoryName": {
                        "type": "string",
                        "description": "Filter by factory type",
                    },
                    "settingName": {
                        "type": "string",
                        "description": "Filter by configuration name",
                    },
                },
            },
        ),
        # 11. get_online_config
        Tool(
            name="get_online_config",
            description="""Get detailed information about a single online configuration.

Returns OnlineFactorySettingDto including:
- config_schema: Schema for configuration
- tfs_actions: All supported operations with metadata
- config: Current configuration content
- References in {setting_id, category} format""",
            inputSchema={
                "type": "object",
                "required": ["setting_id"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Online configuration ID",
                    },
                },
            },
        ),
        # 12. get_online_action_detail
        Tool(
            name="get_online_action_detail",
            description="""Get detailed information about a specific action on an online configuration.

Returns OnlineActionDetailDto with:
- Parameter schema
- Return value schema
- Action description
- Metadata

Note: Only online configurations support this endpoint (not draft).""",
            inputSchema={
                "type": "object",
                "required": ["setting_id", "action"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Online configuration ID",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action name",
                    },
                },
            },
        ),
        # 13. trigger_online_action
        Tool(
            name="trigger_online_action",
            description="""Trigger an action on an online configuration.

Actions are available in the tfs_actions field from get_online_config() response.

Parameters:
- setting_id: Online configuration ID
- action: Action name
- params: Optional action parameters (JSON object)

Note: Online configurations support triggering CELERY async tasks.

Returns ActionResult with success status and result.""",
            inputSchema={
                "type": "object",
                "required": ["setting_id", "action"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Online configuration ID",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action name from tfs_actions",
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional action parameters",
                    },
                },
            },
        ),
    ]


async def handle_online_tool(
    tool_name: str, arguments: dict, client: RobotClient
) -> Any:
    """
    Handle online tool calls.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        client: Robot API client instance

    Returns:
        Tool result
    """
    handlers = {
        "list_online_configs": lambda: client.list_online_configs(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
        ),
        "get_online_config": lambda: client.get_online_config(arguments["setting_id"]),
        "get_online_action_detail": lambda: client.get_online_action_detail(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
        ),
        "trigger_online_action": lambda: client.trigger_online_action(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
            params=arguments.get("params"),
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
