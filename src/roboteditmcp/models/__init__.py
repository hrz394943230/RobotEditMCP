"""Data models for RobotEditMCP."""

from typing import Any

from pydantic import BaseModel, Field


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
    """Result of single draft creation in batch.

    Backend returns camelCase field names, so we use aliases.
    """

    index: int
    temp_id: int = Field(alias="tempId")
    success: bool
    setting_id: int | None = Field(None, alias="settingId")
    setting_dto: dict | None = Field(None, alias="settingDto")
    error_message: str | None = Field(None, alias="errorMessage")

    class Config:
        """Allow both camelCase and snake_case access."""

        populate_by_name = True


class BatchDraftResponse(BaseModel):
    """Response for batch create drafts.

    Backend returns camelCase field names, so we use aliases.
    """

    results: list[BatchDraftResult] = Field(alias="items")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    total_count: int = Field(alias="totalCount")

    class Config:
        """Allow both camelCase and snake_case access."""

        populate_by_name = True


class TemplateListResponse(BaseModel):
    """Response for list templates."""

    templates: list[dict]
    total: int


class ApplyTemplateResponse(BaseModel):
    """Response for apply template.

    Backend returns camelCase field names, so we use alias.
    """

    draft_id: int = Field(alias="draftId")

    class Config:
        """Allow both camelCase and snake_case access."""

        populate_by_name = True


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
