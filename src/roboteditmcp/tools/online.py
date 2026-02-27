"""Online configuration management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_online_tools(client: RobotClient) -> list[Tool]:
    """
    Register all online configuration management tools (7 tools).

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # ========================================
        # Discovery Tools (3)
        # ========================================
        # 1. online_get_scenes
        Tool(
            name="online_get_scenes",
            description="""Get all available scene types for online configurations.

Returns a list of scene names (e.g., ["ROBOT", "LLM", "CHAIN"]).

Use this to discover available scenes before querying factories or configurations.""",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 2. online_get_factories
        Tool(
            name="online_get_factories",
            description="""Get all factory types for a given scene in online mode.

Parameters:
- scene: Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')

Returns dict with factory_names list.

Use this to discover available factory types before querying configurations.""",
            inputSchema={
                "type": "object",
                "required": ["scene"],
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')",
                    },
                },
            },
        ),
        # 3. online_get_factory_struct
        Tool(
            name="online_get_factory_struct",
            description="""Get online factory structure definition.

IMPORTANT: Requires both scene and factoryName parameters!

Use this to understand:
- config_schema: Schema for configurations of this factory type
- tfs_actions: All actions supported by this factory type

Ideal for exploring factory types without needing a specific configuration instance.

Parameters:
- scene: Scene type (e.g., 'ROBOT')
- factoryName: Factory name (e.g., 'RobotBrainOnlineSetting')

Returns OnlineFactoryStructDto.""",
            inputSchema={
                "type": "object",
                "required": ["scene", "factoryName"],
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Scene type",
                    },
                    "factoryName": {
                        "type": "string",
                        "description": "Factory name",
                    },
                },
            },
        ),
        # ========================================
        # Configuration Queries (2)
        # ========================================
        # 4. online_list
        Tool(
            name="online_list",
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
        # 5. online_get
        Tool(
            name="online_get",
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
        # ========================================
        # Action Operations (2)
        # ========================================
        # 6. online_get_action_detail
        Tool(
            name="online_get_action_detail",
            description="""Get detailed information about a specific action on an online configuration.

Returns OnlineActionDetailDto with:
- Parameter schema
- Return value schema
- Action description
- Metadata (category, resourceOpType, isAsync, isPrivate)

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
        # 7. online_trigger_action
        Tool(
            name="online_trigger_action",
            description="""Trigger an action on an online configuration.

Actions are available in the tfs_actions field from online_get() response.

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
        # Discovery
        "online_get_scenes": lambda: client.online.get_online_scenes(),
        "online_get_factories": lambda: client.online.get_online_factories(
            scene=arguments["scene"],
        ),
        "online_get_factory_struct": lambda: client.online.get_online_factory_struct(
            scene=arguments["scene"],
            factoryName=arguments["factoryName"],
        ),
        # Configuration Queries
        "online_list": lambda: client.online.list_online_configs(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
        ),
        "online_get": lambda: client.online.get_online_config(arguments["setting_id"]),
        # Actions
        "online_get_action_detail": lambda: client.online.get_online_action_detail(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
        ),
        "online_trigger_action": lambda: client.online.trigger_online_action(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
            params=arguments.get("params"),
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
