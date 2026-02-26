"""Configuration management for RobotEditMCP."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for RobotEditMCP."""

    # Robot API configurations
    ROBOT_ADMIN_TOKEN: str = os.getenv("ROBOT_ADMIN_TOKEN", "")
    ROBOT_BASE_URL: str = os.getenv("ROBOT_BASE_URL", "")

    # Additional required headers for Robot API
    TF_NAMESPACE: str = os.getenv("TF_NAMESPACE", "")
    TF_ROBOT_ID: str = os.getenv("TF_ROBOT_ID", "")

    # Logging configuration
    ROBOT_LOG_LEVEL: str = os.getenv("ROBOT_LOG_LEVEL", "INFO")

    # API client settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "10"))

    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Validate required configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.ROBOT_ADMIN_TOKEN:
            return False, "ROBOT_ADMIN_TOKEN environment variable is required"

        if not cls.ROBOT_BASE_URL:
            return False, "ROBOT_BASE_URL environment variable is required"

        if not cls.TF_NAMESPACE:
            return False, "TF_NAMESPACE environment variable is required"

        if not cls.TF_ROBOT_ID:
            return False, "TF_ROBOT_ID environment variable is required"

        # Validate BASE_URL format
        base_url = cls.ROBOT_BASE_URL.rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            return False, "ROBOT_BASE_URL must start with http:// or https://"

        return True, ""

    @classmethod
    def get_base_url(cls) -> str:
        """Get normalized base URL."""
        return cls.ROBOT_BASE_URL.rstrip("/")


# Global configuration instance
config = Config()
