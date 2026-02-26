"""API client for RobotServer.

This module provides a unified facade over specialized API clients.
The actual implementation is delegated to category-specific API classes:
- DraftAPI: Draft configuration management
- OnlineAPI: Production configuration management
- TemplateAPI: Template management
- MetadataAPI: Metadata discovery
"""

import logging

from roboteditmcp.api.draft import DraftAPI
from roboteditmcp.api.metadata import MetadataAPI
from roboteditmcp.api.online import OnlineAPI
from roboteditmcp.api.template import TemplateAPI

logger = logging.getLogger(__name__)


class RobotClient:
    """Unified HTTP client for Robot API.

    This class acts as a facade that composes specialized API clients
    for different functional areas. All method calls are delegated
    to the appropriate API instance.

    Example:
        >>> client = RobotClient()
        >>> drafts = client.list_drafts(scene="ROBOT")
        >>> client.close()
    """

    def __init__(self):
        """Initialize the Robot API client with specialized API instances."""
        self.draft = DraftAPI()
        self.online = OnlineAPI()
        self.template = TemplateAPI()
        self.metadata = MetadataAPI()

        logger.info("RobotClient initialized with specialized API modules")

    # ========== Draft Configuration Management ==========

    def list_drafts(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
    ) -> list:
        """List draft configurations with optional filters.

        Args:
            scene: Filter by scene type (e.g., "ROBOT", "LLM", "CHAIN")
            factoryName: Filter by factory type (e.g., "RobotBrainDraftSetting")
            settingName: Filter by setting name

        Returns:
            List of DraftFactorySettingDto
        """
        return self.draft.list_drafts(scene, factoryName, settingName)

    def get_draft(self, setting_id: int) -> dict:
        """Get a single draft configuration by ID.

        Args:
            setting_id: Draft configuration ID

        Returns:
            DraftFactorySettingDto
        """
        return self.draft.get_draft(setting_id)

    def create_draft(
        self,
        scene: str,
        name: str,
        setting_name: str,
        config: dict,
    ) -> dict:
        """Create a new draft configuration.

        Args:
            scene: Scene type
            name: Factory name
            setting_name: Configuration name
            config: Configuration content (JSON object)

        Returns:
            DraftDetail
        """
        return self.draft.create_draft(scene, name, setting_name, config)

    def update_draft(
        self,
        setting_id: int,
        setting_name: str,
        config: dict,
    ) -> dict:
        """Update a draft configuration (supports partial update).

        Args:
            setting_id: Draft configuration ID
            setting_name: Configuration name (required)
            config: Configuration content to update (only modified fields)

        Returns:
            DraftFactorySettingDto
        """
        return self.draft.update_draft(setting_id, setting_name, config)

    def delete_draft(self, setting_id: int) -> dict:
        """Delete a draft configuration.

        Args:
            setting_id: Draft configuration ID

        Returns:
            Deletion result
        """
        return self.draft.delete_draft(setting_id)

    def batch_create_drafts(self, drafts: list):
        """Batch create draft configurations.

        Args:
            drafts: List of BatchDraftRequest with temp_id and draft config

        Returns:
            BatchDraftResponse with results and counts
        """
        return self.draft.batch_create_drafts(drafts)

    def release_draft(self) -> dict:
        """Release all draft configurations to production environment.

        Note: This releases the entire draft environment, not a single draft.

        Returns:
            Dict with onlineRobotId
        """
        return self.draft.release_draft()

    def get_factory_struct(self, scene: str, factoryName: str) -> dict:
        """Get factory structure information.

        Args:
            scene: Scene type
            factoryName: Factory name

        Returns:
            DraftFactoryStructDto with config_schema and tfs_actions
        """
        return self.draft.get_factory_struct(scene, factoryName)

    def trigger_draft_action(
        self,
        setting_id: int,
        action: str,
        params: dict | None = None,
    ):
        """Trigger an action on a draft configuration.

        Args:
            setting_id: Draft configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult
        """
        return self.draft.trigger_draft_action(setting_id, action, params)

    # ========== Online Configuration Management ==========

    def list_online_configs(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
    ) -> list:
        """List production environment configurations.

        Args:
            scene: Filter by scene type
            factoryName: Filter by factory type
            settingName: Filter by setting name

        Returns:
            List of OnlineFactorySettingDto
        """
        return self.online.list_online_configs(scene, factoryName, settingName)

    def get_online_config(self, setting_id: int) -> dict:
        """Get a single online configuration by ID.

        Args:
            setting_id: Online configuration ID

        Returns:
            OnlineFactorySettingDto
        """
        return self.online.get_online_config(setting_id)

    def get_online_action_detail(self, setting_id: int, action: str) -> dict:
        """Get detailed information about a specific action.

        Args:
            setting_id: Online configuration ID
            action: Action name

        Returns:
            OnlineActionDetailDto
        """
        return self.online.get_online_action_detail(setting_id, action)

    def trigger_online_action(
        self,
        setting_id: int,
        action: str,
        params: dict | None = None,
    ):
        """Trigger an action on an online configuration.

        Args:
            setting_id: Online configuration ID
            action: Action name
            params: Optional action parameters

        Returns:
            ActionResult
        """
        return self.online.trigger_online_action(setting_id, action, params)

    # ========== Template Management ==========

    def list_templates(
        self,
        scene: str | None = None,
        factoryName: str | None = None,
        settingName: str | None = None,
        templateName: str | None = None,
        page: int = 1,
        pageSize: int = 10,
    ):
        """List available templates.

        Args:
            scene: Filter by scene type
            factoryName: Filter by factory type
            settingName: Filter by setting name
            templateName: Filter by template name
            page: Page number (default 1)
            pageSize: Items per page (default 10)

        Returns:
            TemplateListResponse with templates and total count
        """
        return self.template.list_templates(
            scene, factoryName, settingName, templateName, page, pageSize
        )

    def get_template(self, setting_id: int) -> dict:
        """Get a single template by ID.

        Args:
            setting_id: Template ID

        Returns:
            TemplateFactorySettingDto
        """
        return self.template.get_template(setting_id)

    def apply_template(self, templateSettingId: int):
        """Create a new draft configuration from a template.

        Args:
            templateSettingId: Template ID

        Returns:
            ApplyTemplateResponse with draft_id
        """
        return self.template.apply_template(templateSettingId)

    def save_as_template(self, setting_id: int, name: str) -> dict:
        """Save a draft configuration as a template.

        Args:
            setting_id: Draft configuration ID
            name: Template name

        Returns:
            TemplateFactorySettingDto
        """
        return self.template.save_as_template(setting_id, name)

    def delete_template(self, setting_id: int) -> dict:
        """Delete a template.

        Args:
            setting_id: Template ID

        Returns:
            Deletion result
        """
        return self.template.delete_template(setting_id)

    # ========== Metadata Tools ==========

    def list_scenes(self) -> list[str]:
        """List all available scene types.

        Returns:
            List of scene names (e.g., ["ROBOT", "LLM", "CHAIN"])
        """
        return self.metadata.list_scenes()

    def list_factories(
        self,
        scene: str,
        type: str = "draft",
    ):
        """List all factory types for a given scene.

        Args:
            scene: Scene type
            type: Configuration type - "draft", "online", or "template"

        Returns:
            FactoryListResponse with factory_names list
        """
        return self.metadata.list_factories(scene, type)

    # ========== Resource Management ==========

    def close(self):
        """Close all HTTP clients."""
        self.draft.close()
        self.online.close()
        self.template.close()
        self.metadata.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
