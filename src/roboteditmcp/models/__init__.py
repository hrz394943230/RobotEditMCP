"""Data models for RobotEditMCP."""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel


class TFSResponse(BaseModel):
    """Standard TFS API response format."""

    code: int
    message: str
    data: Any = None


class SettingRef(BaseModel):
    """Reference to another setting."""

    setting_id: int
    category: str  # "Draft" | "Online" | "Template"


class ActionResult(BaseModel):
    """Result of triggering an action."""

    success: bool
    result: Any | None = None
    error_message: str | None = None


class BatchDraftRequest(BaseModel):
    """Single draft in batch create request."""

    temp_id: int  # Negative ID for internal reference
    draft: dict  # Draft configuration


class BatchDraftResult(BaseModel):
    """Result of single draft creation in batch."""

    index: int
    temp_id: int
    success: bool
    setting_id: int | None = None
    setting_dto: dict | None = None
    error_message: str | None = None


class BatchDraftResponse(BaseModel):
    """Response for batch create drafts."""

    results: list[BatchDraftResult]
    success_count: int
    failure_count: int
    total_count: int


class TemplateListResponse(BaseModel):
    """Response for list templates."""

    templates: list[dict]
    total: int


class ApplyTemplateResponse(BaseModel):
    """Response for apply template."""

    draft_id: int


class FactoryListResponse(BaseModel):
    """Response for list factories."""

    factory_names: list[str]


# Placeholder DTOs - will be populated dynamically from API responses
DraftFactorySettingDto = dict
OnlineFactorySettingDto = dict
TemplateFactorySettingDto = dict
DraftFactoryStructDto = dict
OnlineActionDetailDto = dict
DraftDetail = dict
