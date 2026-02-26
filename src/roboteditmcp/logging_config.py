"""Logging configuration for RobotEditMCP."""

import logging
import sys

from roboteditmcp.config import config


def setup_logging() -> None:
    """Configure logging based on ROBOT_LOG_LEVEL environment variable."""
    log_level = getattr(logging, config.ROBOT_LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

    # Suppress overly verbose loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
