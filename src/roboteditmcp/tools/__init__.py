"""RobotEditMCP tools package."""

from roboteditmcp.tools.draft import register_draft_tools, handle_draft_tool
from roboteditmcp.tools.online import register_online_tools, handle_online_tool
from roboteditmcp.tools.template import register_template_tools, handle_template_tool
from roboteditmcp.tools.metadata import register_metadata_tools, handle_metadata_tool

__all__ = [
    "register_draft_tools",
    "handle_draft_tool",
    "register_online_tools",
    "handle_online_tool",
    "register_template_tools",
    "handle_template_tool",
    "register_metadata_tools",
    "handle_metadata_tool",
]
