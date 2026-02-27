"""Draft configuration management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_draft_tools(client: RobotClient) -> list[Tool]:
    """
    Register all draft configuration management tools (12 tools).

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # ========================================
        # Discovery Tools (2)
        # ========================================
        # 1. draft_get_scenes
        Tool(
            name="draft_get_scenes",
            description="""Get all available scene types for draft configurations.

Returns a list of scene names (e.g., ["ROBOT", "LLM", "CHAIN"]).

Use this to discover available scenes before querying factories or configurations.""",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 2. draft_get_factories
        Tool(
            name="draft_get_factories",
            description="""Get all factory types for a given scene in draft mode.

Parameters:
- scene: Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')

Returns dict with factory_names list.

Use this to discover available factory types before creating configurations.""",
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
        # ========================================
        # Factory Structure (1)
        # ========================================
        # 3. draft_get_factory_struct
        Tool(
            name="draft_get_factory_struct",
            description="""Get draft factory structure definition.

IMPORTANT: Only requires factoryName parameter, NOT scene!

Use this to understand:
- config_schema: Schema for configurations of this factory type
- tfs_actions: All actions supported by this factory type

Ideal for exploring factory types without needing a specific configuration instance.

Parameters:
- factoryName: Factory name (e.g., 'RobotBrainDraftSetting')

Returns DraftFactoryStructDto.""",
            inputSchema={
                "type": "object",
                "required": ["factoryName"],
                "properties": {
                    "factoryName": {
                        "type": "string",
                        "description": "Factory name (e.g., 'RobotBrainDraftSetting')",
                    },
                },
            },
        ),
        # ========================================
        # CRUD Operations (6)
        # ========================================
        # 4. draft_list
        Tool(
            name="draft_list",
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
        # 5. draft_get
        Tool(
            name="draft_get",
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
        # 6. draft_create
        Tool(
            name="draft_create",
            description="""Create a new draft configuration.

Required parameters:
- scene: Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')
- name: Factory name (e.g., 'RobotBrainDraftSetting')
- setting_name: Configuration name
- config: Configuration content as JSON object

Returns DraftFactorySettingDto with the created configuration.""",
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
        # 7. draft_update
        Tool(
            name="draft_update",
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
        # 8. draft_delete
        Tool(
            name="draft_delete",
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
        # 9. draft_batch_create
        Tool(
            name="draft_batch_create",
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
        # ========================================
        # Release Operations (1)
        # ========================================
        # 10. draft_release
        Tool(
            name="draft_release",
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
        # ========================================
        # Template Operations (1)
        # ========================================
        # 11. draft_save_as_template
        Tool(
            name="draft_save_as_template",
            description="""Save a draft configuration as a template.

Uses DraftFactorySettingPostDto structure for request body.

Parameters:
- draft_id: Draft configuration ID (required)
- name: Factory name (required)
- scene: Scene type (optional)
- setting_name: Template name (optional)
- config: Configuration data (optional)

Returns dict with templateId.""",
            inputSchema={
                "type": "object",
                "required": ["draft_id", "name"],
                "properties": {
                    "draft_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
                    },
                    "name": {
                        "type": "string",
                        "description": "Factory name (required)",
                    },
                    "scene": {
                        "type": "string",
                        "description": "Scene type (optional)",
                    },
                    "setting_name": {
                        "type": "string",
                        "description": "Template name (optional)",
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration data (optional)",
                    },
                },
            },
        ),
        # ========================================
        # Action Triggers (1)
        # ========================================
        # 12. draft_trigger_action
        Tool(
            name="draft_trigger_action",
            description="""Trigger an action on a draft configuration.

Actions are available in the tfs_actions field from get_draft() response.

Note: Uses PUT method. Draft configurations cannot trigger CELERY async tasks.

Parameters:
- setting_id: Draft configuration ID
- action: Action name
- params: Optional action parameters (JSON object)

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
        # Discovery
        "draft_get_scenes": lambda: client.draft.get_draft_scenes(),
        "draft_get_factories": lambda: client.draft.get_draft_factories(
            scene=arguments["scene"],
        ),
        # Factory Structure
        "draft_get_factory_struct": lambda: client.draft.get_draft_factory_struct(
            factoryName=arguments["factoryName"],
        ),
        # CRUD
        "draft_list": lambda: client.draft.list_drafts(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
        ),
        "draft_get": lambda: client.draft.get_draft(arguments["setting_id"]),
        "draft_create": lambda: client.draft.create_draft(
            scene=arguments["scene"],
            name=arguments["name"],
            setting_name=arguments["setting_name"],
            config=arguments["config"],
        ),
        "draft_update": lambda: client.draft.update_draft(
            setting_id=arguments["setting_id"],
            setting_name=arguments["setting_name"],
            config=arguments["config"],
        ),
        "draft_delete": lambda: client.draft.delete_draft(arguments["setting_id"]),
        "draft_batch_create": lambda: client.draft.batch_create_drafts(
            arguments["drafts"],
        ),
        # Release
        "draft_release": lambda: client.draft.release_draft(),
        # Template
        "draft_save_as_template": lambda: client.draft.save_as_template(
            draft_id=arguments["draft_id"],
            name=arguments["name"],
            scene=arguments.get("scene"),
            setting_name=arguments.get("setting_name"),
            config=arguments.get("config"),
        ),
        # Actions
        "draft_trigger_action": lambda: client.draft.trigger_draft_action(
            setting_id=arguments["setting_id"],
            action=arguments["action"],
            params=arguments.get("params"),
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
