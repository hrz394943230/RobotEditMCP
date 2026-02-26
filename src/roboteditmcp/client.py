"""API client for RobotServer."""

import logging

import httpx
from pydantic import ValidationError

from roboteditmcp.config import config
from roboteditmcp.models import (
    ActionResult,
    ApplyTemplateResponse,
    BatchDraftResponse,
    FactoryListResponse,
    TemplateListResponse,
    TFSResponse,
)

logger = logging.getLogger(__name__)


class RobotAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")


class RobotClient:
    """HTTP client for Robot API."""

    def __init__(self):
        """Initialize the Robot API client."""
        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Configuration error: {error_msg}")

        self.base_url = config.get_base_url()
        self.admin_token = config.ROBOT_ADMIN_TOKEN
        self.timeout = config.API_TIMEOUT

        # Create HTTP client with connection limits
        self.client = httpx.Client(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=config.MAX_CONNECTIONS),
        )

        logger.info(f"RobotClient initialized with base_url: {self.base_url}")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with admin_key authentication."""
        return {
            "admin_key": self.admin_token,
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> dict:
        """
        Handle API response and extract data.

        Args:
            response: HTTP response object

        Returns:
            Response data

        Raises:
            RobotAPIError: If API returns an error
        """
        try:
            response_data = response.json()

            # Try to parse as TFSResponse
            try:
                tfs_response = TFSResponse(**response_data)
                if tfs_response.code != 200:
                    raise RobotAPIError(
                        tfs_response.message,
                        code=tfs_response.code,
                    )
                return tfs_response.data
            except ValidationError:
                # If not standard TFSResponse, return as-is
                if response.status_code >= 400:
                    raise RobotAPIError(
                        response_data.get("message", "Unknown error"),
                        code=response.status_code,
                    ) from None
                return response_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise RobotAPIError(f"HTTP error: {e}") from e

    # ========== Draft Configuration Management ==========

    def list_drafts(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
    ) -> list:
        """
        List draft configurations with optional filters.

        Args:
            scene: Filter by scene type (e.g., "ROBOT", "LLM", "CHAIN")
            factoryName: Filter by factory type (e.g., "RobotBrainDraftSetting")
            settingName: Filter by setting name

        Returns:
            List of DraftFactorySettingDto
        """
        params = {}
        if scene:
            params["scene"] = scene
        if factoryName:
            params["factoryName"] = factoryName
        if settingName:
            params["settingName"] = settingName

        response = self.client.get(
            f"{self.base_url}/api/v1/draft/factory-settings",
            headers=self._get_headers(),
            params=params,
        )
        return self._handle_response(response)

    def get_draft(self, setting_id: int) -> dict:
        """
        Get a single draft configuration by ID.

        Args:
            setting_id: Draft configuration ID

        Returns:
            DraftFactorySettingDto
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/draft/factory-settings/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def create_draft(
        self,
        scene: str,
        name: str,
        setting_name: str,
        config: dict,
    ) -> dict:
        """
        Create a new draft configuration.

        Args:
            scene: Scene type
            name: Factory name
            setting_name: Configuration name
            config: Configuration content (JSON object)

        Returns:
            DraftDetail
        """
        payload = {
            "scene": scene,
            "name": name,
            "setting_name": setting_name,
            "config": config,
        }

        response = self.client.post(
            f"{self.base_url}/api/v1/draft/factory-settings",
            headers=self._get_headers(),
            json=payload,
        )
        return self._handle_response(response)

    def update_draft(
        self,
        setting_id: int,
        setting_name: str,
        config: dict,
    ) -> dict:
        """
        Update a draft configuration (supports partial update).

        Args:
            setting_id: Draft configuration ID
            setting_name: Configuration name (required)
            config: Configuration content to update (only modified fields)

        Returns:
            DraftFactorySettingDto
        """
        payload = {
            "setting_name": setting_name,
            "config": config,
        }

        response = self.client.put(
            f"{self.base_url}/api/v1/draft/factory-settings/{setting_id}",
            headers=self._get_headers(),
            json=payload,
        )
        return self._handle_response(response)

    def delete_draft(self, setting_id: int) -> dict:
        """
        Delete a draft configuration.

        Args:
            setting_id: Draft configuration ID

        Returns:
            Deletion result
        """
        response = self.client.delete(
            f"{self.base_url}/api/v1/draft/factory-settings/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def batch_create_drafts(self, drafts: list) -> BatchDraftResponse:
        """
        Batch create draft configurations.

        Args:
            drafts: List of BatchDraftRequest with temp_id and draft config

        Returns:
            BatchDraftResponse with results and counts
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/draft/factory-settings/batch",
            headers=self._get_headers(),
            json={"drafts": drafts},
        )
        data = self._handle_response(response)
        return BatchDraftResponse(**data)

    def release_draft(self) -> dict:
        """
        Release all draft configurations to production environment.

        Note: This releases the entire draft environment, not a single draft.

        Returns:
            Dict with onlineRobotId
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/draft/release",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_factory_struct(self, scene: str, factoryName: str) -> dict:
        """
        Get factory structure information.

        Args:
            scene: Scene type
            factoryName: Factory name

        Returns:
            DraftFactoryStructDto with config_schema and tfs_actions
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/draft/factory-struct",
            headers=self._get_headers(),
            params={"scene": scene, "factoryName": factoryName},
        )
        return self._handle_response(response)

    def trigger_draft_action(
        self,
        setting_id: int,
        action: str,
        params: dict | None = None,
    ) -> ActionResult:
        """
        Trigger an action on a draft configuration.

        Args:
            setting_id: Draft configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult
        """
        payload = {"action": action}
        if params:
            payload["params"] = params

        response = self.client.post(
            f"{self.base_url}/api/v1/draft/factory-settings/{setting_id}/actions",
            headers=self._get_headers(),
            json=payload,
        )
        data = self._handle_response(response)
        return ActionResult(**data)

    # ========== Online Configuration Management ==========

    def list_online_configs(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
    ) -> list:
        """
        List production environment configurations.

        Args:
            scene: Filter by scene type
            factoryName: Filter by factory type
            settingName: Filter by setting name

        Returns:
            List of OnlineFactorySettingDto
        """
        params = {}
        if scene:
            params["scene"] = scene
        if factoryName:
            params["factoryName"] = factoryName
        if settingName:
            params["settingName"] = settingName

        response = self.client.get(
            f"{self.base_url}/api/v1/online/factory-settings",
            headers=self._get_headers(),
            params=params,
        )
        return self._handle_response(response)

    def get_online_config(self, setting_id: int) -> dict:
        """
        Get a single online configuration by ID.

        Args:
            setting_id: Online configuration ID

        Returns:
            OnlineFactorySettingDto
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/online/factory-settings/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_online_action_detail(self, setting_id: int, action: str) -> dict:
        """
        Get detailed information about a specific action.

        Args:
            setting_id: Online configuration ID
            action: Action name

        Returns:
            OnlineActionDetailDto
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/online/factory-settings/{setting_id}/actions/{action}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def trigger_online_action(
        self,
        setting_id: int,
        action: str,
        params: dict | None = None,
    ) -> ActionResult:
        """
        Trigger an action on an online configuration.

        Args:
            setting_id: Online configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult
        """
        payload = {"action": action}
        if params:
            payload["params"] = params

        response = self.client.post(
            f"{self.base_url}/api/v1/online/factory-settings/{setting_id}/actions",
            headers=self._get_headers(),
            json=payload,
        )
        data = self._handle_response(response)
        return ActionResult(**data)

    # ========== Template Management ==========

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

    # ========== Metadata Tools ==========

    def list_scenes(self) -> list[str]:
        """
        List all available scene types.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/metadata/scenes",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def list_factories(
        self,
        scene: str,
        type: str = "draft",
    ) -> FactoryListResponse:
        """
        List all factory types for a given scene.

        Args:
            scene: Scene type
            type: Configuration type - "draft", "online", or "template"

        Returns:
            FactoryListResponse with factory_names list
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/metadata/factories",
            headers=self._get_headers(),
            params={"scene": scene, "type": type},
        )
        data = self._handle_response(response)
        return FactoryListResponse(**data)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
