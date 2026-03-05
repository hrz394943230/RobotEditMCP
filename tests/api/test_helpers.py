"""Test environment helper for RobotEditMCP integration tests.

This module provides environment clearing and setup functionality for tests.
All operations are performed on real API endpoints.
"""

import logging
import time

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


class TestEnvironmentHelper:
    """Helper class for test environment management.

    Provides methods to clear and setup test environments.
    All operations affect the real API environment.
    """

    def __init__(self, client: RobotClient | None = None):
        """Initialize the helper with a RobotClient instance.

        Args:
            client: RobotClient instance. If None, creates a new one.
        """
        self.client = client if client is not None else RobotClient()

    def clear_drafts(self) -> None:
        """Clear all draft configurations from the environment.

        Deletes all draft configurations regardless of scene or type.
        Stops immediately on error and logs the failure.

        Raises:
            Exception: If deletion fails for any draft
        """
        drafts = self.client.draft.list_drafts()

        if not drafts:
            logger.info("No drafts to clear")
            return

        logger.info(f"Clearing {len(drafts)} draft(s)...")
        start_time = time.time()
        deleted_count = 0

        for draft in drafts:
            draft_id = draft.get("settingId") or draft.get("setting_id") or draft.get("id")
            if not draft_id:
                logger.warning(f"Draft missing ID: {draft}")
                continue

            try:
                self.client.draft.delete_draft(draft_id)
                deleted_count += 1
                logger.info(f"Deleted draft id={draft_id}")
            except Exception as e:
                error_msg = f"Failed to delete draft id={draft_id}: {e}"
                logger.error(error_msg)
                raise Exception(error_msg) from e

        elapsed = time.time() - start_time
        logger.info(f"Cleared {deleted_count} draft(s) in {elapsed:.2f}s")

    def clear_templates(self) -> None:
        """Clear all template configurations from the environment.

        Deletes all template configurations.
        Stops immediately on error and logs the failure.

        Raises:
            Exception: If deletion fails for any template
        """
        # List all templates (page 1, large page size)
        response = self.client.template.list_templates(page=1, pageSize=1000)

        if not response or not hasattr(response, "templates"):
            logger.info("No templates to clear")
            return

        templates = response.templates

        if not templates:
            logger.info("No templates to clear")
            return

        logger.info(f"Clearing {len(templates)} template(s)...")
        start_time = time.time()
        deleted_count = 0

        for template in templates:
            template_id = template.get("settingId") or template.get("setting_id") or template.get("id")
            if not template_id:
                logger.warning(f"Template missing ID: {template}")
                continue

            try:
                self.client.template.delete_template(template_id)
                deleted_count += 1
                logger.info(f"Deleted template id={template_id}")
            except Exception as e:
                error_msg = f"Failed to delete template id={template_id}: {e}"
                logger.error(error_msg)
                raise Exception(error_msg) from e

        elapsed = time.time() - start_time
        logger.info(f"Cleared {deleted_count} template(s) in {elapsed:.2f}s")

    def reset_online(self) -> dict:
        """Reset online environment to minimal ROBOT configuration.

        This method:
        1. Clears all drafts
        2. Creates a minimal ROBOT configuration
        3. Releases to online environment

        Returns:
            Dictionary with created resource IDs

        Raises:
            Exception: If any step fails
        """
        logger.info("Resetting online environment...")

        # Step 1: Clear all drafts
        self.clear_drafts()

        # Step 2: Create minimal ROBOT config
        from .base_test import BaseRobotTest

        # Create a temporary BaseRobotTest instance to use its methods
        base_test = BaseRobotTest()
        base_test.setup_method()
        base_test._client = self.client

        draft_ids = base_test.create_minimal_robot_config(name_suffix="online_reset")

        # Step 3: Release to online
        release_result = self.client.draft.release_draft()

        logger.info(f"Online environment reset complete. Robot ID: {release_result.get('onlineRobotId')}")

        return {
            "draft_ids": draft_ids,
            "release_result": release_result,
        }

    def create_draft(
        self,
        scene: str,
        name: str,
        setting_name: str,
        config: dict | None = None,
    ) -> int:
        """Create a single draft configuration.

        Args:
            scene: Scene type (e.g., "ROBOT", "LLM", "CHAIN")
            name: Factory name
            setting_name: Configuration name
            config: Configuration content (optional)

        Returns:
            Created draft ID

        Raises:
            Exception: If creation fails
        """
        if config is None:
            config = {}

        response = self.client.draft.create_draft(
            scene=scene,
            name=name,
            setting_name=setting_name,
            config=config,
        )

        draft_id = response.get("settingId") or response.get("setting_id") or response.get("id")

        if not draft_id:
            raise Exception(f"Failed to create draft: {response}")

        logger.info(f"Created draft: {setting_name} (id={draft_id})")
        return draft_id

    def create_minimal_robot_config(self, name_suffix: str = "robot") -> dict:
        """Create a minimal but complete ROBOT configuration for testing.

        Creates all required dependencies for a ROBOT configuration.

        Args:
            name_suffix: Suffix for resource naming

        Returns:
            Dictionary with all created draft IDs

        Note:
            This uses the BaseRobotTest method for consistency.
        """
        from .base_test import BaseRobotTest

        base_test = BaseRobotTest()
        base_test.setup_method()
        base_test._client = self.client

        return base_test.create_minimal_robot_config(name_suffix=name_suffix)

    def load_template(self, template_name: str, **kwargs) -> dict:
        """Load and render a configuration template.

        Args:
            template_name: Name of the template file (without .json extension)
            **kwargs: Variables for template substitution

        Returns:
            Rendered template dictionary

        Raises:
            FileNotFoundError: If template file not found
            Exception: If template parsing fails
        """
        import json
        import os

        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        template_path = os.path.join(template_dir, f"{template_name}.json")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            template_content = f.read()

        # Simple variable substitution: {{var}} -> value
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))

        try:
            return json.loads(template_content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse template {template_name}: {e}") from e

    def assert_environment_empty(self) -> None:
        """Assert that the environment has no drafts or templates.

        Raises:
            AssertionError: If environment is not empty
        """
        drafts = self.client.draft.list_drafts()
        templates_response = self.client.template.list_templates(page=1, pageSize=1000)
        templates = templates_response.templates if templates_response else []

        errors = []
        if drafts:
            errors.append(f"Environment has {len(drafts)} draft(s)")
        if templates:
            errors.append(f"Environment has {len(templates)} template(s)")

        if errors:
            raise AssertionError("Environment not empty: " + "; ".join(errors))

        logger.info("Environment is empty")
