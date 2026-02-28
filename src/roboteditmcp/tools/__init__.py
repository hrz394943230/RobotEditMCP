"""RobotEditMCP tools package."""

from roboteditmcp.tools.draft import handle_draft_tool, register_draft_tools
from roboteditmcp.tools.online import handle_online_tool, register_online_tools
from roboteditmcp.tools.template import handle_template_tool, register_template_tools

__all__ = [
    "register_draft_tools",
    "handle_draft_tool",
    "register_online_tools",
    "handle_online_tool",
    "register_template_tools",
    "handle_template_tool",
]
