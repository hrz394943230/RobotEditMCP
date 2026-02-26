"""Template management tools."""

import logging
from typing import Any

from mcp.types import Tool

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


def register_template_tools(client: RobotClient) -> list[Tool]:
    """
    Register all template management tools.

    Args:
        client: Robot API client instance

    Returns:
        List of MCP tools
    """
    return [
        # 14. list_templates
        Tool(
            name="list_templates",
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
                "required": ["page", "pageSize"],
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
        # 15. get_template
        Tool(
            name="get_template",
            description="""Get detailed information about a single template.

Returns TemplateFactorySettingDto with complete template information.""",
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
        # 16. apply_template
        Tool(
            name="apply_template",
            description="""Create a new draft configuration from a template.

Parameters:
- templateSettingId: Template ID to apply

Note:
- Does not support specifying a new configuration name
- After applying, use update_draft() to rename the configuration

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
        # 17. save_as_template
        Tool(
            name="save_as_template",
            description="""Save a draft configuration as a template.

Parameters:
- setting_id: Draft configuration ID
- name: Template name (passed in request body)

Returns TemplateFactorySettingDto.""",
            inputSchema={
                "type": "object",
                "required": ["setting_id", "name"],
                "properties": {
                    "setting_id": {
                        "type": "integer",
                        "description": "Draft configuration ID",
                    },
                    "name": {
                        "type": "string",
                        "description": "Template name",
                    },
                },
            },
        ),
        # 18. delete_template
        Tool(
            name="delete_template",
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


async def handle_template_tool(tool_name: str, arguments: dict, client: RobotClient) -> Any:
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
        "list_templates": lambda: client.list_templates(
            scene=arguments.get("scene"),
            factoryName=arguments.get("factoryName"),
            settingName=arguments.get("settingName"),
            templateName=arguments.get("templateName"),
            page=arguments.get("page", 1),
            pageSize=arguments.get("pageSize", 10),
        ),
        "get_template": lambda: client.get_template(arguments["setting_id"]),
        "apply_template": lambda: client.apply_template(arguments["templateSettingId"]),
        "save_as_template": lambda: client.save_as_template(
            setting_id=arguments["setting_id"],
            name=arguments["name"],
        ),
        "delete_template": lambda: client.delete_template(arguments["setting_id"]),
    }

    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handlers[tool_name]()
