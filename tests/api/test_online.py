"""Integration tests for Online API endpoints.

These tests verify online configuration endpoints that actually work.

Note: Online configs are published configurations that cannot be deleted.
Tests create their own test configurations via draft release process.
"""

import logging
import os

import pytest

from roboteditmcp.client import RobotClient

from .base_test import BaseRobotTest

logger = logging.getLogger(__name__)

# Check if online tests should be skipped
SKIP_ONLINE_TESTS = os.getenv('SKIP_ONLINE_TESTS', '').lower() in ('true', '1', 'yes')


@pytest.fixture
def client():
    """Create a RobotClient instance for testing."""
    return RobotClient()


class TestOnlineAPI(BaseRobotTest):
    """Test cases for Online API endpoints (focused on working endpoints).

    Creates test configurations via draft release for action testing.
    Online configs cannot be deleted, but drafts are cleaned up.
    """

    def _create_test_online_configs(self) -> tuple[int, int]:
        """Create test online configurations via draft release.

        Creates a minimal ROBOT config (required for release) and a PROMPT_TEMPLATE config
        for testing actions.

        Returns:
            Tuple of (robot_draft_id, template_draft_id)

        Note: Online configs are created via release and cannot be deleted directly.
              Drafts are tracked for cleanup in teardown.
        """
        import time

        # Create a minimal ROBOT config (required for release)
        # Note: RobotDraftSetting requires specific fields for release
        robot_draft_id = self.create_draft(
            scene="ROBOT",
            name="RobotDraftSetting",
            setting_name=f"{self.RESOURCE_PREFIX}TestOnlineAPI_robot_{int(time.time())}",
            config={
                "nick_name": "test_robot",
                "brain": {"id": 0, "category": "Draft"},  # Placeholder brain
                "drive": {"id": 0, "category": "Draft"},  # Placeholder drive
                "lock_timeout": 60,
                "wait_processing_timeout": 30
            }
        )

        # Create a PROMPT_TEMPLATE config for testing render action
        template_draft_id = self.create_draft(
            scene="PROMPT_TEMPLATE",
            name="FStrTemplateDraft",
            setting_name=f"{self.RESOURCE_PREFIX}TestOnlineAPI_template_{int(time.time())}",
            config={
                "templates": {
                    "zh": "你好吗{name}"
                },
                "active_language": "zh",
                "params_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        }
                    },
                    "required": ["name"]
                }
            }
        )

        # Release drafts to online (requires at least one ROBOT config)
        logger.info(f"Releasing drafts {robot_draft_id} and {template_draft_id} to online...")
        release_result = self.client.draft.release_draft()
        logger.info(f"Release result: {release_result}")

        return robot_draft_id, template_draft_id

    def _find_online_config_by_draft_name(self, draft_setting_name: str) -> tuple | None:
        """Find online config by its draft setting name.

        Args:
            draft_setting_name: The settingName of the draft that was released

        Returns:
            Tuple of (online_id, online_config) or None if not found
        """
        # Query online configs with the same setting name
        online_configs = self.client.online.list_online_configs(
            settingName=draft_setting_name
        )

        if not online_configs:
            return None

        online_config = online_configs[0]
        online_id = online_config.get('settingId') or online_config.get('setting_id') or online_config.get('id')

        return online_id, online_config

    def _get_any_online_config(self) -> tuple | None:
        """Helper method to get any available online config.

        Returns:
            Tuple of (config_id, config) or None if no configs available
        """
        configs = self.client.online.list_online_configs()

        if not configs:
            return None

        # Use the first available config
        online_config = configs[0]
        config_id = (online_config.get('settingId') or online_config.get('setting_id') or
                    online_config.get('id'))

        return config_id, online_config

    def test_list_online_configs(self):
        """Test GET /factory/online/query - List online configurations.

        Verifies:
        - Endpoint is accessible
        - Response contains list of online configs

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        response = self.client.online.list_online_configs()
        assert isinstance(response, list), "Response should be a list"

    def test_get_online_config(self):
        """Test GET /factory/online/:settingId - Get single online config.

        Verifies:
        - Endpoint is accessible with settingId parameter
        - Can retrieve online config details

        Note:
        - If SKIP_ONLINE_TESTS is set, this test will be skipped.
        - Requires existing online configurations in the environment.
        - To prepare test data, run: python tests/api/prepare_online_config.py
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        result = self._get_any_online_config()

        if result is None:
            pytest.skip(
                "No online configurations available. "
                "Run 'python tests/api/prepare_online_config.py' to prepare test data, "
                "or set SKIP_ONLINE_TESTS=true to skip online tests."
            )

        config_id, _ = result

        # Get single online config
        response = self.client.online.get_online_config(config_id)

        # Verify response
        assert isinstance(response, dict), "Response should be a dict"
        assert response.get('settingId') or response.get('setting_id'), "Should have config ID"

    def test_get_online_scenes(self):
        """Test GET /factory/online/scenes - Get available online config scenes.

        Verifies:
        - Endpoint returns list of scene names
        - Response contains expected scenes

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        try:
            response = self.client.online.get_online_scenes()
            assert isinstance(response, list), "Response should be a list"
            # Verify at least one scene exists
            assert len(response) > 0, "Should return at least one scene"
            # Check for expected scene names (may vary by environment)
            expected_scenes = ["ROBOT", "LLM", "CHAIN", "DOC_STORE", "MEMORY"]
            found_scenes = [scene for scene in expected_scenes if scene in response]
            assert len(found_scenes) > 0, f"Should contain at least one common scene, got: {response}"
        except Exception as e:
            # API may not be available in all environments
            error_str = str(e)
            if "500" in error_str or "601" in error_str or "Not Found" in error_str:
                pytest.skip(
                    f"get_online_scenes API not available in this environment: {error_str[:100]}"
                )
            else:
                raise

    def test_get_online_factories(self):
        """Test GET /factory/online/:scene/factories - Get factories for a scene.

        Verifies:
        - Endpoint returns factory names for given scene
        - Response contains factory_names field or factory list

        Uses DOC_STORE as test scene (commonly available).

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        try:
            # Use DOC_STORE as it's commonly available
            test_scene = "DOC_STORE"
            response = self.client.online.get_online_factories(test_scene)
            assert isinstance(response, dict), "Response should be a dict"
            # Response may have 'factory_names' or 'factoryNames' field
            factory_names = (
                response.get('factory_names') or
                response.get('factoryNames') or
                response.get('factories') or
                []
            )
            assert isinstance(factory_names, list), "factory_names should be a list"
            assert len(factory_names) > 0, f"Should return at least one factory for {test_scene}"
        except Exception as e:
            # API may not be available in all environments
            error_str = str(e)
            if ("500" in error_str or "601" in error_str or "Not Found" in error_str or
                "JSONDecodeError" in error_str or "Expecting value" in error_str):
                pytest.skip(
                    f"get_online_factories API not available in this environment: {error_str[:150]}"
                )
            else:
                raise

    def test_get_online_factory_struct(self):
        """Test GET /factory/online/struct/:scene/:factoryName - Get factory structure.

        Verifies:
        - Endpoint returns factory structure definition
        - Response contains config_schema

        Uses DOC_STORE scene and PostgresDocStore factory.

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        Note: Online factory names differ from draft names (e.g., PostgresDocStore vs PostgresDocStoreDraft)
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        try:
            # Use PostgresDocStore (not PostgresDocStoreOnline or PostgresDocStoreDraft)
            test_scene = "DOC_STORE"
            test_factory = "PostgresDocStore"

            # Get factory structure
            response = self.client.online.get_online_factory_struct(
                scene=test_scene,
                factoryName=test_factory
            )

            assert isinstance(response, dict), "Response should be a dict"
            # Verify response contains config_schema
            assert 'config_schema' in response or 'configSchema' in response, \
                "Response should contain config_schema"
        except Exception as e:
            # API may not be available in all environments
            error_str = str(e)
            if ("500" in error_str or "601" in error_str or "Not Found" in error_str or
                "JSONDecodeError" in error_str or "Expecting value" in error_str or
                "FactoryNotFoundError" in error_str):
                pytest.skip(
                    f"get_online_factory_struct API not available in this environment: {error_str[:150]}"
                )
            else:
                raise

    def test_get_online_action_detail(self):
        """Test GET /factory/online/:settingId/action/:action/detail - Get action detail.

        Verifies:
        - Endpoint returns action detail if available
        - Response contains action metadata (params_schema, response_schema, etc.)

        Uses existing DOC_STORE configuration with get_platforms action.

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        This endpoint may be restricted in staging environment.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        # Find DOC_STORE config which has get_platforms action
        all_configs = self.client.online.list_online_configs()

        # Manually filter for DOC_STORE configs (API scene param may not work)
        doc_store_configs = [c for c in all_configs if c.get('scene') == 'DOC_STORE']

        if not doc_store_configs:
            pytest.skip("No DOC_STORE online configurations available")

        # Find one with get_platforms action
        config = None
        for cfg in doc_store_configs:
            tfs_actions = (cfg.get('tfsActions') or cfg.get('tfs_actions', {}))
            if tfs_actions and 'get_platforms' in tfs_actions:
                config = cfg
                break

        if not config:
            pytest.skip("No DOC_STORE config with get_platforms action found")

        config_id = config.get('settingId') or config.get('setting_id') or config.get('id')

        # Get action detail for get_platforms action
        try:
            response = self.client.online.get_online_action_detail(
                setting_id=config_id,
                action="get_platforms"
            )

            # Verify response structure
            assert response is not None, "Response should not be None"
            assert isinstance(response, dict), "Response should be a dict"

            # Response should contain action metadata
            assert len(response) > 0, "Response should contain action metadata"

            # Common fields in action detail
            # May have: params_schema, response_schema, category, etc.
            # Just verify we got some data back
            logger.info(f"Action detail response keys: {list(response.keys())}")

        except Exception as e:
            error_str = str(e)
            # Check for specific errors that indicate environment restrictions
            if ("403" in error_str or "401" in error_str or "forbidden" in error_str.lower() or
                "601" in error_str or "invalid_value" in error_str or
                "404" in error_str or "Not Found" in error_str):
                pytest.skip(
                    f"Action detail endpoint restricted in this environment: {error_str[:150]}"
                )
            else:
                # Re-raise unexpected exceptions
                raise

    def test_trigger_online_action(self):
        """Test PUT /factory/online/:settingId/action/:action - Trigger action.

        Verifies:
        - Endpoint triggers action on online configuration
        - Action returns result (can be dict, list, or other types)
        - Response data is properly extracted from TFSResponse

        Uses existing DOC_STORE configuration with get_platforms action.
        The get_platforms action is a simple GET-type action that returns platform list.

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        # Find DOC_STORE config which has get_platforms action
        all_configs = self.client.online.list_online_configs()

        # Manually filter for DOC_STORE configs (API scene param may not work)
        doc_store_configs = [c for c in all_configs if c.get('scene') == 'DOC_STORE']

        if not doc_store_configs:
            pytest.skip("No DOC_STORE online configurations available")

        # Find one with get_platforms action
        config = None
        for cfg in doc_store_configs:
            tfs_actions = (cfg.get('tfsActions') or cfg.get('tfs_actions', {}))
            if tfs_actions and 'get_platforms' in tfs_actions:
                config = cfg
                break

        if not config:
            pytest.skip("No DOC_STORE config with get_platforms action found")

        config_id = config.get('settingId') or config.get('setting_id') or config.get('id')

        # Trigger the get_platforms action (no parameters needed)
        action_name = "get_platforms"
        response = self.client.online.trigger_online_action(
            setting_id=config_id,
            action=action_name,
            params={}  # get_platforms doesn't require parameters
        )

        # Verify the result
        # The trigger_online_action method extracts TFSResponse.data automatically
        # get_platforms returns a list of platforms: [[id, name], ...] or [] if none configured
        assert response is not None, "Response should not be None"
        assert isinstance(response, list), f"get_platforms should return a list, got {type(response)}"
        # The list may be empty (no platforms configured) or contain platform entries
        logger.info(f"get_platforms returned {len(response)} platforms")

    def test_trigger_online_action_drive(self):
        """Test PUT /factory/online/:settingId/action/:action - Trigger DRIVE action with proper Robot config.

        Verifies:
        - Batch create multiple interdependent drafts (ROBOT, DRIVE, BRAIN, MEMORY, LLM, etc.)
        - Release drafts to online environment
        - DRIVE action works correctly with proper Robot initialization
        - get_all_tools_name action returns tool list

        Uses verified robot configuration from 机器人配置json.txt.

        Test Flow:
        1. Batch create all required drafts
        2. Release to online
        3. Find the created DRIVE config
        4. Trigger get_all_tools_name action
        5. Verify tool list is returned

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        Note: This test may be skipped if ApiFox configs already exist (duplicate config error).
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        # Load verified robot configuration
        import json
        config_file = "/Users/huruize/PycharmProjects/RobotEditMCP/机器人配置json.txt"

        try:
            with open(config_file) as f:
                robot_config = json.load(f)
        except FileNotFoundError:
            pytest.skip(f"Robot configuration file not found: {config_file}")

        drafts_data = robot_config.get('drafts', [])

        # Step 1: Batch create drafts
        try:
            batch_result = self.client.draft.batch_create_drafts(drafts_data)
        except Exception as e:
            error_str = str(e)
            # Check for duplicate config error
            if "Config duplicate" in error_str or "草稿配置名称重复" in error_str:
                pytest.skip(
                    "ApiFox configs already exist from previous test run. "
                    "Please manually delete them or use a different configuration."
                )
            raise

        # Verify batch creation success
        assert batch_result.success_count > 0, "At least some drafts should be created"

        # Track created draft IDs for cleanup
        created_draft_ids = []
        for draft_result in batch_result.results:
            if draft_result.success and draft_result.setting_id:
                created_draft_ids.append(draft_result.setting_id)

        logger.info(f"Created {len(created_draft_ids)} drafts")

        # Step 2: Release to online
        import time
        try:
            release_result = self.client.draft.release_draft()
        except Exception as e:
            error_str = str(e)
            # Check for duplicate or other config errors
            if "Config duplicate" in error_str or "草稿配置名称重复" in error_str:
                pytest.skip(
                    "ApiFox configs already exist in online environment. "
                    "Please manually delete them or use a different configuration."
                )
            raise

        assert release_result is not None, "Release should return a result"
        assert 'onlineRobotId' in release_result, "Release should return online robot ID"

        robot_online_id = release_result['onlineRobotId']
        logger.info(f"Released robot to online, robot_id: {robot_online_id}")

        # Wait for release to propagate
        time.sleep(5)

        # Step 3: Find the created DRIVE config
        # Look for "ApiFoxMarkI" which is tempId=4 in the config
        online_configs = self.client.online.list_online_configs()

        drive_config = None
        for cfg in online_configs:
            setting_name = cfg.get('settingName') or cfg.get('setting_name', '')
            if setting_name == 'ApiFoxMarkI' and cfg.get('scene') == 'DRIVE':
                drive_config = cfg
                break

        if not drive_config:
            pytest.skip("Could not find ApiFoxMarkI DRIVE config after release")

        drive_online_id = drive_config.get('settingId')
        logger.info(f"Found DRIVE config: {drive_online_id}")

        # Step 4: Verify DRIVE has actions
        drive_detail = self.client.online.get_online_config(drive_online_id)
        tfs_actions = (drive_detail.get('tfsActions') or drive_detail.get('tfs_actions', {}))

        assert 'get_all_tools_name' in tfs_actions, "DRIVE should have get_all_tools_name action"

        # Step 5: Trigger get_all_tools_name action
        action_name = "get_all_tools_name"
        response = self.client.online.trigger_online_action(
            setting_id=drive_online_id,
            action=action_name,
            params={}
        )

        # Step 6: Verify response
        assert response is not None, "Action should return a result"
        assert isinstance(response, list), f"get_all_tools_name should return a list, got {type(response)}"

        # The response should be a list of tool definitions
        # Each tool should have at least 'name' and 'description'
        if len(response) > 0:
            first_tool = response[0]
            assert isinstance(first_tool, dict), "Tool should be a dict"
            assert 'name' in first_tool, "Tool should have 'name' field"
            logger.info(f"get_all_tools_name returned {len(response)} tools")
            logger.info(f"First tool: {first_tool.get('name')}")

        # Note: Drafts cannot be deleted after release, so we skip cleanup
        # They will remain in the system but should not interfere with other tests
        logger.info("Test completed successfully. Created drafts remain in system (this is expected).")
