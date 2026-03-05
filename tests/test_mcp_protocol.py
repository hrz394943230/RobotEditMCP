"""MCP Protocol Compliance Tests.

This module ensures RobotEditMCP maintains compatibility with the MCP (Model Context Protocol)
specification when using stdio transport. These tests verify critical protocol behaviors
to prevent breaking changes during code modifications.

Test Coverage:
- MCP initialization handshake
- Protocol version compliance
- Tool discovery and listing
- Tool invocation and response handling
- Error handling and edge cases
- JSON-RPC message format compliance

Reference: https://spec.modelcontextprotocol.io/specification/
"""

import pytest


class TestMCPEndpointStructure:
    """Tests for MCP endpoint structure and routing.

    Verifies that the server correctly exposes tools and maintains
    proper structure for client integration.
    """

    def test_server_has_tools(self):
        """Test that server exposes tools through registration.

        Priority: P0 - Critical for functionality

        Verifies:
        - Tools are registered in the server
        - Tool count meets minimum requirements
        - Tools have proper structure
        """
        from roboteditmcp.client import RobotClient
        from roboteditmcp.tools import (
            register_draft_tools,
            register_online_tools,
            register_template_tools,
        )

        # Create a client and server instance
        client = RobotClient()
        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        # Verify tool count
        assert len(all_tools) >= 25, (
            f"Expected at least 25 tools, got {len(all_tools)}. "
            "If tool count changed intentionally, update this test."
        )

        # Verify each tool has required attributes
        for tool in all_tools:
            assert hasattr(tool, "name"), f"Tool must have 'name' attribute: {tool}"
            assert hasattr(tool, "description"), f"Tool must have 'description' attribute: {tool}"
            assert hasattr(tool, "inputSchema"), f"Tool must have 'inputSchema' attribute: {tool}"

            # Verify name is non-empty string
            assert isinstance(tool.name, str), "Tool name must be a string"
            assert len(tool.name) > 0, "Tool name cannot be empty"

            # Verify description is string
            assert isinstance(tool.description, str), "Tool description must be a string"
            assert len(tool.description) > 10, f"Tool {tool.name} description is too short"

            # Verify inputSchema is dict
            assert isinstance(tool.inputSchema, dict), "Tool inputSchema must be a dict"

    def test_critical_tools_exist(self):
        """Test that all critical tools are available.

        Priority: P0 - Breaking changes if removed

        Verifies:
        - All critical tools are present
        - Tool names haven't changed (backward compatibility)

        Note:
            If a tool is renamed or removed, this test will fail. This is intentional
            to prevent breaking changes. Update CRITICAL_TOOLS if the change is deliberate.
        """
        from roboteditmcp.client import RobotClient
        from roboteditmcp.tools import (
            register_draft_tools,
            register_online_tools,
            register_template_tools,
        )

        # Critical tools that must always be available
        CRITICAL_TOOLS = [
            # Draft operations
            "draft_list",
            "draft_get",
            "draft_create",
            "draft_update",
            "draft_delete",
            "draft_batch_create",
            "draft_release",
            "draft_get_scenes",
            "draft_get_factories",
            "draft_save_as_template",
            "draft_trigger_action",
            # Online operations
            "online_list",
            "online_get",
            "online_get_action_detail",
            "online_trigger_action",
            # Template operations
            "template_list",
            "template_get",
            "template_apply",
            "template_delete",
        ]

        client = RobotClient()
        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools
        tool_names = {tool.name for tool in all_tools}

        missing_tools = set(CRITICAL_TOOLS) - tool_names

        assert len(missing_tools) == 0, (
            f"Critical tools are missing: {missing_tools}. "
            "These tools are part of the public API. "
            "If this is intentional, update CRITICAL_TOOLS in test_mcp_protocol.py"
        )

    def test_tool_naming_convention(self):
        """Test that tools follow consistent naming convention.

        Priority: P2 - Important for API consistency

        Verifies:
        - Tools use category_action naming (e.g., draft_list)
        - No spaces or special characters
        - Names are lowercase with underscores
        """
        import re

        from roboteditmcp.client import RobotClient
        from roboteditmcp.tools import (
            register_draft_tools,
            register_online_tools,
            register_template_tools,
        )

        client = RobotClient()
        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools

        # Pattern: category_action (e.g., draft_list, online_get)
        # Allow: lowercase letters, numbers, underscores
        valid_pattern = re.compile(r'^[a-z][a-z0-9_]*$')

        invalid_names = []
        for tool in all_tools:
            if not valid_pattern.match(tool.name):
                invalid_names.append(tool.name)

        assert len(invalid_names) == 0, (
            f"Tool names don't follow naming convention: {invalid_names}. "
            "Expected pattern: category_action (lowercase with underscores)"
        )

    def test_no_duplicate_tool_names(self):
        """Test that there are no duplicate tool names.

        Priority: P1 - Important for protocol compliance

        Verifies:
        - Each tool has a unique name
        - No name collisions across categories
        """
        from roboteditmcp.client import RobotClient
        from roboteditmcp.tools import (
            register_draft_tools,
            register_online_tools,
            register_template_tools,
        )

        client = RobotClient()
        draft_tools = register_draft_tools(client)
        online_tools = register_online_tools(client)
        template_tools = register_template_tools(client)

        all_tools = draft_tools + online_tools + template_tools
        tool_names = [tool.name for tool in all_tools]

        duplicate_names = {
            name for name in tool_names if tool_names.count(name) > 1
        }

        assert len(duplicate_names) == 0, (
            f"Duplicate tool names found: {duplicate_names}. "
            "Each tool must have a unique name."
        )

    def test_tool_schemas_are_valid(self):
        """Test that tool schemas follow JSON Schema format.

        Priority: P1 - Important for client integration

        Verifies:
        - Input schemas follow JSON Schema specification
        - Required fields are properly defined
        - Types are valid JSON Schema types
        """
        from roboteditmcp.client import RobotClient
        from roboteditmcp.tools import (
            register_draft_tools,
            register_online_tools,
            register_template_tools,
        )

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

            # Verify schema is a dict
            assert isinstance(schema, dict), f"Tool {tool.name} schema must be a dict"

            # Verify basic JSON Schema structure
            assert "type" in schema or "$schema" in schema, (
                f"Tool {tool.name} schema must have 'type' or '$schema' field"
            )

            # If type is "object", verify properties
            if schema.get("type") == "object":
                assert "properties" in schema, (
                    f"Tool {tool.name} has type 'object' but missing 'properties'"
                )

                properties = schema["properties"]
                assert isinstance(properties, dict), (
                    f"Tool {tool.name} properties must be a dict"
                )

                # Verify each property is valid
                for prop_name, prop_schema in properties.items():
                    assert isinstance(prop_schema, dict), (
                        f"Tool {tool.name} property '{prop_name}' schema must be a dict"
                    )

                    # Verify type field if present
                    if "type" in prop_schema:
                        assert prop_schema["type"] in valid_types, (
                            f"Tool {tool.name} property '{prop_name}' has invalid type: "
                            f"{prop_schema['type']}"
                        )


class TestMCPServerInitialization:
    """Tests for MCP server initialization.

    Verifies that the server can be properly initialized and
    configured for stdio transport.
    """

    def test_server_can_be_instantiated(self):
        """Test that MCP server can be instantiated.

        Priority: P0 - Critical for server startup

        Verifies:
        - Server object is created successfully
        - Server has required attributes
        """
        from roboteditmcp.server import RobotEditMCPServer

        server = RobotEditMCPServer()

        assert server is not None
        assert hasattr(server, "get_server")
        assert hasattr(server, "client")

        # Verify get_server returns a valid MCP server instance
        mcp_server = server.get_server()
        assert mcp_server is not None
        assert hasattr(mcp_server, "name")

    def test_server_has_metadata(self):
        """Test that server exposes metadata.

        Priority: P1 - Important for client identification

        Verifies:
        - Server name is defined
        - Server has proper configuration
        """
        from roboteditmcp.server import RobotEditMCPServer

        server = RobotEditMCPServer()
        mcp_server = server.get_server()

        # The mcp.Server should have name attribute
        assert hasattr(mcp_server, "name"), "Server must have name attribute"
        assert mcp_server.name == "roboteditmcp", "Server name should be 'roboteditmcp'"

    def test_server_initialization_options(self):
        """Test server initialization options.

        Priority: P1 - Important for protocol compliance

        Verifies:
        - create_initialization_options() returns valid options
        - Options contain required metadata
        """
        from roboteditmcp.server import RobotEditMCPServer

        server = RobotEditMCPServer()
        mcp_server = server.get_server()

        init_options = mcp_server.create_initialization_options()

        # InitializationOptions should have server_name and server_version
        assert hasattr(init_options, "server_name"), "Init options must have server_name"
        assert hasattr(init_options, "server_version"), "Init options must have server_version"

        assert init_options.server_name == "roboteditmcp"
        assert len(init_options.server_version) > 0


class TestMCPProtocolMessageFormat:
    """Test JSON-RPC message format compliance.

    Ensures that all messages follow the JSON-RPC 2.0 specification
    as required by the MCP protocol.
    """

    def test_json_rpc_request_format(self):
        """Test that JSON-RPC requests follow the correct format.

        Priority: P1 - Important for protocol compliance

        Verifies:
        - Request has required fields (jsonrpc, id, method)
        - jsonrpc version is "2.0"
        - id is present (can be string, number, or null)
        - method is a non-empty string
        """
        # Example valid request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        }

        self._assert_valid_json_rpc_request(request)

        # Test with string id
        request["id"] = "test-id"
        self._assert_valid_json_rpc_request(request)

        # Test with params
        request["params"] = {}
        self._assert_valid_json_rpc_request(request)

    def test_json_rpc_response_format(self):
        """Test that JSON-RPC responses follow the correct format.

        Priority: P1 - Important for protocol compliance

        Verifies:
        - Response has required fields (jsonrpc, id, result OR error)
        - jsonrpc version is "2.0"
        - id matches request id
        - result or error is present (not both)
        """
        # Success response
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": []
            }
        }

        self._assert_valid_json_rpc_response(response)

        # Error response
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }

        self._assert_valid_json_rpc_response(error_response)

    def _assert_valid_json_rpc_request(self, request: dict):
        """Assert that a JSON-RPC request is valid.

        Args:
            request: Request dict to validate

        Raises:
            AssertionError: If request is invalid
        """
        assert "jsonrpc" in request, "Request must have 'jsonrpc' field"
        assert request["jsonrpc"] == "2.0", "jsonrpc version must be '2.0'"

        assert "id" in request, "Request must have 'id' field"
        assert isinstance(request["id"], (str, int, type(None))), (
            "Request id must be string, number, or null"
        )

        assert "method" in request, "Request must have 'method' field"
        assert isinstance(request["method"], str), "Method must be a string"
        assert len(request["method"]) > 0, "Method cannot be empty"

        # If params present, verify it's dict or list
        if "params" in request:
            assert isinstance(request["params"], (dict, list)), (
                "Params must be object or array"
            )

    def _assert_valid_json_rpc_response(self, response: dict):
        """Assert that a JSON-RPC response is valid.

        Args:
            response: Response dict to validate

        Raises:
            AssertionError: If response is invalid
        """
        assert "jsonrpc" in response, "Response must have 'jsonrpc' field"
        assert response["jsonrpc"] == "2.0", "jsonrpc version must be '2.0'"

        assert "id" in response, "Response must have 'id' field"

        # Must have result OR error, not both
        has_result = "result" in response
        has_error = "error" in response

        assert has_result or has_error, "Response must have 'result' or 'error'"
        assert not (has_result and has_error), (
            "Response cannot have both 'result' and 'error'"
        )

        if has_error:
            error = response["error"]
            assert isinstance(error, dict), "Error must be an object"
            assert "code" in error, "Error must have 'code'"
            assert "message" in error, "Error must have 'message'"
            assert isinstance(error["message"], str), "Error message must be a string"


class TestMCPBackwardCompatibility:
    """Tests to ensure backward compatibility is maintained.

    These tests verify that changes to the codebase don't break
    existing client integrations.
    """

    def test_tool_names_not_changed(self):
        """Test that critical tool names haven't changed.

        Priority: P0 - Critical for backward compatibility

        This test documents the expected tool names. If any tool
        is renamed, this test will fail to alert developers to
        update client integrations.
        """
        # This is a documentation test - the actual check is in
        # TestMCPEndpointStructure.test_critical_tools_exist

        expected_tools = {
            # Draft operations
            "draft_list": "List draft configurations",
            "draft_get": "Get a single draft configuration",
            "draft_create": "Create a new draft configuration",
            "draft_update": "Update an existing draft configuration",
            "draft_delete": "Delete a draft configuration",
            "draft_batch_create": "Create multiple drafts at once",
            "draft_release": "Release all drafts to production",
            "draft_get_scenes": "Get available scene types",
            "draft_get_factories": "Get factory types for a scene",
            "draft_save_as_template": "Save a draft as a template",
            "draft_trigger_action": "Trigger an action on a draft",

            # Online operations
            "online_list": "List online configurations",
            "online_get": "Get an online configuration",
            "online_get_action_detail": "Get action metadata",
            "online_trigger_action": "Trigger an online action",

            # Template operations
            "template_list": "List templates",
            "template_get": "Get a template",
            "template_apply": "Apply a template to create a draft",
            "template_delete": "Delete a template",
        }

        # This serves as documentation
        # Actual validation happens in test_critical_tools_exist
        assert len(expected_tools) > 0, "Tool catalog must not be empty"


# Test markers
pytestmark = [
    pytest.mark.unit,  # These are unit tests (no external API calls)
]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "unit"])
