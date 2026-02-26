"""Base API client for RobotServer."""

import logging

import httpx
from pydantic import ValidationError

from roboteditmcp.config import config
from roboteditmcp.models import TFSResponse

logger = logging.getLogger(__name__)


class RobotAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")


class BaseAPI:
    """Base HTTP client for Robot API.

    Provides common functionality for all API modules:
    - HTTP client with connection pooling
    - Authentication and K8s routing via cookies
    - Standardized response handling
    """

    def __init__(self):
        """Initialize the base API client."""
        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Configuration error: {error_msg}")

        self.base_url = config.get_base_url()
        self.admin_token = config.ROBOT_ADMIN_TOKEN
        self.timeout = config.API_TIMEOUT

        # Prepare cookies for authentication and K8s routing
        cookies = {
            "adminToken": self.admin_token,
            "tfNamespace": config.TF_NAMESPACE,
            "tfRobotId": config.TF_ROBOT_ID,
        }

        # Create HTTP client with connection limits and cookies
        self.client = httpx.Client(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=config.MAX_CONNECTIONS),
            cookies=cookies,
        )

        logger.info(f"BaseAPI initialized with base_url: {self.base_url}")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
        }

    def _get_cookies(self) -> dict[str, str]:
        """Get request cookies for authentication and K8s routing."""
        return {
            "adminToken": self.admin_token,
            "tfNamespace": config.TF_NAMESPACE,
            "tfRobotId": config.TF_ROBOT_ID,
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

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
