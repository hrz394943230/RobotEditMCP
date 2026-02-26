"""Draft configuration API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ActionResult, BatchDraftResponse

logger = logging.getLogger(__name__)


class DraftAPI(BaseAPI):
    """API client for draft configuration management.

    Handles all draft-related operations:
    - CRUD operations on draft configurations
    - Batch creation with temp_id references
    - Releasing drafts to production
    - Factory structure queries
    - Action triggers
    """

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
