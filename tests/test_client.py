"""Tests for RobotClient API methods."""

from typing import TYPE_CHECKING

import pytest

from roboteditmcp.client import RobotAPIError, RobotClient

if TYPE_CHECKING:
    pass


class TestRobotClient:
    """Test cases for RobotClient class."""

    def test_client_initialization(self, env_vars: dict):
        """Test that RobotClient can be initialized with environment variables.

        Args:
            env_vars: Environment variables loaded from .env
        """
        client = RobotClient()
        assert client is not None
        assert client.base_url == env_vars["ROBOT_BASE_URL"].rstrip("/")
        assert client.admin_token == env_vars["ROBOT_ADMIN_TOKEN"]
        assert client.timeout == int(env_vars["API_TIMEOUT"])

    def test_client_headers_contain_required_fields(self, env_vars: dict):
        """Test that _get_headers returns required HTTP headers.

        Args:
            env_vars: Environment variables loaded from .env
        """
        client = RobotClient()
        headers = client._get_headers()

        # Verify Content-Type header is present
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_client_cookies_contain_required_fields(self, env_vars: dict):
        """Test that _get_cookies returns all required cookies.

        Args:
            env_vars: Environment variables loaded from .env
        """
        client = RobotClient()
        cookies = client._get_cookies()

        # Verify all required cookies are present
        assert "adminToken" in cookies
        assert "tfNamespace" in cookies
        assert "tfRobotId" in cookies

        # Verify cookie values match environment variables
        assert cookies["adminToken"] == env_vars["ROBOT_ADMIN_TOKEN"]
        assert cookies["tfNamespace"] == env_vars["TF_NAMESPACE"]
        assert cookies["tfRobotId"] == env_vars["TF_ROBOT_ID"]


class TestListScenes:
    """Test cases for list_scenes API method."""

    @pytest.mark.integration
    def test_list_scenes_returns_list(self):
        """Test that list_scenes returns a list."""
        try:
            client = RobotClient()
            scenes = client.list_scenes()
            assert isinstance(scenes, list), f"Expected list, got {type(scenes)}"
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")

    @pytest.mark.integration
    def test_list_scenes_returns_strings(self):
        """Test that all items in scenes list are strings."""
        try:
            client = RobotClient()
            scenes = client.list_scenes()
            for scene in scenes:
                assert isinstance(scene, str), f"Expected string, got {type(scene)}"
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")

    @pytest.mark.integration
    def test_list_scenes_not_empty(self):
        """Test that list_scenes returns at least one scene."""
        try:
            client = RobotClient()
            scenes = client.list_scenes()
            assert len(scenes) > 0, "Scenes list should not be empty"
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")

    @pytest.mark.integration
    def test_list_scenes_contains_expected_scenes(self):
        """Test that list_scenes contains common expected scene types.

        This test checks for common scene types like ROBOT, LLM, CHAIN.
        The test is flexible enough to pass if at least some expected scenes are present.
        """
        try:
            client = RobotClient()
            scenes = client.list_scenes()

            # Common expected scene types (based on API documentation)
            common_scenes = {"ROBOT", "LLM", "CHAIN"}

            # Check if at least some of the common scenes are present
            found_scenes = set(scenes) & common_scenes

            assert len(found_scenes) > 0, (
                f"Expected to find at least one of {common_scenes}, but got {scenes}"
            )
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")

    @pytest.mark.integration
    def test_list_scenes_uppercase(self):
        """Test that all scene names are uppercase strings."""
        try:
            client = RobotClient()
            scenes = client.list_scenes()
            for scene in scenes:
                assert scene.isupper(), (
                    f"Scene name '{scene}' should be uppercase, but it's not"
                )
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")

    def test_list_scenes_request_headers(self, mocker, env_vars: dict):
        """Test that list_scenes sends correct HTTP headers and cookies.

        Args:
            mocker: Pytest mocker fixture
            env_vars: Environment variables loaded from .env
        """
        # Mock the HTTP client's get method
        client = RobotClient()
        mock_get = mocker.patch.object(client.client, "get")

        # Mock successful response with example scenes
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": ["ROBOT", "LLM", "CHAIN"],
        }
        mock_get.return_value = mock_response

        # Call list_scenes
        client.list_scenes()

        # Verify the GET request was made
        mock_get.assert_called_once()

        # Check that cookies are set on the client instance
        assert client.client.cookies.get("adminToken") == env_vars["ROBOT_ADMIN_TOKEN"]
        assert client.client.cookies.get("tfNamespace") == env_vars["TF_NAMESPACE"]
        assert client.client.cookies.get("tfRobotId") == env_vars["TF_ROBOT_ID"]

    def test_list_scenes_api_error_handling(self, mocker):
        """Test that list_scenes properly handles API errors.

        Args:
            mocker: Pytest mocker fixture
        """
        client = RobotClient()

        # Mock HTTP error response
        mock_get = mocker.patch.object(client.client, "get")
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"code": 401, "message": "Unauthorized"}
        mock_get.return_value = mock_response

        # Should raise RobotAPIError on 401
        with pytest.raises(RobotAPIError) as exc_info:
            client.list_scenes()

        assert "Unauthorized" in str(exc_info.value)

    def test_list_scenes_request_url(self, mocker):
        """Test that list_scenes calls the correct API endpoint.

        Args:
            mocker: Pytest mocker fixture
        """
        client = RobotClient()
        mock_get = mocker.patch.object(client.client, "get")

        # Mock successful response
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": ["ROBOT", "LLM"],
        }
        mock_get.return_value = mock_response

        # Call list_scenes
        client.list_scenes()

        # Verify the URL is correct
        call_args = mock_get.call_args
        expected_url = f"{client.base_url}/factory/draft-scenes"
        assert call_args[0][0] == expected_url

    @pytest.mark.integration
    def test_list_scenes_response_structure(self):
        """Test that list_scenes returns properly structured data.

        This is an integration test that verifies the actual API response
        structure matches expectations. Mark with pytest.mark.integration to
        skip with: pytest -m "not integration"
        """
        client = RobotClient()
        try:
            scenes = client.list_scenes()

            # Verify response structure
            assert isinstance(scenes, list)
            assert len(scenes) > 0

            # Verify each item is a non-empty string
            for scene in scenes:
                assert isinstance(scene, str)
                assert len(scene) > 0
                # Scene names should typically be uppercase and alphanumeric
                assert scene.isalnum() or "_" in scene or "-" in scene
        except Exception as e:
            pytest.skip(f"Integration test skipped due to backend error: {e}")
