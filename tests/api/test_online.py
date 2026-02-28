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
def client(env_vars):
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

    def test_get_online_action_detail(self):
        """Test GET /factory/online/:settingId/action/:action/detail - Get action detail.

        Note: This endpoint is restricted in staging environment (readonly only).
        """
        pytest.skip("Staging环境限制：仅支持readonly接口，Action Detail接口不可用")

    def test_trigger_online_action(self):
        """Test PUT /factory/online/:settingId/action/:action - Trigger action.

        Verifies:
        - Endpoint triggers action

        Note: Action format is an array where the last elements are:
        - resourceOpType: 'get', 'get_list', 'update', 'delete', etc.
        - category: 'pageable', 'graphical', 'doc', 'none', etc.
        - isAsync: boolean
        - isPrivate: boolean
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
            pytest.skip("No actions available")

        # Parse action array format: [..., resourceOpType, category, isAsync, isPrivate]
        read_actions = []
        for name, action in tfs_actions.items():
            if isinstance(action, list) and len(action) >= 5:
                # Action format: [schema, ..., resourceOpType, category, isAsync, isPrivate]
                resource_op_type = action[-4] if len(action) >= 4 else None
                # Look for GET, GET_LIST, or READ types
                if resource_op_type in ['GET', 'GET_LIST', 'READ', 'get', 'get_list', 'read']:
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
