"""API modules for RobotServer.

This package contains specialized API client classes for different
functional areas: draft, online, and template.
"""

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.api.draft import DraftAPI
from roboteditmcp.api.online import OnlineAPI
from roboteditmcp.api.template import TemplateAPI

__all__ = [
    "BaseAPI",
    "DraftAPI",
    "OnlineAPI",
    "TemplateAPI",
]
