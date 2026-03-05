"""Tests for online configuration management MCP tools.

This module tests all 7 online-related MCP tools by mocking the API layer
and verifying the tool handlers work correctly.
"""

import pytest
from unittest.mock import MagicMock

from roboteditmcp.tools.online import handle_online_tool, register_online_tools
from roboteditmcp.client import RobotClient


class TestOnlineToolsRegistration:
    """Tests for online tool registration."""

    def test_online_tools_count(self):
        """Test that all 7 online tools are registered."""
        client = RobotClient()
        tools = register_online_tools(client)
        assert len(tools) == 7

    def test_online_tool_names(self):
        """Test that all expected online tool names are present."""
        client = RobotClient()
        tools = register_online_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_names = {
            "online_get_scenes",
            "online_get_factories",
            "online_get_factory_struct",
            "online_list",
            "online_get",
            "online_get_action_detail",
            "online_trigger_action",
        }
        assert tool_names == expected_names

    def test_online_tools_have_valid_schemas(self):
        """Test that all online tools have valid input schemas."""
        client = RobotClient()
        tools = register_online_tools(client)

        for tool in tools:
            assert hasattr(tool, "inputSchema")
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema


class TestOnlineDiscoveryTools:
    """Tests for online discovery tools (get_scenes, get_factories, get_factory_struct)."""

    @pytest.mark.asyncio
    async def test_online_get_scenes(self):
        """Test online_get_scenes tool."""
        client = MagicMock()
        client.online.get_online_scenes = MagicMock(
            return_value=["ROBOT", "LLM", "CHAIN"]
        )

        result = await handle_online_tool("online_get_scenes", {}, client)

        client.online.get_online_scenes.assert_called_once()
        assert result == ["ROBOT", "LLM", "CHAIN"]

    @pytest.mark.asyncio
    async def test_online_get_factories(self):
        """Test online_get_factories tool."""
        client = MagicMock()
        client.online.get_online_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainOnlineSetting", "LLMOnlineSetting"]}
        )

        arguments = {"scene": "ROBOT"}
        result = await handle_online_tool("online_get_factories", arguments, client)

        client.online.get_online_factories.assert_called_once_with(scene="ROBOT")
        assert result["factory_names"] == ["RobotBrainOnlineSetting", "LLMOnlineSetting"]

    @pytest.mark.asyncio
    async def test_online_get_factory_struct(self):
        """Test online_get_factory_struct tool."""
        client = MagicMock()
        mock_struct = {
            "factory_name": "RobotBrainOnlineSetting",
            "config_schema": {"type": "object"},
            "tfs_actions": [
                {"name": "test_action", "category": "TEST", "isAsync": False}
            ],
        }
        client.online.get_online_factory_struct = MagicMock(return_value=mock_struct)

        arguments = {"scene": "ROBOT", "factoryName": "RobotBrainOnlineSetting"}
        result = await handle_online_tool(
            "online_get_factory_struct", arguments, client
        )

        client.online.get_online_factory_struct.assert_called_once()
        assert result["factory_name"] == "RobotBrainOnlineSetting"
        assert len(result["tfs_actions"]) == 1


class TestOnlineConfigurationQueries:
    """Tests for online configuration query tools (list, get)."""

    @pytest.mark.asyncio
    async def test_online_list(self):
        """Test online_list tool with filters."""
        client = MagicMock()
        mock_configs = [
            {
                "setting_id": 1,
                "scene": "ROBOT",
                "factory_name": "RobotBrainOnlineSetting",
                "setting_name": "production_robot",
            }
        ]
        client.online.list_online_configs = MagicMock(return_value=mock_configs)

        arguments = {"scene": "ROBOT", "factoryName": "RobotBrainOnlineSetting"}
        result = await handle_online_tool("online_list", arguments, client)

        client.online.list_online_configs.assert_called_once_with(
            scene="ROBOT",
            factoryName="RobotBrainOnlineSetting",
            settingName=None,
        )
        assert len(result) == 1
        assert result[0]["setting_id"] == 1

    @pytest.mark.asyncio
    async def test_online_list_no_filters(self):
        """Test online_list tool without filters."""
        client = MagicMock()
        client.online.list_online_configs = MagicMock(return_value=[])

        result = await handle_online_tool("online_list", {}, client)

        client.online.list_online_configs.assert_called_once_with(
            scene=None,
            factoryName=None,
            settingName=None,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_online_get(self):
        """Test online_get tool."""
        client = MagicMock()
        mock_config = {
            "setting_id": 123,
            "scene": "ROBOT",
            "factory_name": "RobotBrainOnlineSetting",
            "setting_name": "prod_robot",
            "config": {"model": "gpt-4"},
            "tfs_actions": [
                {"name": "restart", "category": "LIFECYCLE", "isAsync": True}
            ],
        }
        client.online.get_online_config = MagicMock(return_value=mock_config)

        arguments = {"setting_id": 123}
        result = await handle_online_tool("online_get", arguments, client)

        client.online.get_online_config.assert_called_once()
        assert result["setting_id"] == 123
        assert result["config"]["model"] == "gpt-4"
        assert len(result["tfs_actions"]) == 1


class TestOnlineActionOperations:
    """Tests for online action operations (get_action_detail, trigger_action)."""

    @pytest.mark.asyncio
    async def test_online_get_action_detail(self):
        """Test online_get_action_detail tool."""
        client = MagicMock()
        mock_action_detail = {
            "action_name": "restart",
            "description": "Restart the robot instance",
            "parameter_schema": {"type": "object"},
            "return_schema": {"type": "string"},
            "metadata": {
                "category": "LIFECYCLE",
                "resourceOpType": "UPDATE",
                "isAsync": True,
                "isPrivate": False,
            },
        }
        client.online.get_online_action_detail = MagicMock(return_value=mock_action_detail)

        arguments = {"setting_id": 201, "action": "restart"}
        result = await handle_online_tool(
            "online_get_action_detail", arguments, client
        )

        client.online.get_online_action_detail.assert_called_once_with(
            setting_id=201, action="restart"
        )
        assert result["action_name"] == "restart"
        assert result["metadata"]["isAsync"] is True

    @pytest.mark.asyncio
    async def test_online_trigger_action(self):
        """Test online_trigger_action tool."""
        client = MagicMock()
        mock_action_result = {
            "success": True,
            "result": {"task_id": "task-123", "status": "pending"},
        }
        client.online.trigger_online_action = MagicMock(return_value=mock_action_result)

        arguments = {
            "setting_id": 301,
            "action": "restart",
            "params": {"force": True},
        }
        result = await handle_online_tool("online_trigger_action", arguments, client)

        client.online.trigger_online_action.assert_called_once()
        assert result["success"] is True
        assert result["result"]["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_online_trigger_action_without_params(self):
        """Test online_trigger_action without optional parameters."""
        client = MagicMock()
        mock_action_result = {"success": True, "result": {"status": "completed"}}
        client.online.trigger_online_action = MagicMock(return_value=mock_action_result)

        arguments = {
            "setting_id": 302,
            "action": "validate",
        }
        result = await handle_online_tool("online_trigger_action", arguments, client)

        client.online.trigger_online_action.assert_called_once()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_online_trigger_action_async_task(self):
        """Test online_trigger_action with async task (CELERY)."""
        client = MagicMock()
        mock_action_result = {
            "success": True,
            "result": {"task_id": "celery-task-456", "status": "PENDING"},
            "is_async": True,
        }
        client.online.trigger_online_action = MagicMock(return_value=mock_action_result)

        arguments = {
            "setting_id": 303,
            "action": "deploy",
            "params": {"environment": "production"},
        }
        result = await handle_online_tool("online_trigger_action", arguments, client)

        client.online.trigger_online_action.assert_called_once()
        assert result["is_async"] is True
        assert "task_id" in result["result"]


class TestOnlineToolErrorHandling:
    """Tests for online tool error handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self):
        """Test that unknown tool names raise ValueError."""
        client = MagicMock()

        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_online_tool("unknown_online_tool", {}, client)

    @pytest.mark.asyncio
    async def test_online_get_factories_missing_scene(self):
        """Test that online_get_factories raises error when scene is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_online_tool("online_get_factories", {}, client)

    @pytest.mark.asyncio
    async def test_online_get_factory_struct_missing_params(self):
        """Test that online_get_factory_struct raises error when params are missing."""
        client = MagicMock()

        # Missing factoryName
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_get_factory_struct", {"scene": "ROBOT"}, client
            )

        # Missing scene
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_get_factory_struct", {"factoryName": "RobotBrainOnlineSetting"}, client
            )

    @pytest.mark.asyncio
    async def test_online_get_missing_setting_id(self):
        """Test that online_get raises error when setting_id is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_online_tool("online_get", {}, client)

    @pytest.mark.asyncio
    async def test_online_get_action_detail_missing_params(self):
        """Test that online_get_action_detail raises error when params are missing."""
        client = MagicMock()

        # Missing action
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_get_action_detail", {"setting_id": 123}, client
            )

        # Missing setting_id
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_get_action_detail", {"action": "restart"}, client
            )

    @pytest.mark.asyncio
    async def test_online_trigger_action_missing_params(self):
        """Test that online_trigger_action raises error when params are missing."""
        client = MagicMock()

        # Missing action
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_trigger_action", {"setting_id": 123}, client
            )

        # Missing setting_id
        with pytest.raises(KeyError):
            await handle_online_tool(
                "online_trigger_action", {"action": "restart"}, client
            )


class TestOnlineToolsIntegration:
    """Integration tests for online tools workflow."""

    @pytest.mark.asyncio
    async def test_online_discovery_workflow(self):
        """Test a typical workflow for discovering online configurations."""
        client = MagicMock()

        # Mock the discovery chain
        client.online.get_online_scenes = MagicMock(return_value=["ROBOT", "LLM"])
        client.online.get_online_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainOnlineSetting"]}
        )
        client.online.get_online_factory_struct = MagicMock(
            return_value={
                "factory_name": "RobotBrainOnlineSetting",
                "config_schema": {},
                "tfs_actions": [{"name": "restart"}],
            }
        )

        # Step 1: Get scenes
        scenes = await handle_online_tool("online_get_scenes", {}, client)
        assert scenes == ["ROBOT", "LLM"]

        # Step 2: Get factories for a scene
        factories = await handle_online_tool(
            "online_get_factories", {"scene": "ROBOT"}, client
        )
        assert "RobotBrainOnlineSetting" in factories["factory_names"]

        # Step 3: Get factory structure
        struct = await handle_online_tool(
            "online_get_factory_struct",
            {"scene": "ROBOT", "factoryName": "RobotBrainOnlineSetting"},
            client,
        )
        assert struct["factory_name"] == "RobotBrainOnlineSetting"
        assert len(struct["tfs_actions"]) == 1

    @pytest.mark.asyncio
    async def test_online_action_workflow(self):
        """Test a typical workflow for triggering online actions."""
        client = MagicMock()

        # Mock the action workflow
        mock_config = {
            "setting_id": 999,
            "setting_name": "prod_robot",
            "tfs_actions": [
                {"name": "restart", "category": "LIFECYCLE", "isAsync": True}
            ],
        }
        mock_action_detail = {
            "action_name": "restart",
            "description": "Restart the robot",
            "parameter_schema": {},
            "metadata": {"isAsync": True},
        }
        mock_trigger_result = {
            "success": True,
            "result": {"task_id": "task-789"},
        }

        client.online.get_online_config = MagicMock(return_value=mock_config)
        client.online.get_online_action_detail = MagicMock(
            return_value=mock_action_detail
        )
        client.online.trigger_online_action = MagicMock(return_value=mock_trigger_result)

        # Step 1: Get config to see available actions
        config = await handle_online_tool("online_get", {"setting_id": 999}, client)
        assert len(config["tfs_actions"]) == 1

        # Step 2: Get action detail
        action_detail = await handle_online_tool(
            "online_get_action_detail", {"setting_id": 999, "action": "restart"}, client
        )
        assert action_detail["action_name"] == "restart"
        assert action_detail["metadata"]["isAsync"] is True

        # Step 3: Trigger action
        result = await handle_online_tool(
            "online_trigger_action",
            {"setting_id": 999, "action": "restart", "params": {}},
            client,
        )
        assert result["success"] is True
        assert "task_id" in result["result"]
