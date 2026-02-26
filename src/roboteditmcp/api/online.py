"""Online configuration API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import ActionResult

logger = logging.getLogger(__name__)


class OnlineAPI(BaseAPI):
    """API client for online (production) configuration management.

    Handles all online-related operations:
    - Querying production configurations
    - Getting action details
    - Triggering actions on production configurations
    """

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
