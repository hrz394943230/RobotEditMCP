"""Template management API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ApplyTemplateResponse, TemplateListResponse

logger = logging.getLogger(__name__)


class TemplateAPI(BaseAPI):
    """API client for template management.

    Handles all template-related operations:
    - Listing and querying templates
    - Applying templates to create new drafts
    - Saving drafts as templates
    - Deleting templates
    """

    def list_templates(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
        templateName: str | None = None,
        page: int = 1,
        pageSize: int = 10,
    ) -> TemplateListResponse:
        """
        List available templates.

        Args:
            scene: Filter by scene type
            factoryName: Filter by factory type
            settingName: Filter by setting name
            templateName: Filter by template name
            page: Page number (default 1)
            pageSize: Items per page (default 10)

        Returns:
            TemplateListResponse with templates and total count
        """
        params = {"page": page, "pageSize": pageSize}
        if scene:
            params["scene"] = scene
        if factoryName:
            params["factoryName"] = factoryName
        if settingName:
            params["settingName"] = settingName
        if templateName:
            params["templateName"] = templateName

        response = self.client.get(
            f"{self.base_url}/api/v1/template/factory-settings",
            headers=self._get_headers(),
            params=params,
        )
        data = self._handle_response(response)
        return TemplateListResponse(**data)

    def get_template(self, setting_id: int) -> dict:
        """
        Get a single template by ID.

        Args:
            setting_id: Template ID

        Returns:
            TemplateFactorySettingDto
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/template/factory-settings/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def apply_template(self, templateSettingId: int) -> ApplyTemplateResponse:
        """
        Create a new draft configuration from a template.

        Args:
            templateSettingId: Template ID

        Returns:
            ApplyTemplateResponse with draft_id
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/template/factory-settings/{templateSettingId}/apply",
            headers=self._get_headers(),
        )
        data = self._handle_response(response)
        return ApplyTemplateResponse(**data)

    def save_as_template(self, setting_id: int, name: str) -> dict:
        """
        Save a draft configuration as a template.

        Args:
            setting_id: Draft configuration ID
            name: Template name

        Returns:
            TemplateFactorySettingDto
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/draft/factory-settings/{setting_id}/save-as-template",
            headers=self._get_headers(),
            json={"name": name},
        )
        return self._handle_response(response)

    def delete_template(self, setting_id: int) -> dict:
        """
        Delete a template.

        Args:
            setting_id: Template ID

        Returns:
            Deletion result
        """
        response = self.client.delete(
            f"{self.base_url}/api/v1/template/factory-settings/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)
