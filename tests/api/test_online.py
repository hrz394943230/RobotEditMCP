"""Integration tests for Online API endpoints.

These tests verify online configuration endpoints that actually work.
"""

import pytest

from roboteditmcp.client import RobotClient
from .base_test import BaseRobotTest


@pytest.fixture
def client(env_vars):
    """Create a RobotClient instance for testing."""
    return RobotClient()


@pytest.fixture
def sample_config(client: RobotClient):
    """Get sample configuration from the API for test data generation."""
    try:
        configs = client.online.list_online_configs()
        if configs:
            return configs[0]
    except Exception:
        pass

    return None


class TestOnlineAPI(BaseRobotTest):
    """Test cases for Online API endpoints (focused on working endpoints).

    Note: Online configs typically don't support deletion, so resource
    tracking is limited but base class provides consistent interface.
    """

    def test_list_online_configs(self):
        """Test GET /factory/online/query - List online configurations.

        Verifies:
        - Endpoint is accessible
        - Response contains list of online configs
        """
        response = self.client.online.list_online_configs()
        assert isinstance(response, list), "Response should be a list"

    def test_get_online_config(self, sample_config):
        """Test GET /factory/online/:settingId - Get single online config.

        Verifies:
        - Endpoint is accessible with settingId parameter
        """
        if sample_config is None:
            pytest.skip("No online configurations available")

        config = sample_config
        config_id = (config.get('settingId') or config.get('setting_id') or
                    config.get('id'))

        response = self.client.online.get_online_config(config_id)
        assert isinstance(response, dict), "Response should be a dict"

    def test_get_online_action_detail(self):
        """Test GET /factory/online/:settingId/action/:action/detail - Get action detail.

        Note: This endpoint is restricted in staging environment (readonly only).
        """
        pytest.skip("Staging环境限制：仅支持readonly接口，Action Detail接口不可用")

    def test_trigger_online_action(self, sample_config):
        """Test PUT /factory/online/:settingId/action/:action - Trigger action.

        Verifies:
        - Endpoint triggers action

        Note: Action format is an array where the last elements are:
        - resourceOpType: 'get', 'get_list', 'update', 'delete', etc.
        - category: 'pageable', 'graphical', 'doc', 'none', etc.
        - isAsync: boolean
        - isPrivate: boolean
        """
        if sample_config is None:
            pytest.skip("No online configurations available")

        config = sample_config
        config_id = (config.get('settingId') or config.get('setting_id') or
                    config.get('id'))

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
