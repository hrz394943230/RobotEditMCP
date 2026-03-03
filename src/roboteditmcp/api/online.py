"""Online configuration API for RobotServer."""

import logging

from pydantic import ValidationError

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
            f"{self.base_url}/factory/online/scene/{scene}/factories",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def get_online_factory_struct(self, scene: str, factoryName: str) -> dict:
        """
        Get online factory structure definition.

        Note: Requires both scene and factoryName parameters!

        Args:
            scene: Scene type (e.g., "ROBOT", "DOC_STORE")
            factoryName: Factory name (e.g., "RobotBrainOnlineSetting", "PostgresDocStoreOnline")

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

    def get_online_action_detail(self, setting_id: int, action: str, category: str | None = None) -> dict:
        """
        Get detailed information about a specific action.

        Args:
            setting_id: Online configuration ID
            action: Action name
            category: Optional category parameter ("pageable" or "graphical")

        Returns:
            OnlineActionDetailDto
        """
        # Try POST method with category in body (if category provided)
        if category:
            response = self.client.post(
                f"{self.base_url}/factory/online/{setting_id}/action/{action}/detail",
                headers=self._get_headers(),
                json={"category": category}
            )
        else:
            # Try GET method without category
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
    ):
        """
        Trigger an action on an online configuration.

        Note: Response can be a dict (ActionResult) or a list (raw data)

        Args:
            setting_id: Online configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult or raw action result (can be dict, list, or other types)
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

        # Try to parse as ActionResult if it's a dict
        if isinstance(data, dict):
            try:
                return ActionResult(**data)
            except (TypeError, ValidationError):
                # If it doesn't match ActionResult structure, return as-is
                return data
        # Return as-is if it's not a dict (e.g., list, string, etc.)
        return data
