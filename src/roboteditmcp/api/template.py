"""Template management API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ApplyTemplateResponse, TemplateListResponse

logger = logging.getLogger(__name__)


class TemplateAPI(BaseAPI):
    """API client for template management.

    Handles all template-related operations (7 endpoints):
    - Scene and factory discovery
    - Listing and querying templates
    - Applying templates to create new drafts
    - Deleting templates
    """

    # ========================================
    # Discovery Endpoints
    # ========================================

    def get_template_scenes(self) -> list[str]:
        """
        Get all available scene types for template configurations.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        response = self.client.get(
            f"{self.base_url}/factory/templates/scenes",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_template_factories(self, scene: str) -> dict:
        """
        Get all factory types for a given scene in template mode.

        Args:
            scene: Scene type (e.g., "ROBOT", "LLM", "CHAIN")

        Returns:
            Dict with factory_names list
        """
        response = self.client.get(
            f"{self.base_url}/factory/templates/{scene}/factories",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_template_factory_struct(self, scene: str, factoryName: str) -> dict:
        """
        Get template factory structure definition.

        Note: Requires both scene and factoryName parameters!

        Args:
            scene: Scene type (e.g., "ROBOT")
            factoryName: Factory name (e.g., "RobotBrainTemplateSetting")

        Returns:
            TemplateFactoryStructDto with config_schema (no tfs_actions)
        """
        response = self.client.get(
            f"{self.base_url}/factory/templates/struct/{scene}/{factoryName}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Template Queries
    # ========================================

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
            f"{self.base_url}/factory/template/settings",
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
            f"{self.base_url}/factory/templates/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Template Operations
    # ========================================

    def apply_template(self, templateSettingId: int) -> ApplyTemplateResponse:
        """
        Create a new draft configuration from a template.

        Args:
            templateSettingId: Template ID

        Returns:
            ApplyTemplateResponse with draft_id
        """
        response = self.client.post(
            f"{self.base_url}/factory/templates/apply",
            headers=self._get_headers(),
            params={"templateSettingId": templateSettingId},
        )
        data = self._handle_response(response)
        return ApplyTemplateResponse(**data)

    def delete_template(self, setting_id: int) -> dict:
        """
        Delete a template.

        Args:
            setting_id: Template ID

        Returns:
            Deletion result
        """
        response = self.client.delete(
            f"{self.base_url}/factory/templates/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)
