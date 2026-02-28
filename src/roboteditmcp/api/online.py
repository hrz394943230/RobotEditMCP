"""Online configuration API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ActionResult

logger = logging.getLogger(__name__)


class OnlineAPI(BaseAPI):
    """API client for online (production) configuration management.

    Handles all online-related operations (7 endpoints):
    - Scene and factory discovery
    - Querying production configurations
    - Getting action details
    - Triggering actions on production configurations
    """

    # ========================================
    # Discovery Endpoints
    # ========================================

    def get_online_scenes(self) -> list[str]:
        """
        Get all available scene types for online configurations.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        response = self.client.get(
            f"{self.base_url}/factory/online/scenes",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_online_factories(self, scene: str) -> dict:
        """
        Get all factory types for a given scene in online mode.

        Args:
            scene: Scene type (e.g., "ROBOT", "LLM", "CHAIN")

        Returns:
            Dict with factory_names list
        """
        response = self.client.get(
            f"{self.base_url}/factory/online/{scene}/factories",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_online_factory_struct(self, scene: str, factoryName: str) -> dict:
        """
        Get online factory structure definition.

        Note: Requires both scene and factoryName parameters!

        Args:
            scene: Scene type (e.g., "ROBOT")
            factoryName: Factory name (e.g., "RobotBrainOnlineSetting")

        Returns:
            OnlineFactoryStructDto with config_schema and tfs_actions
        """
        response = self.client.get(
            f"{self.base_url}/factory/online/struct/{scene}/{factoryName}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Configuration Queries
    # ========================================

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
            f"{self.base_url}/factory/online/query",
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
            f"{self.base_url}/factory/online/{setting_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # ========================================
    # Action Operations
    # ========================================

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
            f"{self.base_url}/factory/online/{setting_id}/action/{action}/detail",
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
        # Backend uses PUT method with params as body
        # Important: Always pass a dict, even if empty (not None)
        payload = params if params is not None else {}

        response = self.client.put(
            f"{self.base_url}/factory/online/{setting_id}/action/{action}",
            headers=self._get_headers(),
            json=payload,
        )
        data = self._handle_response(response)
        return ActionResult(**data)
