"""Tests for draft configuration management MCP tools.

This module tests all 12 draft-related MCP tools by mocking the API layer
and verifying the tool handlers work correctly.
"""

import pytest
from unittest.mock import MagicMock

from roboteditmcp.tools.draft import handle_draft_tool, register_draft_tools
from roboteditmcp.client import RobotClient


class TestDraftToolsRegistration:
    """Tests for draft tool registration."""

    def test_draft_tools_count(self):
        """Test that all 11 draft tools are registered."""
        client = RobotClient()
        tools = register_draft_tools(client)
        assert len(tools) == 11

    def test_draft_tool_names(self):
        """Test that all expected draft tool names are present."""
        client = RobotClient()
        tools = register_draft_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_names = {
            "draft_get_scenes",
            "draft_get_factories",
            "draft_list",
            "draft_get",
            "draft_create",
            "draft_update",
            "draft_delete",
            "draft_batch_create",
            "draft_release",
            "draft_save_as_template",
            "draft_trigger_action",
        }
        assert tool_names == expected_names

    def test_draft_tools_have_valid_schemas(self):
        """Test that all draft tools have valid input schemas."""
        client = RobotClient()
        tools = register_draft_tools(client)

        for tool in tools:
            assert hasattr(tool, "inputSchema")
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema


class TestDraftDiscoveryTools:
    """Tests for draft discovery tools (get_scenes, get_factories)."""

    @pytest.mark.asyncio
    async def test_draft_get_scenes(self):
        """Test draft_get_scenes tool."""
        client = MagicMock()
        client.draft.get_draft_scenes = MagicMock(return_value=["ROBOT", "LLM", "CHAIN"])

        result = await handle_draft_tool("draft_get_scenes", {}, client)

        client.draft.get_draft_scenes.assert_called_once()
        assert result == ["ROBOT", "LLM", "CHAIN"]

    @pytest.mark.asyncio
    async def test_draft_get_factories(self):
        """Test draft_get_factories tool."""
        client = MagicMock()
        client.draft.get_draft_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainDraftSetting", "LLMDraftSetting"]}
        )

        arguments = {"scene": "ROBOT"}
        result = await handle_draft_tool("draft_get_factories", arguments, client)

        client.draft.get_draft_factories.assert_called_once_with(scene="ROBOT")
        assert result["factory_names"] == ["RobotBrainDraftSetting", "LLMDraftSetting"]


class TestDraftCRUDTools:
    """Tests for draft CRUD operations (list, get, create, update, delete)."""

    @pytest.mark.asyncio
    async def test_draft_list(self):
        """Test draft_list tool with filters."""
        client = MagicMock()
        mock_drafts = [
            {
                "setting_id": 1,
                "scene": "ROBOT",
                "factory_name": "RobotBrainDraftSetting",
                "setting_name": "test_robot",
            }
        ]
        client.draft.list_drafts = MagicMock(return_value=mock_drafts)

        arguments = {"scene": "ROBOT", "factoryName": "RobotBrainDraftSetting"}
        result = await handle_draft_tool("draft_list", arguments, client)

        client.draft.list_drafts.assert_called_once_with(
            scene="ROBOT",
            factoryName="RobotBrainDraftSetting",
            settingName=None,
        )
        assert len(result) == 1
        assert result[0]["setting_id"] == 1

    @pytest.mark.asyncio
    async def test_draft_list_no_filters(self):
        """Test draft_list tool without filters."""
        client = MagicMock()
        client.draft.list_drafts = MagicMock(return_value=[])

        result = await handle_draft_tool("draft_list", {}, client)

        client.draft.list_drafts.assert_called_once_with(
            scene=None,
            factoryName=None,
            settingName=None,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_draft_get(self):
        """Test draft_get tool."""
        client = MagicMock()
        mock_draft = {
            "setting_id": 123,
            "scene": "ROBOT",
            "factory_name": "RobotBrainDraftSetting",
            "setting_name": "test_robot",
            "config": {"model": "gpt-4"},
        }
        client.draft.get_draft = MagicMock(return_value=mock_draft)

        arguments = {"setting_id": 123}
        result = await handle_draft_tool("draft_get", arguments, client)

        client.draft.get_draft.assert_called_once()
        assert result["setting_id"] == 123
        assert result["config"]["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_draft_create(self):
        """Test draft_create tool."""
        client = MagicMock()
        mock_created_draft = {
            "setting_id": 456,
            "scene": "ROBOT",
            "factory_name": "RobotBrainDraftSetting",
            "setting_name": "new_robot",
            "config": {"model": "gpt-4"},
        }
        client.draft.create_draft = MagicMock(return_value=mock_created_draft)

        arguments = {
            "scene": "ROBOT",
            "name": "RobotBrainDraftSetting",
            "setting_name": "new_robot",
            "config": {"model": "gpt-4"},
        }
        result = await handle_draft_tool("draft_create", arguments, client)

        client.draft.create_draft.assert_called_once()
        assert result["setting_id"] == 456
        assert result["setting_name"] == "new_robot"

    @pytest.mark.asyncio
    async def test_draft_update(self):
        """Test draft_update tool with partial update."""
        client = MagicMock()
        mock_updated_draft = {
            "setting_id": 789,
            "scene": "ROBOT",
            "factory_name": "RobotBrainDraftSetting",
            "setting_name": "updated_robot",
            "config": {"model": "gpt-4-turbo"},
        }
        client.draft.update_draft = MagicMock(return_value=mock_updated_draft)

        arguments = {
            "setting_id": 789,
            "setting_name": "updated_robot",
            "config": {"model": "gpt-4-turbo"},
        }
        result = await handle_draft_tool("draft_update", arguments, client)

        client.draft.update_draft.assert_called_once()
        assert result["config"]["model"] == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_draft_delete(self):
        """Test draft_delete tool."""
        client = MagicMock()
        client.draft.delete_draft = MagicMock(return_value={"success": True})

        arguments = {"setting_id": 999}
        result = await handle_draft_tool("draft_delete", arguments, client)

        client.draft.delete_draft.assert_called_once()
        assert result["success"] is True


class TestDraftBatchOperations:
    """Tests for draft batch operations."""

    @pytest.mark.asyncio
    async def test_draft_batch_create(self):
        """Test draft_batch_create tool with multiple drafts."""
        client = MagicMock()
        mock_response = {
            "results": [
                {"temp_id": -1, "setting_id": 101, "success": True},
                {"temp_id": -2, "setting_id": 102, "success": True},
            ],
            "success_count": 2,
            "failure_count": 0,
            "total_count": 2,
        }
        client.draft.batch_create_drafts = MagicMock(return_value=mock_response)

        arguments = {
            "drafts": [
                {
                    "temp_id": -1,
                    "draft": {
                        "scene": "ROBOT",
                        "name": "RobotBrainDraftSetting",
                        "setting_name": "robot1",
                        "config": {},
                    },
                },
                {
                    "temp_id": -2,
                    "draft": {
                        "scene": "LLM",
                        "name": "LLMDraftSetting",
                        "setting_name": "llm1",
                        "config": {},
                    },
                },
            ],
        }
        result = await handle_draft_tool("draft_batch_create", arguments, client)

        client.draft.batch_create_drafts.assert_called_once()
        assert result["success_count"] == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_draft_batch_create_with_references(self):
        """Test draft_batch_create with internal references."""
        client = MagicMock()
        mock_response = {
            "results": [
                {"temp_id": -1, "setting_id": 201, "success": True},
                {"temp_id": -2, "setting_id": 202, "success": True},
            ],
            "success_count": 2,
            "failure_count": 0,
            "total_count": 2,
        }
        client.draft.batch_create_drafts = MagicMock(return_value=mock_response)

        arguments = {
            "drafts": [
                {
                    "temp_id": -1,
                    "draft": {
                        "scene": "LLM",
                        "name": "LLMDraftSetting",
                        "setting_name": "llm_provider",
                        "config": {"model": "gpt-4"},
                    },
                },
                {
                    "temp_id": -2,
                    "draft": {
                        "scene": "ROBOT",
                        "name": "RobotBrainDraftSetting",
                        "setting_name": "robot",
                        "config": {
                            "llm_config": {"setting_id": -1, "category": "Draft"}
                        },
                    },
                },
            ],
        }
        result = await handle_draft_tool("draft_batch_create", arguments, client)

        client.draft.batch_create_drafts.assert_called_once()
        assert len(result["results"]) == 2


class TestDraftReleaseOperations:
    """Tests for draft release operations."""

    @pytest.mark.asyncio
    async def test_draft_release(self):
        """Test draft_release tool."""
        client = MagicMock()
        mock_release_response = {
            "onlineRobotId": 301,
            "message": "Drafts released successfully",
        }
        client.draft.release_draft = MagicMock(return_value=mock_release_response)

        result = await handle_draft_tool("draft_release", {}, client)

        client.draft.release_draft.assert_called_once()
        assert result["onlineRobotId"] == 301


class TestDraftTemplateOperations:
    """Tests for draft template operations."""

    @pytest.mark.asyncio
    async def test_draft_save_as_template(self):
        """Test draft_save_as_template tool."""
        client = MagicMock()
        mock_template_response = {
            "templateId": 401,
            "message": "Template created successfully",
        }
        client.draft.save_as_template = MagicMock(return_value=mock_template_response)

        arguments = {
            "draft_id": 123,
            "name": "RobotBrainTemplateSetting",
            "scene": "ROBOT",
            "setting_name": "my_template",
            "config": {"model": "gpt-4"},
        }
        result = await handle_draft_tool("draft_save_as_template", arguments, client)

        client.draft.save_as_template.assert_called_once()
        assert result["templateId"] == 401

    @pytest.mark.asyncio
    async def test_draft_save_as_template_minimal(self):
        """Test draft_save_as_template with minimal parameters."""
        client = MagicMock()
        mock_template_response = {"templateId": 402}
        client.draft.save_as_template = MagicMock(return_value=mock_template_response)

        arguments = {
            "draft_id": 124,
            "name": "RobotBrainTemplateSetting",
        }
        result = await handle_draft_tool("draft_save_as_template", arguments, client)

        client.draft.save_as_template.assert_called_once()
        assert result["templateId"] == 402


class TestDraftActionOperations:
    """Tests for draft action operations."""

    @pytest.mark.asyncio
    async def test_draft_trigger_action(self):
        """Test draft_trigger_action tool."""
        client = MagicMock()
        mock_action_result = {
            "success": True,
            "result": {"status": "completed"},
        }
        client.draft.trigger_draft_action = MagicMock(return_value=mock_action_result)

        arguments = {
            "setting_id": 501,
            "action": "test_action",
            "params": {"param1": "value1"},
        }
        result = await handle_draft_tool("draft_trigger_action", arguments, client)

        client.draft.trigger_draft_action.assert_called_once()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_draft_trigger_action_without_params(self):
        """Test draft_trigger_action without optional parameters."""
        client = MagicMock()
        mock_action_result = {"success": True}
        client.draft.trigger_draft_action = MagicMock(return_value=mock_action_result)

        arguments = {
            "setting_id": 502,
            "action": "simple_action",
        }
        result = await handle_draft_tool("draft_trigger_action", arguments, client)

        client.draft.trigger_draft_action.assert_called_once()
        assert result["success"] is True


class TestDraftToolErrorHandling:
    """Tests for draft tool error handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self):
        """Test that unknown tool names raise ValueError."""
        client = MagicMock()

        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_draft_tool("unknown_draft_tool", {}, client)

    @pytest.mark.asyncio
    async def test_draft_get_factories_missing_scene(self):
        """Test that draft_get_factories raises error when scene is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_draft_tool("draft_get_factories", {}, client)

    @pytest.mark.asyncio
    async def test_draft_get_missing_setting_id(self):
        """Test that draft_get raises error when setting_id is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_draft_tool("draft_get", {}, client)
