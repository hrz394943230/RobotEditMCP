"""Tests for template management MCP tools.

This module tests all 7 template-related MCP tools by mocking the API layer
and verifying the tool handlers work correctly.
"""

import pytest
from unittest.mock import MagicMock

from roboteditmcp.tools.template import (
    handle_template_tool,
    register_template_tools,
)
from roboteditmcp.client import RobotClient


class TestTemplateToolsRegistration:
    """Tests for template tool registration."""

    def test_template_tools_count(self):
        """Test that all 7 template tools are registered."""
        client = RobotClient()
        tools = register_template_tools(client)
        assert len(tools) == 7

    def test_template_tool_names(self):
        """Test that all expected template tool names are present."""
        client = RobotClient()
        tools = register_template_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_names = {
            "template_get_scenes",
            "template_get_factories",
            "template_get_factory_struct",
            "template_list",
            "template_get",
            "template_apply",
            "template_delete",
        }
        assert tool_names == expected_names

    def test_template_tools_have_valid_schemas(self):
        """Test that all template tools have valid input schemas."""
        client = RobotClient()
        tools = register_template_tools(client)

        for tool in tools:
            assert hasattr(tool, "inputSchema")
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema


class TestTemplateDiscoveryTools:
    """Tests for template discovery tools (get_scenes, get_factories, get_factory_struct)."""

    @pytest.mark.asyncio
    async def test_template_get_scenes(self):
        """Test template_get_scenes tool."""
        client = MagicMock()
        client.template.get_template_scenes = MagicMock(
            return_value=["ROBOT", "LLM", "CHAIN"]
        )

        result = await handle_template_tool("template_get_scenes", {}, client)

        client.template.get_template_scenes.assert_called_once()
        assert result == ["ROBOT", "LLM", "CHAIN"]

    @pytest.mark.asyncio
    async def test_template_get_factories(self):
        """Test template_get_factories tool."""
        client = MagicMock()
        client.template.get_template_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainTemplateSetting", "LLMTemplateSetting"]}
        )

        arguments = {"scene": "ROBOT"}
        result = await handle_template_tool("template_get_factories", arguments, client)

        client.template.get_template_factories.assert_called_once_with(scene="ROBOT")
        assert result["factory_names"] == ["RobotBrainTemplateSetting", "LLMTemplateSetting"]

    @pytest.mark.asyncio
    async def test_template_get_factory_struct(self):
        """Test template_get_factory_struct tool."""
        client = MagicMock()
        mock_struct = {
            "factory_name": "RobotBrainTemplateSetting",
            "config_schema": {"type": "object", "properties": {"model": {"type": "string"}}},
        }
        client.template.get_template_factory_struct = MagicMock(return_value=mock_struct)

        arguments = {"scene": "ROBOT", "factoryName": "RobotBrainTemplateSetting"}
        result = await handle_template_tool(
            "template_get_factory_struct", arguments, client
        )

        client.template.get_template_factory_struct.assert_called_once()
        assert result["factory_name"] == "RobotBrainTemplateSetting"
        assert "config_schema" in result


class TestTemplateQueryTools:
    """Tests for template query tools (list, get)."""

    @pytest.mark.asyncio
    async def test_template_list(self):
        """Test template_list tool with pagination."""
        client = MagicMock()
        mock_templates = {
            "templates": [
                {
                    "setting_id": 1,
                    "scene": "ROBOT",
                    "factory_name": "RobotBrainTemplateSetting",
                    "template_name": "robot_template_v1",
                },
                {
                    "setting_id": 2,
                    "scene": "LLM",
                    "factory_name": "LLMTemplateSetting",
                    "template_name": "llm_template_v1",
                },
            ],
            "total": 2,
        }
        client.template.list_templates = MagicMock(return_value=mock_templates)

        arguments = {"page": 1, "pageSize": 10}
        result = await handle_template_tool("template_list", arguments, client)

        client.template.list_templates.assert_called_once()
        assert result["total"] == 2
        assert len(result["templates"]) == 2

    @pytest.mark.asyncio
    async def test_template_list_with_filters(self):
        """Test template_list tool with filters."""
        client = MagicMock()
        mock_templates = {
            "templates": [
                {
                    "setting_id": 1,
                    "scene": "ROBOT",
                    "factory_name": "RobotBrainTemplateSetting",
                    "template_name": "robot_template_v1",
                }
            ],
            "total": 1,
        }
        client.template.list_templates = MagicMock(return_value=mock_templates)

        arguments = {
            "scene": "ROBOT",
            "factoryName": "RobotBrainTemplateSetting",
            "templateName": "robot_template_v1",
            "page": 1,
            "pageSize": 10,
        }
        result = await handle_template_tool("template_list", arguments, client)

        client.template.list_templates.assert_called_once_with(
            scene="ROBOT",
            factoryName="RobotBrainTemplateSetting",
            settingName=None,
            templateName="robot_template_v1",
            page=1,
            pageSize=10,
        )
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_template_list_default_pagination(self):
        """Test template_list tool with default pagination values."""
        client = MagicMock()
        mock_templates = {"templates": [], "total": 0}
        client.template.list_templates = MagicMock(return_value=mock_templates)

        result = await handle_template_tool("template_list", {}, client)

        client.template.list_templates.assert_called_once_with(
            scene=None,
            factoryName=None,
            settingName=None,
            templateName=None,
            page=1,
            pageSize=10,
        )
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_template_get(self):
        """Test template_get tool."""
        client = MagicMock()
        mock_template = {
            "setting_id": 123,
            "scene": "ROBOT",
            "factory_name": "RobotBrainTemplateSetting",
            "template_name": "my_robot_template",
            "config_schema": {"type": "object"},
            "config": {"model": "gpt-4", "temperature": 0.7},
        }
        client.template.get_template = MagicMock(return_value=mock_template)

        arguments = {"setting_id": 123}
        result = await handle_template_tool("template_get", arguments, client)

        client.template.get_template.assert_called_once()
        assert result["setting_id"] == 123
        assert result["template_name"] == "my_robot_template"
        assert result["config"]["model"] == "gpt-4"


class TestTemplateOperations:
    """Tests for template operations (apply, delete)."""

    @pytest.mark.asyncio
    async def test_template_apply(self):
        """Test template_apply tool."""
        client = MagicMock()
        mock_apply_response = {
            "draft_id": 456,
            "message": "Template applied successfully",
        }
        client.template.apply_template = MagicMock(return_value=mock_apply_response)

        arguments = {"templateSettingId": 123}
        result = await handle_template_tool("template_apply", arguments, client)

        client.template.apply_template.assert_called_once()
        assert result["draft_id"] == 456

    @pytest.mark.asyncio
    async def test_template_delete(self):
        """Test template_delete tool."""
        client = MagicMock()
        mock_delete_response = {"success": True, "message": "Template deleted"}
        client.template.delete_template = MagicMock(return_value=mock_delete_response)

        arguments = {"setting_id": 789}
        result = await handle_template_tool("template_delete", arguments, client)

        client.template.delete_template.assert_called_once()
        assert result["success"] is True


class TestTemplateToolErrorHandling:
    """Tests for template tool error handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self):
        """Test that unknown tool names raise ValueError."""
        client = MagicMock()

        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_template_tool("unknown_template_tool", {}, client)

    @pytest.mark.asyncio
    async def test_template_get_factories_missing_scene(self):
        """Test that template_get_factories raises error when scene is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_template_tool("template_get_factories", {}, client)

    @pytest.mark.asyncio
    async def test_template_get_factory_struct_missing_params(self):
        """Test that template_get_factory_struct raises error when params are missing."""
        client = MagicMock()

        # Missing factoryName
        with pytest.raises(KeyError):
            await handle_template_tool(
                "template_get_factory_struct", {"scene": "ROBOT"}, client
            )

        # Missing scene
        with pytest.raises(KeyError):
            await handle_template_tool(
                "template_get_factory_struct",
                {"factoryName": "RobotBrainTemplateSetting"},
                client,
            )

    @pytest.mark.asyncio
    async def test_template_get_missing_setting_id(self):
        """Test that template_get raises error when setting_id is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_template_tool("template_get", {}, client)

    @pytest.mark.asyncio
    async def test_template_apply_missing_template_id(self):
        """Test that template_apply raises error when templateSettingId is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_template_tool("template_apply", {}, client)

    @pytest.mark.asyncio
    async def test_template_delete_missing_setting_id(self):
        """Test that template_delete raises error when setting_id is missing."""
        client = MagicMock()

        with pytest.raises(KeyError):
            await handle_template_tool("template_delete", {}, client)


class TestTemplateToolsIntegration:
    """Integration tests for template tools workflow."""

    @pytest.mark.asyncio
    async def test_template_discovery_and_application_workflow(self):
        """Test a typical workflow for discovering and applying templates."""
        client = MagicMock()

        # Mock the discovery and application chain
        client.template.get_template_scenes = MagicMock(return_value=["ROBOT", "LLM"])
        client.template.get_template_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainTemplateSetting"]}
        )
        client.template.list_templates = MagicMock(
            return_value={
                "templates": [
                    {
                        "setting_id": 100,
                        "template_name": "standard_robot",
                        "factory_name": "RobotBrainTemplateSetting",
                    }
                ],
                "total": 1,
            }
        )
        client.template.get_template = MagicMock(
            return_value={
                "setting_id": 100,
                "template_name": "standard_robot",
                "config_schema": {},
                "config": {"model": "gpt-4"},
            }
        )
        client.template.apply_template = MagicMock(
            return_value={"draft_id": 500, "message": "Created"}
        )

        # Step 1: Get scenes
        scenes = await handle_template_tool("template_get_scenes", {}, client)
        assert scenes == ["ROBOT", "LLM"]

        # Step 2: Get factories for a scene
        factories = await handle_template_tool(
            "template_get_factories", {"scene": "ROBOT"}, client
        )
        assert "RobotBrainTemplateSetting" in factories["factory_names"]

        # Step 3: List templates
        templates = await handle_template_tool(
            "template_list", {"scene": "ROBOT", "page": 1, "pageSize": 10}, client
        )
        assert len(templates["templates"]) == 1
        template_id = templates["templates"][0]["setting_id"]

        # Step 4: Get template details
        template = await handle_template_tool(
            "template_get", {"setting_id": template_id}, client
        )
        assert template["template_name"] == "standard_robot"

        # Step 5: Apply template
        result = await handle_template_tool(
            "template_apply", {"templateSettingId": template_id}, client
        )
        assert result["draft_id"] == 500

    @pytest.mark.asyncio
    async def test_template_factory_structure_exploration(self):
        """Test exploring template factory structures."""
        client = MagicMock()

        # Mock factory structure exploration
        client.template.get_template_scenes = MagicMock(return_value=["ROBOT"])
        client.template.get_template_factories = MagicMock(
            return_value={"factory_names": ["RobotBrainTemplateSetting"]}
        )
        client.template.get_template_factory_struct = MagicMock(
            return_value={
                "factory_name": "RobotBrainTemplateSetting",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "temperature": {"type": "number"},
                    },
                },
            }
        )

        # Step 1: Get scenes
        scenes = await handle_template_tool("template_get_scenes", {}, client)

        # Step 2: Get factories
        factories = await handle_template_tool(
            "template_get_factories", {"scene": "ROBOT"}, client
        )

        # Step 3: Get factory structure
        factory_struct = await handle_template_tool(
            "template_get_factory_struct",
            {"scene": "ROBOT", "factoryName": "RobotBrainTemplateSetting"},
            client,
        )

        assert "ROBOT" in scenes
        assert "RobotBrainTemplateSetting" in factories["factory_names"]
        assert "config_schema" in factory_struct
        assert "properties" in factory_struct["config_schema"]

    @pytest.mark.asyncio
    async def test_template_list_pagination(self):
        """Test template list pagination behavior."""
        client = MagicMock()

        # Mock paginated responses
        page1_response = {
            "templates": [
                {"setting_id": i, "template_name": f"template_{i}"}
                for i in range(1, 11)
            ],
            "total": 25,
        }
        page2_response = {
            "templates": [
                {"setting_id": i, "template_name": f"template_{i}"}
                for i in range(11, 21)
            ],
            "total": 25,
        }
        page3_response = {
            "templates": [
                {"setting_id": i, "template_name": f"template_{i}"}
                for i in range(21, 26)
            ],
            "total": 25,
        }

        client.template.list_templates = MagicMock(
            side_effect=[page1_response, page2_response, page3_response]
        )

        # Page 1
        result1 = await handle_template_tool(
            "template_list", {"page": 1, "pageSize": 10}, client
        )
        assert len(result1["templates"]) == 10
        assert result1["total"] == 25

        # Page 2
        result2 = await handle_template_tool(
            "template_list", {"page": 2, "pageSize": 10}, client
        )
        assert len(result2["templates"]) == 10
        assert result2["templates"][0]["setting_id"] == 11

        # Page 3
        result3 = await handle_template_tool(
            "template_list", {"page": 3, "pageSize": 10}, client
        )
        assert len(result3["templates"]) == 5
        assert result3["templates"][0]["setting_id"] == 21
