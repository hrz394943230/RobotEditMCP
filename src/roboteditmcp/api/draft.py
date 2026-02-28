"""Draft configuration API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ActionResult, BatchDraftResponse

logger = logging.getLogger(__name__)


class DraftAPI(BaseAPI):
    """API client for draft configuration management.

    Handles all draft-related operations (12 endpoints):
    - Scene and factory discovery
    - CRUD operations on draft configurations
    - Batch creation with temp_id references
    - Releasing drafts to production
    - Saving drafts as templates
    - Factory structure queries
    - Action triggers
    """

    # ========================================
    # Discovery Endpoints (from metadata.py)
    # ========================================

    def get_draft_scenes(self) -> list[str]:
        """
        Get all available scene types for draft configurations.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        response = self.client.get(
            f"{self.base_url}/factory/drafts/scenes",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_draft_factories(self, scene: str) -> dict:
        """
        Get all factory types for a given scene in draft mode.

        Args:
            scene: Scene type (e.g., "ROBOT", "LLM", "CHAIN")

        Returns:
            Dict with factory_names list
        """
        response = self.client.get(
            f"{self.base_url}/factory/drafts/{scene}/factories",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Factory Structure
    # ========================================

    def get_draft_factory_struct(self, factoryName: str) -> dict:
        """
        Get draft factory structure definition.

        Note: Only requires factoryName parameter, NOT scene!

        Args:
            factoryName: Factory name (e.g., "RobotBrainDraftSetting")

        Returns:
            DraftFactoryStructDto with config_schema and tfs_actions
        """
        response = self.client.get(
            f"{self.base_url}/factory/drafts/struct/{factoryName}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # CRUD Operations
    # ========================================

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
            f"{self.base_url}/factory/drafts/query",
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
            f"{self.base_url}/factory/drafts/{setting_id}",
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
            DraftFactorySettingDto
        """
        payload = {
            "scene": scene,
            "name": name,
            "settingName": setting_name,
            "config": config,
        }

        response = self.client.post(
            f"{self.base_url}/factory/drafts",
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
            "settingName": setting_name,
            "config": config,
        }

        response = self.client.put(
            f"{self.base_url}/factory/drafts/{setting_id}",
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
            f"{self.base_url}/factory/drafts/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Batch Operations
    # ========================================

    def batch_create_drafts(self, drafts: list) -> BatchDraftResponse:
        """
        Batch create draft configurations.

        Args:
            drafts: List of BatchDraftRequest with temp_id and draft config

        Returns:
            BatchDraftResponse with results and counts
        """
        response = self.client.post(
            f"{self.base_url}/factory/drafts/batch",
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
            f"{self.base_url}/factory/drafts/release",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Template Operations
    # ========================================

    def save_as_template(
        self,
        draft_id: int,
        name: str,
        scene: str | None = None,
        setting_name: str | None = None,
        config: dict | None = None,
    ) -> dict:
        """
        Save a draft configuration as a template.

        Uses DraftFactorySettingPostDto structure for request body.

        Args:
            draft_id: Draft configuration ID
            name: Factory name (required)
            scene: Scene type (optional)
            setting_name: Template name (optional)
            config: Configuration data (optional)

        Returns:
            Dict with templateId
        """
        payload = {"name": name}
        if scene is not None:
            payload["scene"] = scene
        if setting_name is not None:
            payload["settingName"] = setting_name
        if config is not None:
            payload["config"] = config

        response = self.client.post(
            f"{self.base_url}/factory/drafts/{draft_id}/savetemplate",
            headers=self._get_headers(),
            json=payload,
        )
        return self._handle_response(response)

    # ========================================
    # Action Triggers
    # ========================================

    def trigger_draft_action(
        self,
        setting_id: int,
        action: str,
        params: dict | None = None,
    ) -> ActionResult:
        """
        Trigger an action on a draft configuration.

        Note: Uses PUT method (not POST)

        Args:
            setting_id: Draft configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult
        """
        # Important: Always pass a dict, even if empty
        body = params if params is not None else {}

        response = self.client.put(
            f"{self.base_url}/factory/drafts/{setting_id}/action/{action}",
            headers=self._get_headers(),
            json=body,
        )
        data = self._handle_response(response)
        return ActionResult(**data)
