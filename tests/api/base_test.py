"""Base test class for RobotEditMCP integration tests.

Provides automatic resource tracking and cleanup for test isolation.
"""

import logging
from typing import Dict, List, Optional

from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)


class BaseRobotTest:
    """Base class for integration tests with automatic resource tracking and cleanup.

    Features:
    - Automatic resource tracking (drafts, templates, online configs)
    - LIFO cleanup order (templates -> drafts -> online)
    - Unique resource naming for parallel test support
    - Cleanup failure reporting without blocking tests
    """

    # Resource types
    RESOURCE_DRAFT = "draft"
    RESOURCE_TEMPLATE = "template"
    RESOURCE_ONLINE = "online"

    # Test resource naming prefix
    RESOURCE_PREFIX = "mcp_test_"

    def setup_method(self):
        """Setup before each test method.

        Initializes client reference and resource tracking containers.
        """
        self._client: Optional[RobotClient] = None
        self._resources: Dict[str, List[int]] = {
            self.RESOURCE_DRAFT: [],
            self.RESOURCE_TEMPLATE: [],
            self.RESOURCE_ONLINE: [],
        }
        self._resource_counter: int = 0

    def teardown_method(self):
        """Cleanup after each test method.

        Cleans up tracked resources in LIFO order.
        Logs warnings for cleanup failures but doesn't raise exceptions.
        """
        errors = []

        # LIFO order: templates -> drafts -> online (reverse dependency order)
        for resource_type in [self.RESOURCE_TEMPLATE, self.RESOURCE_DRAFT, self.RESOURCE_ONLINE]:
            resource_ids = self._resources.get(resource_type, [])

            # LIFO: delete from end to start
            for resource_id in reversed(resource_ids):
                try:
                    self._delete_resource(resource_type, resource_id)
                    logger.info(f"Cleanup successful: {resource_type} id={resource_id}")
                except Exception as e:
                    error_msg = f"Cleanup failed: {resource_type} id={resource_id}, error={e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

        # Report cleanup errors
        if errors:
            logger.warning(f"Cleanup completed with {len(errors)} error(s):")
            for error in errors:
                logger.warning(f"  - {error}")

            # Generate manual cleanup suggestions
            self._generate_cleanup_report(errors)

    def _delete_resource(self, resource_type: str, resource_id: int):
        """Delete a resource by type and ID.

        Args:
            resource_type: Type of resource (draft/template/online)
            resource_id: ID of the resource to delete

        Raises:
            Exception: If deletion fails
        """
        if resource_type == self.RESOURCE_DRAFT:
            self.client.draft.delete_draft(resource_id)
        elif resource_type == self.RESOURCE_TEMPLATE:
            self.client.template.delete_template(resource_id)
        elif resource_type == self.RESOURCE_ONLINE:
            # Online configs usually don't support direct deletion
            logger.warning(f"Online resource doesn't support deletion: id={resource_id}")

    def _generate_cleanup_report(self, errors: List[str]):
        """Generate a cleanup failure report with manual cleanup commands.

        Args:
            errors: List of error messages
        """
        logger.warning("=" * 60)
        logger.warning("Cleanup Failure Report - Manual Cleanup Suggestions:")
        logger.warning("=" * 60)

        for resource_type, ids in self._resources.items():
            if ids:
                ids_str = ", ".join(map(str, ids))
                logger.warning(f"  {resource_type}: [{ids_str}]")

        logger.warning("=" * 60)

    @property
    def client(self) -> RobotClient:
        """Get RobotClient instance (lazy initialization).

        Returns:
            RobotClient instance
        """
        if self._client is None:
            self._client = RobotClient()
        return self._client

    def _generate_resource_name(self, suffix: str = "") -> str:
        """Generate a unique test resource name.

        Format: mcp_test_<ClassName>_<Counter>_<Suffix>

        Example: mcp_test_TestDraftAPI_001_create

        Args:
            suffix: Optional suffix for the resource name

        Returns:
            Unique resource name
        """
        class_name = self.__class__.__name__
        self._resource_counter += 1
        counter_str = str(self._resource_counter).zfill(3)

        parts = [self.RESOURCE_PREFIX, class_name, counter_str]
        if suffix:
            parts.append(suffix)

        return "_".join(parts)

    def _track_resource(self, resource_type: str, resource_id: int):
        """Track a created resource for later cleanup.

        Args:
            resource_type: Type of resource (draft/template/online)
            resource_id: ID of the created resource
        """
        if resource_type in self._resources:
            self._resources[resource_type].append(resource_id)
            logger.info(f"Tracking resource: {resource_type} id={resource_id}")

    def _verify_resource_created(self, response, expected_key: str = "settingId") -> int:
        """Verify resource creation and return the resource ID.

        Performs basic existence verification:
        - Checks response is not None
        - Checks response contains expected ID field
        - ID value is not empty

        Args:
            response: API response (dict or Pydantic model)
            expected_key: Expected key name for the resource ID

        Returns:
            The resource ID

        Raises:
            AssertionError: If verification fails
        """
        assert response is not None, "Create response should not be None"

        # Convert Pydantic model to dict if needed
        if isinstance(response, dict):
            response_dict = response
        elif hasattr(response, 'model_dump'):
            response_dict = response.model_dump()
        elif hasattr(response, 'dict'):
            response_dict = response.dict()
        else:
            raise AssertionError(f"Unsupported response type: {type(response)}")

        # Try multiple possible ID field names
        possible_keys = [expected_key, expected_key.lower(), "id"]
        resource_id = None

        for key in possible_keys:
            if key in response_dict:
                resource_id = response_dict[key]
                break

        assert resource_id is not None, f"Response should contain resource ID (checked fields: {possible_keys})"
        assert resource_id, f"Resource ID should not be empty: {resource_id}"

        logger.info(f"Resource creation verified: id={resource_id}")
        return resource_id

    # ===== Creation Methods =====

    def create_draft(
        self,
        scene: str,
        name: str,
        setting_name: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> int:
        """Create a draft configuration and automatically track it for cleanup.

        Args:
            scene: Scene name (e.g., "ROBOT", "LLM", "CHAIN")
            name: Factory name
            setting_name: Configuration name (optional, auto-generated if not provided)
            config: Configuration content (optional)

        Returns:
            Created draft ID
        """
        if setting_name is None:
            setting_name = self._generate_resource_name("draft")

        if config is None:
            config = {}

        response = self.client.draft.create_draft(
            scene=scene,
            name=name,
            setting_name=setting_name,
            config=config,
        )

        draft_id = self._verify_resource_created(response)
        self._track_resource(self.RESOURCE_DRAFT, draft_id)
        return draft_id

    def create_template(self, draft_id: int, name: Optional[str] = None) -> int:
        """Create a template from a draft and automatically track it for cleanup.

        Args:
            draft_id: Source draft ID
            name: Template name (optional, auto-generated if not provided)

        Returns:
            Created template ID
        """
        if name is None:
            name = self._generate_resource_name("template")

        response = self.client.draft.save_as_template(
            draft_id=draft_id,
            name=name,
        )

        template_id = self._verify_resource_created(response, "templateId")
        self._track_resource(self.RESOURCE_TEMPLATE, template_id)
        return template_id

    def create_draft_from_template(self, template_id: int) -> int:
        """Create a draft from a template and automatically track it for cleanup.

        Args:
            template_id: Template ID

        Returns:
            Created draft ID
        """
        response = self.client.template.apply_template(
            templateSettingId=template_id
        )

        # ApplyTemplateResponse has 'draft_id' field (snake_case in model_dump)
        draft_id = self._verify_resource_created(response, "draft_id")
        self._track_resource(self.RESOURCE_DRAFT, draft_id)
        return draft_id

    def batch_create_drafts(self, drafts: List[dict]) -> List[int]:
        """Batch create drafts and automatically track them for cleanup.

        Args:
            drafts: List of draft configurations

        Returns:
            List of created draft IDs (only successful creations)

        Raises:
            AssertionError: If no drafts were successfully created
        """
        response = self.client.draft.batch_create_drafts(drafts)

        # Extract all created IDs and track them
        draft_ids = []
        results = response.results if hasattr(response, 'results') else []

        for result in results:
            # Convert to dict if it's a Pydantic model
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif hasattr(result, 'dict'):
                result_dict = result.dict()
            elif isinstance(result, dict):
                result_dict = result
            else:
                logger.warning(f"Skipping result with unsupported type: {type(result)}")
                continue

            # Check if this draft was successfully created
            # BatchDraftResult has 'success' field and 'settingId' (or 'setting_id')
            if not result_dict.get('success', False):
                logger.warning(f"Draft creation failed: {result_dict.get('error_message', 'Unknown error')}")
                continue

            # Get the setting ID from various possible fields
            draft_id = (
                result_dict.get('settingId') or
                result_dict.get('setting_id') or
                result_dict.get('id')
            )

            if draft_id:
                self._track_resource(self.RESOURCE_DRAFT, draft_id)
                draft_ids.append(draft_id)
                logger.info(f"Batch draft created successfully: id={draft_id}")

        assert len(draft_ids) > 0, "At least one draft should be created successfully"

        return draft_ids

    # ===== Robot Configuration Setup =====

    def create_test_robot_config(self, name_suffix: str = "robot") -> int:
        """Create a simple ROBOT configuration for testing.

        Creates a minimal ROBOT configuration without dependencies.
        The brain and drive fields can be None for testing purposes.

        Args:
            name_suffix: Suffix for resource naming

        Returns:
            The ROBOT draft ID

        Note:
            This creates a simplified ROBOT config without brain/drive
            dependencies, suitable for testing online config endpoints.
        """
        # Create a simple ROBOT configuration (brain and drive can be None)
        robot_id = self.create_draft(
            scene="ROBOT",
            name="RobotDraftSetting",
            setting_name=self._generate_resource_name(f"{name_suffix}_robot"),
            config={
                "nick_name": f"TestRobot_{name_suffix}",
                "brain": None,  # Optional for testing
                "drive": None,  # Optional for testing
                "lock_timeout": 1800,
                "wait_processing_timeout": 20
            }
        )

        logger.info(f"Created simple ROBOT config: robot_id={robot_id}")
        return robot_id

    # ===== Cleanup Methods =====

    def cleanup_all(self):
        """Manually trigger cleanup of all tracked resources.

        Normally you don't need to call this method as teardown will auto-cleanup.
        Only use in special cases (e.g., need to reset state mid-test).
        """
        self.teardown_method()
