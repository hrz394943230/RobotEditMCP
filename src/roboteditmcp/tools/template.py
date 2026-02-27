"""Template management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_template_tools(client: RobotClient) -> list[Tool]:
    """
    Register all template management tools (7 tools).

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # ========================================
        # Discovery Tools (3)
        # ========================================
        # 1. template_get_scenes
        Tool(
            name="template_get_scenes",
            description="""Get all available scene types for template configurations.

Returns a list of scene names (e.g., ["ROBOT", "LLM", "CHAIN"]).

Use this to discover available scenes before querying factories or templates.""",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 2. template_get_factories
        Tool(
            name="template_get_factories",
            description="""Get all factory types for a given scene in template mode.

Parameters:
- scene: Scene type (e.g., 'ROBOT', 'LLM', 'CHAIN')

Returns dict with factory_names list.

Use this to discover available factory types before querying templates.""",
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
        # 3. template_get_factory_struct
        Tool(
            name="template_get_factory_struct",
            description="""Get template factory structure definition.

IMPORTANT: Requires both scene and factoryName parameters!

Note: Templates do NOT have tfs_actions (only config_schema).

Use this to understand:
- config_schema: Schema for configurations of this factory type

Ideal for exploring factory types without needing a specific template instance.

Parameters:
- scene: Scene type (e.g., 'ROBOT')
- factoryName: Factory name (e.g., 'RobotBrainTemplateSetting')

Returns TemplateFactoryStructDto.""",
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
        # Template Queries (2)
        # ========================================
        # 4. template_list
        Tool(
            name="template_list",
            description="""List available templates with pagination and filters.

Returns templates list with total count.

Parameters:
- page: Page number (default 1)
- pageSize: Items per page (default 10)

Optional filters:
- scene: Filter by scene type
- factoryName: Filter by factory type
- settingName: Filter by configuration name
- templateName: Filter by template name""",
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
                    "templateName": {
                        "type": "string",
                        "description": "Filter by template name",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default 1)",
                        "default": 1,
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Items per page (default 10)",
                        "default": 10,
                    },
                },
            },
        ),
        # 5. template_get
        Tool(
            name="template_get",
            description="""Get detailed information about a single template.

Returns TemplateFactorySettingDto with complete template information including:
- config_schema: Schema for configuration validation
- config: Template configuration content
- template_name: Template name

Note: Templates do NOT have tfs_actions.""",
            inputSchema={
                "type": "object",
                "required": ["setting_id"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Template ID",
                    },
                },
            },
        ),
        # ========================================
        # Template Operations (2)
        # ========================================
        # 6. template_apply
        Tool(
            name="template_apply",
            description="""Create a new draft configuration from a template.

Parameters:
- templateSettingId: Template ID to apply

Note:
- Does not support specifying a new configuration name
- After applying, use draft_update() to rename the configuration

Returns ApplyTemplateResponse with the created draft_id.""",
            inputSchema={
                "type": "object",
                "required": ["templateSettingId"],
                "properties": {
                    "templateSettingId": {
                        "type": "integer",
                        "description": "Template ID to apply",
                    },
                },
            },
        ),
        # 7. template_delete
        Tool(
            name="template_delete",
            description="""Delete a template.

Parameters:
- setting_id: Template ID to delete""",
            inputSchema={
                "type": "object",
                "required": ["setting_id"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Template ID",
                    },
                },
            },
        ),
    ]


async def handle_template_tool(
    tool_name: str, arguments: dict, client: RobotClient
) -> Any:
    """
    Handle template tool calls.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        client: Robot API client instance

    Returns:
        Tool result
    """
    handlers = {
        # Discovery
        "template_get_scenes": lambda: client.template.get_template_scenes(),
        "template_get_factories": lambda: client.template.get_template_factories(
            scene=arguments["scene"],
        ),
        "template_get_factory_struct": lambda: client.template.get_template_factory_struct(
            scene=arguments["scene"],
            factoryName=arguments["factoryName"],
        ),
        # Template Queries
        "template_list": lambda: client.template.list_templates(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
            templateName=arguments.get("templateName"),
            page=arguments.get("page", 1),
            pageSize=arguments.get("pageSize", 10),
        ),
        "template_get": lambda: client.template.get_template(arguments["setting_id"]),
        # Template Operations
        "template_apply": lambda: client.template.apply_template(
            arguments["templateSettingId"],
        ),
        "template_delete": lambda: client.template.delete_template(
            arguments["setting_id"],
        ),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
