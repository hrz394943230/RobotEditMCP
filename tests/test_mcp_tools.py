"""Tests for all MCP tools and handlers.

This module provides comprehensive testing of all 26 MCP tools by testing
the tool handlers directly with mocked API clients.
"""

from unittest.mock import MagicMock

import pytest

from roboteditmcp.client import RobotClient
from roboteditmcp.tools import (
    handle_online_tool,
    handle_template_tool,
    register_draft_tools,
    register_online_tools,
    register_template_tools,
)


class TestAllToolsRegistration:
    """Tests for complete tool registration."""

    def test_all_tools_registered(self):
        """Test that all 26 tools are properly registered."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        # Total tool count
        assert len(all_tools) == 25, f"Expected 25 tools, got {len(all_tools)}"

        # Verify individual counts
        assert len(draft_tools) == 11, f"Expected 11 draft tools, got {len(draft_tools)}"
        assert len(online_tools) == 7, f"Expected 7 online tools, got {len(online_tools)}"
        assert len(template_tools) == 7, f"Expected 7 template tools, got {len(template_tools)}"

    def test_all_tool_names_unique(self):
        """Test that all tool names are unique."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools
        tool_names = [tool.name for tool in all_tools]

        # Check for duplicates
        unique_names = set(tool_names)
        assert len(tool_names) == len(unique_names), (
            f"Duplicate tool names found: "
            f"{[name for name in tool_names if tool_names.count(name) > 1]}"
        )

    def test_all_tools_have_required_attributes(self):
        """Test that all tools have required attributes."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        for tool in all_tools:
            # Check required attributes
            assert hasattr(tool, "name"), f"Tool missing 'name': {tool}"
            assert hasattr(tool, "description"), f"Tool {tool.name} missing 'description'"
            assert hasattr(tool, "inputSchema"), f"Tool {tool.name} missing 'inputSchema'"

            # Check types
            assert isinstance(tool.name, str), f"Tool {tool.name} name must be string"
            assert isinstance(tool.description, str), f"Tool {tool.name} description must be string"
            assert isinstance(tool.inputSchema, dict), f"Tool {tool.name} inputSchema must be dict"

            # Check non-empty
            assert len(tool.name) > 0, "Tool name cannot be empty"
            assert len(tool.description) > 10, f"Tool {tool.name} description too short"


class TestDraftToolsCoverage:
    """Tests ensuring all draft tools are covered."""

    def test_draft_tool_names_complete(self):
        """Test that all expected draft tools exist."""
        client = RobotClient()
        tools = register_draft_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_tools = {
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

        missing_tools = expected_tools - tool_names
        extra_tools = tool_names - expected_tools

        assert len(missing_tools) == 0, f"Missing draft tools: {missing_tools}"
        assert len(extra_tools) == 0, f"Unexpected draft tools: {extra_tools}"


class TestOnlineToolsCoverage:
    """Tests ensuring all online tools are covered."""

    def test_online_tool_names_complete(self):
        """Test that all expected online tools exist."""
        client = RobotClient()
        tools = register_online_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_tools = {
            "online_get_scenes",
            "online_get_factories",
            "online_get_factory_struct",
            "online_list",
            "online_get",
            "online_get_action_detail",
            "online_trigger_action",
        }

        missing_tools = expected_tools - tool_names
        extra_tools = tool_names - expected_tools

        assert len(missing_tools) == 0, f"Missing online tools: {missing_tools}"
        assert len(extra_tools) == 0, f"Unexpected online tools: {extra_tools}"


class TestTemplateToolsCoverage:
    """Tests ensuring all template tools are covered."""

    def test_template_tool_names_complete(self):
        """Test that all expected template tools exist."""
        client = RobotClient()
        tools = register_template_tools(client)
        tool_names = {tool.name for tool in tools}

        expected_tools = {
            "template_get_scenes",
            "template_get_factories",
            "template_get_factory_struct",
            "template_list",
            "template_get",
            "template_apply",
            "template_delete",
        }

        missing_tools = expected_tools - tool_names
        extra_tools = tool_names - expected_tools

        assert len(missing_tools) == 0, f"Missing template tools: {missing_tools}"
        assert len(extra_tools) == 0, f"Unexpected template tools: {extra_tools}"


class TestToolHandlerRouting:
    """Tests for tool handler routing."""

    @pytest.mark.asyncio
    async def test_all_draft_tools_routable(self):
        """Test that all draft tools can be routed to handler."""
        client = MagicMock()
        client.draft.get_draft_scenes = MagicMock(return_value=[])

        tool_names = [
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
        ]

        for tool_name in tool_names:
            # Just verify the handler accepts the tool name
            # (actual execution tested in individual test files)
            # We'll check that the tool name exists in handlers
            from roboteditmcp.tools.draft import handle_draft_tool
            # The tool should be routable (we check this by ensuring it doesn't raise ValueError)
            # Since we're not providing args, it will raise KeyError for missing required params
            # But if the tool name is unknown, it will raise ValueError
            try:
                await handle_draft_tool(tool_name, {}, client)
            except ValueError:
                # This means the tool name is unknown - should not happen
                raise AssertionError(f"Tool {tool_name} not routable") from None
            except (KeyError, TypeError):
                # Expected - missing required parameters
                pass

    @pytest.mark.asyncio
    async def test_all_online_tools_routable(self):
        """Test that all online tools can be routed to handler."""
        client = MagicMock()
        client.online.get_online_scenes = MagicMock(return_value=[])

        tool_names = [
            "online_get_scenes",
            "online_get_factories",
            "online_get_factory_struct",
            "online_list",
            "online_get",
            "online_get_action_detail",
            "online_trigger_action",
        ]

        for tool_name in tool_names:
            try:
                await handle_online_tool(tool_name, {}, client)
            except ValueError:
                # This means the tool name is unknown - should not happen
                raise AssertionError(f"Tool {tool_name} not routable") from None
            except (KeyError, TypeError):
                # Expected - missing required parameters
                pass

    @pytest.mark.asyncio
    async def test_all_template_tools_routable(self):
        """Test that all template tools can be routed to handler."""
        client = MagicMock()
        client.template.get_template_scenes = MagicMock(return_value=[])

        tool_names = [
            "template_get_scenes",
            "template_get_factories",
            "template_get_factory_struct",
            "template_list",
            "template_get",
            "template_apply",
            "template_delete",
        ]

        for tool_name in tool_names:
            try:
                await handle_template_tool(tool_name, {}, client)
            except ValueError:
                # This means the tool name is unknown - should not happen
                raise AssertionError(f"Tool {tool_name} not routable") from None
            except (KeyError, TypeError):
                # Expected - missing required parameters
                pass


class TestToolInputSchemas:
    """Tests for tool input schema validation."""

    def test_all_tool_schemas_valid_json_schema(self):
        """Test that all tool input schemas are valid JSON Schema."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        valid_types = {
            "string", "number", "integer", "boolean", "array", "object", "null"
        }

        for tool in all_tools:
            schema = tool.inputSchema

            # Must have type
            assert "type" in schema, f"Tool {tool.name} schema missing 'type'"

            # If type is object, must have properties
            if schema["type"] == "object":
                assert "properties" in schema, (
                    f"Tool {tool.name} has type 'object' but missing 'properties'"
                )

                # Verify each property has valid type
                for prop_name, prop_schema in schema["properties"].items():
                    if "type" in prop_schema:
                        assert prop_schema["type"] in valid_types, (
                            f"Tool {tool.name} property '{prop_name}' has invalid type: "
                            f"{prop_schema['type']}"
                        )

    def test_required_fields_correctly_specified(self):
        """Test that required fields are properly specified in schemas."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        for tool in all_tools:
            schema = tool.inputSchema

            # If required is specified, it must be a list
            if "required" in schema:
                assert isinstance(schema["required"], list), (
                    f"Tool {tool.name} 'required' must be a list"
                )

                # All required fields must exist in properties
                if "properties" in schema:
                    properties = schema["properties"]
                    for required_field in schema["required"]:
                        assert required_field in properties, (
                            f"Tool {tool.name} requires '{required_field}' "
                            f"but it's not in properties"
                        )


class TestToolDescriptions:
    """Tests for tool descriptions."""

    def test_all_tools_have_meaningful_descriptions(self):
        """Test that all tools have meaningful descriptions."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        for tool in all_tools:
            # Check description length
            assert len(tool.description) >= 10, (
                f"Tool {tool.name} description is too short: '{tool.description}'"
            )

            # Check description is not just whitespace
            assert tool.description.strip() == tool.description, (
                f"Tool {tool.name} description has leading/trailing whitespace"
            )

            # Check description contains useful information
            # (should mention what the tool does)
            assert len(tool.description.split()) >= 3, (
                f"Tool {tool.name} description should be more detailed"
            )


class TestToolNamingConventions:
    """Tests for tool naming conventions."""

    def test_tool_names_follow_category_action_pattern(self):
        """Test that tool names follow category_action pattern."""
        import re

        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        # Pattern: category_action (e.g., draft_list, online_get)
        valid_pattern = re.compile(r'^[a-z][a-z0-9_]*$')

        for tool in all_tools:
            assert valid_pattern.match(tool.name), (
                f"Tool {tool.name} doesn't follow naming convention. "
                f"Expected pattern: category_action (lowercase with underscores)"
            )

    def test_tool_names_indicate_category(self):
        """Test that tool names correctly indicate their category."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        # Check draft tools
        for tool in draft_tools:
            assert tool.name.startswith("draft_"), (
                f"Draft tool {tool.name} doesn't start with 'draft_'"
            )

        # Check online tools
        for tool in online_tools:
            assert tool.name.startswith("online_"), (
                f"Online tool {tool.name} doesn't start with 'online_'"
            )

        # Check template tools
        for tool in template_tools:
            assert tool.name.startswith("template_"), (
                f"Template tool {tool.name} doesn't start with 'template_'"
            )


class TestToolCategorySeparation:
    """Tests for proper tool category separation."""

    def test_tools_properly_separated_by_category(self):
        """Test that tools are properly separated into categories."""
        client = RobotClient()

        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        # No tool should appear in multiple categories
        draft_names = {tool.name for tool in draft_tools}
        online_names = {tool.name for tool in online_tools}
        template_names = {tool.name for tool in template_tools}

        # Check for overlaps
        draft_online_overlap = draft_names & online_names
        draft_template_overlap = draft_names & template_names
        online_template_overlap = online_names & template_names

        assert len(draft_online_overlap) == 0, (
            f"Tools appear in both draft and online: {draft_online_overlap}"
        )
        assert len(draft_template_overlap) == 0, (
            f"Tools appear in both draft and template: {draft_template_overlap}"
        )
        assert len(online_template_overlap) == 0, (
            f"Tools appear in both online and template: {online_template_overlap}"
        )
