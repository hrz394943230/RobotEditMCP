"""Base test class for RobotEditMCP integration tests.

Provides automatic resource tracking and cleanup for test isolation.
"""

import logging

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
        self._client: RobotClient | None = None
        self._resources: dict[str, list[int]] = {
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

    def _generate_cleanup_report(self, errors: list[str]):
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
        setting_name: str | None = None,
        config: dict | None = None,
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

    def create_template(self, draft_id: int, name: str | None = None) -> int:
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

    def batch_create_drafts(self, drafts: list[dict]) -> list[int]:
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

    def create_minimal_robot_config(self, name_suffix: str = "robot") -> dict:
        """Create a minimal but complete ROBOT configuration for testing.

        Creates all required dependencies for a ROBOT configuration:
        - DOC_STORE (drive)
        - CONVERSATION_MANAGER
        - MEMORY (uses doc_store and conversation_manager)
        - LLM provider
        - CHAIN (uses llm) - optional, falls back to LLM directly if not available
        - BRAIN (uses chain and memory)
        - ROBOT (uses brain and drive)

        Args:
            name_suffix: Suffix for resource naming

        Returns:
            Dictionary with all created draft IDs

        Note:
            This creates a complete ROBOT config that can be released to production.
            All drafts are automatically tracked for cleanup.
            Some components may not be available in all environments (e.g., CHAIN).
        """
        draft_ids = {}

        # 1. Create DOC_STORE (drive)
        doc_store_id = self.create_draft(
            scene="DOC_STORE",
            name="PostgresDocStoreDraft",
            setting_name=self._generate_resource_name(f"{name_suffix}_doc_store"),
            config={
                "name": f"TestDocStore_{name_suffix}",
                "description": "Test document store for robot config"
            }
        )
        draft_ids["doc_store"] = doc_store_id
        logger.info(f"Created DOC_STORE: {doc_store_id}")

        # 2. Create CONVERSATION_MANAGER (optional, may not be available)
        conversation_manager_id = None
        try:
            conversation_manager_id = self.create_draft(
                scene="CONVERSATION_MANAGER",
                name="PGInjectedConversationManagerDraftSetting",
                setting_name=self._generate_resource_name(f"{name_suffix}_conv_mgr"),
                config={"platform_id": 1}
            )
            draft_ids["conversation_manager"] = conversation_manager_id
            logger.info(f"Created CONVERSATION_MANAGER: {conversation_manager_id}")
        except Exception as e:
            logger.warning(f"CONVERSATION_MANAGER not available: {e}")

        # 3. Create MEMORY (uses doc_store and conversation_manager if available)
        memory_config = {
            "docs": {
                "setting_id": doc_store_id,
                "category": "Draft"
            },
            "conversation_manager": {
                "setting_id": conversation_manager_id,
                "category": "Draft"
            } if conversation_manager_id else None,
            "memos": None,
            "knowledge": None,
            "recall_strict": False,
            "top_k": 20,
            "kg_format": "tfrobot",
            "enable_kg_query_expansion": True
        }

        memory_id = None
        try:
            memory_id = self.create_draft(
                scene="MEMORY",
                name="AIMemoryDraftSetting",
                setting_name=self._generate_resource_name(f"{name_suffix}_memory"),
                config=memory_config
            )
            draft_ids["memory"] = memory_id
            logger.info(f"Created MEMORY: {memory_id}")
        except Exception as e:
            logger.warning(f"MEMORY not available: {e}")

        # 4. Create LLM provider
        llm_id = self.create_draft(
            scene="LLM",
            name="GPT草稿",
            setting_name=self._generate_resource_name(f"{name_suffix}_llm"),
            config={
                "input_price": 0,
                "output_price": 0,
                "name": f"test-gpt-model-{name_suffix}",
                "context_window": 4096,
                "system_msg_prompt": [],
                "before_input_msg_prompt": [],
                "after_input_msg_prompt": [],
                "after_intermediate_msg_prompt": [],
                "tool_filter": None,
                "frequency_penalty": 0,
                "max_tokens": 1024,
                "top_p": 1,
                "n": 1,
                "presence_penalty": 0,
                "temperature": 0.7,
                "openai_api_key": "test-key-not-used",
                "proxy_host": None,
                "proxy_port": None,
                "response_format": {"type": "text"},
                "stream": False
            }
        )
        draft_ids["llm"] = llm_id
        logger.info(f"Created LLM: {llm_id}")

        # 5. Create CHAIN (optional, may not be available)
        chain_id = None
        try:
            chain_id = self.create_draft(
                scene="CHAIN",
                name="ChainDraft",
                setting_name=self._generate_resource_name(f"{name_suffix}_chain"),
                config={
                    "llm": {
                        "setting_id": llm_id,
                        "category": "Draft"
                    },
                    "max_iterations": 5,
                    "max_tokens": 4096,
                    "tool_response_instructions": "Stop when done.",
                    "enable_thinking": False,
                    "enable_test_mode": True
                }
            )
            draft_ids["chain"] = chain_id
            logger.info(f"Created CHAIN: {chain_id}")
        except Exception as e:
            logger.warning(f"CHAIN not available, will use LLM directly: {e}")
            # Use LLM ID as chain_id (for BRAIN configuration)
            chain_id = llm_id

        # 6. Create BRAIN (uses chain and optionally memory)
        brain_config = {
            "chain": {
                "setting_id": chain_id,
                "category": "Draft"
            },
            "memory": {
                "setting_id": memory_id,
                "category": "Draft"
            } if memory_id else None,
            "memory_chunk_size": 2048
        }

        brain_id = self.create_draft(
            scene="BRAIN",
            name="RobotBrainDraftSetting",
            setting_name=self._generate_resource_name(f"{name_suffix}_brain"),
            config=brain_config
        )
        draft_ids["brain"] = brain_id
        logger.info(f"Created BRAIN: {brain_id}")

        # 7. Create DRIVE (uses doc_store)
        drive_id = self.create_draft(
            scene="DRIVE",
            name="RobotMarkIDraftSetting",
            setting_name=self._generate_resource_name(f"{name_suffix}_drive"),
            config={
                "tool_set": [],
                "exception_tips": {
                    "error_suffix": "Test error suffix",
                    "tool_not_found": "Test tool not found",
                    "extraction_error": "Test extraction error"
                },
                "dock_tools": [],
                "top_k": 5
            }
        )
        draft_ids["drive"] = drive_id
        logger.info(f"Created DRIVE: {drive_id}")

        # 8. Create ROBOT (uses brain and drive)
        robot_id = self.create_draft(
            scene="ROBOT",
            name="RobotDraftSetting",
            setting_name=self._generate_resource_name(f"{name_suffix}_robot"),
            config={
                "nick_name": f"TestRobot_{name_suffix}",
                "brain": {
                    "setting_id": brain_id,
                    "category": "Draft"
                },
                "drive": {
                    "setting_id": drive_id,
                    "category": "Draft"
                },
                "lock_timeout": 1800,
                "wait_processing_timeout": 20
            }
        )
        draft_ids["robot"] = robot_id
        logger.info(f"Created ROBOT: {robot_id}")

        return draft_ids

    # ===== Cleanup Methods =====

    def cleanup_all(self):
        """Manually trigger cleanup of all tracked resources.

        Normally you don't need to call this method as teardown will auto-cleanup.
        Only use in special cases (e.g., need to reset state mid-test).
        """
        self.teardown_method()
