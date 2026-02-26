"""Draft configuration management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_draft_tools(client: RobotClient) -> list[Tool]:
    """
    Register all draft configuration management tools.

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # 1. list_drafts
        Tool(
            name="list_drafts",
            description="""List draft configurations with optional filters.

Returns a list of draft configurations with full DTO information including config_schema and tfs_actions.

Example filters:
- scene: "ROBOT", "LLM", "CHAIN"
- factoryName: "RobotBrainDraftSetting"
- settingName: specific configuration name""",
            inputSchema={
                "type": "object",
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Filter by scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')",
                    },
                    "factoryName": {
                        "type": "string",
                        "description": "Filter by factory type (e.g., 'RobotBrainDraftSetting')",
                    },
                    "settingName": {
                        "type": "string",
                        "description": "Filter by configuration name",
                    },
                },
            },
        ),
        # 2. get_draft
        Tool(
            name="get_draft",
            description="""Get detailed information about a single draft configuration.

Returns complete DraftFactorySettingDto including:
- config_schema: Schema for configuration validation
- tfs_actions: All supported operations with metadata
- config: Current configuration content
- References in {setting_id, category} format""",
            inputSchema={
                "type": "object",
                "required": ["setting_id"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
                    },
                },
            },
        ),
        # 3. create_draft
        Tool(
            name="create_draft",
            description="""Create a new draft configuration.

Required parameters:
- scene: Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')
- name: Factory name (e.g., 'RobotBrainDraftSetting')
- setting_name: Configuration name
- config: Configuration content as JSON object

Returns DraftDetail with the created configuration.""",
            inputSchema={
                "type": "object",
                "required": ["scene", "name", "setting_name", "config"],
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')",
                    },
                    "name": {
                        "type": "string",
                        "description": "Factory name (e.g., 'RobotBrainDraftSetting')",
                    },
                    "setting_name": {
                        "type": "string",
                        "description": "Configuration name",
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration content (JSON object)",
                    },
                },
            },
        ),
        # 4. update_draft
        Tool(
            name="update_draft",
            description="""Update a draft configuration (supports partial update).

Parameters:
- setting_id: Configuration ID (required)
- setting_name: Configuration name (required)
- config: Configuration fields to update (only modified fields needed)

Note: setting_name is always required. Use Pydantic model_copy for partial updates.
Returns updated DraftFactorySettingDto.""",
            inputSchema={
                "type": "object",
                "required": ["setting_id", "setting_name", "config"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
                    },
                    "setting_name": {
                        "type": "string",
                        "description": "Configuration name (required)",
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration fields to update",
                    },
                },
            },
        ),
        # 5. delete_draft
        Tool(
            name="delete_draft",
            description="""Delete a draft configuration.

Parameters:
- setting_id: Draft configuration ID to delete""",
            inputSchema={
                "type": "object",
                "required": ["setting_id"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
                    },
                },
            },
        ),
        # 6. batch_create_drafts
        Tool(
            name="batch_create_drafts",
            description="""Batch create multiple draft configurations with internal references.

Use this to create interconnected configurations that reference each other.

Parameters:
- drafts: Array of draft objects, each containing:
  - temp_id: Negative integer for internal reference (e.g., -1, -2)
  - draft.scene: Scene type
  - draft.name: Factory name
  - draft.setting_name: Configuration name
  - draft.config: Configuration content

Referencing other drafts in batch:
Use {setting_id: -2, category: "Draft"} to reference the draft with temp_id=-2.

Returns:
- results: Array with success/failure status for each draft
- success_count, failure_count, total_count""",
            inputSchema={
                "type": "object",
                "required": ["drafts"],
                "properties": {
                    "drafts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["temp_id", "draft"],
                            "properties": {
                                "temp_id": {
                                    "type": "integer",
                                    "description": "Temporary ID (negative number)",
                                },
                                "draft": {
                                    "type": "object",
                                    "required": [
                                        "scene",
                                        "name",
                                        "setting_name",
                                        "config",
                                    ],
                                    "properties": {
                                        "scene": {"type": "string"},
                                        "name": {"type": "string"},
                                        "setting_name": {"type": "string"},
                                        "config": {"type": "object"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ),
        # 7. release_draft
        Tool(
            name="release_draft",
            description="""Release ALL draft configurations to production environment.

IMPORTANT: This releases the entire draft environment, not a single draft!

Requirements:
- Draft environment must contain exactly one Robot configuration
- Will clean existing online configs and publish drafts
- Failure will trigger rollback

Returns:
- onlineRobotId: Published Robot configuration ID""",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 8. get_factory_struct
        Tool(
            name="get_factory_struct",
            description="""Get factory structure information for a scene and factory type.

Use this to understand:
- config_schema: Schema for configurations of this factory type
- tfs_actions: All actions supported by this factory type

Ideal for exploring factory types without needing a specific configuration instance.

Parameters:
- scene: Scene type
- factoryName: Factory name

Returns DraftFactoryStructDto.""",
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
        # 9. trigger_draft_action
        Tool(
            name="trigger_draft_action",
            description="""Trigger an action on a draft configuration.

Actions are available in the tfs_actions field from get_draft() response.

Parameters:
- setting_id: Draft configuration ID
- action: Action name
- params: Optional action parameters (JSON object)

Note: Draft configurations cannot trigger CELERY async tasks (only online configs support this).

Returns ActionResult with success status and result.""",
            inputSchema={
                "type": "object",
                "required": ["setting_id", "action"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
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


async def handle_draft_tool(
    tool_name: str, arguments: dict, client: RobotClient
) -> Any:
    """
    Handle draft tool calls.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        client: Robot API client instance

    Returns:
        Tool result
    """
    handlers = {
        "list_drafts": lambda: client.list_drafts(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
        ),
        "get_draft": lambda: client.get_draft(arguments["setting_id"]),
        "create_draft": lambda: client.create_draft(
            scene=arguments["scene"],
            name=arguments["name"],
            setting_name=arguments["setting_name"],
            config=arguments["config"],
        ),
        "update_draft": lambda: client.update_draft(
            setting_id=arguments["setting_id"],
            setting_name=arguments["setting_name"],
            config=arguments["config"],
        ),
        "delete_draft": lambda: client.delete_draft(arguments["setting_id"]),
        "batch_create_drafts": lambda: client.batch_create_drafts(arguments["drafts"]),
        "release_draft": lambda: client.release_draft(),
        "get_factory_struct": lambda: client.get_factory_struct(
            scene=arguments["scene"],
            factoryName=arguments["factoryName"],
        ),
        "trigger_draft_action": lambda: client.trigger_draft_action(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
            params=arguments.get("params"),
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
