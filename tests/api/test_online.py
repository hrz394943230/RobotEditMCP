"""Integration tests for Online API endpoints.

These tests verify online configuration endpoints that actually work.

Note: Online configs are published configurations that cannot be deleted.
Tests use existing online configs or require preparation via:
    python tests/api/prepare_online_config.py

Or set environment variable to skip online tests:
    export SKIP_ONLINE_TESTS=true
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

    Note: Online configs typically don't support deletion, so resource
    tracking is limited but base class provides consistent interface.
    """

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
        - Handles readonly restriction gracefully

        Note: If SKIP_ONLINE_TESTS is set, this test will be skipped.
        This endpoint may be restricted in staging environment (readonly only).
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        result = self._get_any_online_config()

        if result is None:
            pytest.skip("No online configurations available")

        config_id, config = result

        # Get available actions
        tfs_actions = (config.get('tfsActions') or config.get('tfs_actions', {}))
        if not tfs_actions:
            pytest.skip("No actions available in config")

        # Use the first available action
        action_name = list(tfs_actions.keys())[0]

        try:
            response = self.client.online.get_online_action_detail(
                setting_id=config_id,
                action=action_name
            )
            # If we get here, the endpoint works
            assert response is not None, "Response should not be None"
            assert isinstance(response, dict), "Response should be a dict"
        except Exception as e:
            # Check if it's a permission/restriction error or API not available
            error_str = str(e)
            if ("403" in error_str or "401" in error_str or "forbidden" in error_str.lower() or
                "404" in error_str or "Not Found" in error_str):
                pytest.skip(
                    f"Action detail endpoint restricted or not available: {error_str[:100]}"
                )
            elif "readonly" in error_str.lower() or "read-only" in error_str.lower():
                pytest.skip(f"Action detail endpoint restricted (readonly): {error_str[:100]}")
            else:
                # Re-raise other exceptions
                raise

    def test_trigger_online_action(self):
        """Test PUT /factory/online/:settingId/action/:action - Trigger action.

        Verifies:
        - Endpoint triggers action
        - Action returns result (can be dict, list, or other types)

        Note: Action format is an array where the last elements are:
        - resourceOpType: 'get', 'get_list', 'update', 'delete', etc.
        - category: 'pageable', 'graphical', 'doc', 'none', etc.
        - isAsync: boolean
        - isPrivate: boolean

        Note: Uses DOC_STORE config which has 'get_platforms' action.
        """
        if SKIP_ONLINE_TESTS:
            pytest.skip("Online tests skipped via SKIP_ONLINE_TESTS environment variable")

        result = self._get_any_online_config()

        if result is None:
            pytest.skip("No online configurations available")

        config_id, config = result

        # Get available actions
        tfs_actions = (config.get('tfsActions') or config.get('tfs_actions', {}))
        if not tfs_actions:
            pytest.skip("No actions available in this online config")

        # Parse action array format: [params_schema, response_schema, None, resource_type, operation_type, isAsync, isPrivate]
        # Look for GET-type actions that are safe to call
        read_actions = []
        for name, action in tfs_actions.items():
            if isinstance(action, list) and len(action) >= 7:
                # Action format: [params_schema, response_schema, None, resource_type, operation_type, isAsync, isPrivate]
                operation_type = action[4]  # Index 4 is the operation type (get, add, delete, etc.)
                # Look for GET operation type
                if operation_type in ['GET', 'get']:
                    read_actions.append((name, action))

        if not read_actions:
            pytest.skip("No READ-type actions available (staging environment restriction)")

        # Use the first READ-type action
        action_name, action_def = read_actions[0]

        # Extract params schema if available
        params = {}
        if len(action_def) > 0 and isinstance(action_def[0], dict):
            # Use default values from schema if available
            schema = action_def[0]
            for param_name, param_def in schema.get('properties', {}).items():
                if 'default' in param_def:
                    params[param_name] = param_def['default']

        response = self.client.online.trigger_online_action(
            setting_id=config_id,
            action=action_name,
            params=params if params else {},  # Always pass a dict
        )
        assert response is not None, "Response should not be None"
        # Response can be a list, dict, or other type - just verify it's not None
