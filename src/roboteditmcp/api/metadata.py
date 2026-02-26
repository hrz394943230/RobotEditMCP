"""Metadata discovery API for RobotServer."""

import logging

from roboteditmcp.api.base import BaseAPI
from roboteditmcp.models import FactoryListResponse

logger = logging.getLogger(__name__)


class MetadataAPI(BaseAPI):
    """API client for metadata discovery.

    Handles metadata-related operations:
    - Listing available scene types
    - Listing factory types for a given scene
    """

    def list_scenes(self) -> list[str]:
        """
        List all available scene types.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        response = self.client.get(
            f"{self.base_url}/factory/draft-scenes",
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
