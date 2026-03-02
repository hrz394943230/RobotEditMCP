# RobotEditMCP

MCP server for Robot configuration management - AI Agent tools for Robot draft/online/template configs.

## Overview

RobotEditMCP provides AI Agents with tools to manage Robot configurations through a Model Context Protocol (MCP) server. It enables operations on draft, online (production), and template configurations with support for complex relationships and batch operations.

## Features

- **Draft Configuration Management**: Create, read, update, delete draft configs
- **Online Configuration Management**: Manage production environment configs
- **Template Management**: Save, load, and apply configuration templates
- **Batch Operations**: Create interconnected configurations with internal references
- **Action Triggering**: Execute configuration actions (sync and async)
- **Metadata Discovery**: Explore scenes, factories, and schemas
- **Progressive Disclosure**: Tools designed for AI-driven exploration

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry for package management

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd RobotEditMCP

# Install in development mode
pip install -e .

# Or with poetry
poetry install
```

## Configuration

RobotEditMCP requires environment variables for authentication and API access:

### Required Environment Variables

Create a `.env` file in your project root:

```bash
# Required - API authentication and endpoint
ROBOT_ADMIN_TOKEN=your_admin_token_here
ROBOT_BASE_URL=https://api.robot.com

# Required - Kubernetes network routing headers
TF_NAMESPACE=staging-tenant
TF_ROBOT_ID=friday

# Optional
ROBOT_LOG_LEVEL=INFO
API_TIMEOUT=30
MAX_CONNECTIONS=10
```

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ROBOT_ADMIN_TOKEN` | Yes | Admin API token for authentication (sent in `adminToken` cookie) | - |
| `ROBOT_BASE_URL` | Yes | RobotServer base URL | - |
| `TF_NAMESPACE` | Yes | Kubernetes namespace for Pod routing (sent in `tfNamespace` cookie) | - |
| `TF_ROBOT_ID` | Yes | Robot instance identifier for K8s service discovery (sent in `tfRobotId` cookie) | - |
| `ROBOT_LOG_LEVEL` | No | Log level (INFO/ERROR/DEBUG) | `INFO` |
| `API_TIMEOUT` | No | API request timeout in seconds | `30` |
| `MAX_CONNECTIONS` | No | Maximum HTTP connections | `10` |

### Kubernetes Architecture Notes

**`TF_NAMESPACE` and `TF_ROBOT_ID`** are essential cookies used in the Kubernetes network layer:

- **`tfNamespace`**: Identifies the K8s namespace where the Robot pods are deployed
- **`tfRobotId`**: Identifies the specific Robot instance for service discovery and routing

These cookies enable proper network routing in multi-tenant K8s environments, allowing requests to reach the correct Robot pod. They are set on the HTTP client instance and sent with every HTTP request, processed by the Kubernetes network infrastructure (e.g., Ingress, Service Mesh, or custom controllers).

## Usage

### Running the MCP Server

```bash
# Using the installed command
roboteditmcp

# Or directly with Python
python -m roboteditmcp.main
```

### MCP Client Configuration

Add to your Claude Desktop config or MCP client configuration:

```json
{
  "mcpServers": {
    "robotedit": {
      "command": "roboteditmcp",
      "env": {
        "ROBOT_ADMIN_TOKEN": "your_token_here",
        "ROBOT_BASE_URL": "https://api.robot.com",
        "TF_NAMESPACE": "staging-tenant",
        "TF_ROBOT_ID": "friday"
      }
    }
  }
}
```

## Available Tools

### Draft Configuration (9 tools)

1. **list_drafts** - List draft configurations with optional filters
2. **get_draft** - Get detailed information about a single draft
3. **create_draft** - Create a new draft configuration
4. **update_draft** - Update a draft (supports partial updates)
5. **delete_draft** - Delete a draft configuration
6. **batch_create_drafts** - Batch create with internal references
7. **release_draft** - Release all drafts to production
8. **trigger_draft_action** - Trigger an action on a draft

### Online Configuration (4 tools)

9. **list_online_configs** - List production environment configs
11. **get_online_config** - Get online configuration details
12. **get_online_action_detail** - Get action details (Online only)
13. **trigger_online_action** - Trigger an action (supports async)

### Template Management (5 tools)

14. **list_templates** - List available templates (paginated)
15. **get_template** - Get template details
16. **apply_template** - Create draft from template
17. **save_as_template** - Save draft as template
18. **delete_template** - Delete a template

### Metadata Tools (2 tools)

19. **list_scenes** - List all scene types
20. **list_factories** - List factories for a scene

## Usage Examples

### Exploring the Configuration System

```python
# 1. List available scenes
scenes = list_scenes()
# Returns: ["ROBOT", "LLM", "CHAIN", ...]

# 2. List factories for a scene
factories = list_factories(scene="ROBOT", type="draft")
# Returns: {factory_names: ["RobotBrainDraftSetting", ...]}
```

### Creating a Configuration

```python
# Create a new draft
draft = create_draft(
    scene="ROBOT",
    name="RobotBrainDraftSetting",
    setting_name="My Robot Config",
    config={"model": "gpt-4", "temperature": 0.7}
)
```

### Batch Creating with References

```python
# Create multiple interconnected configs
result = batch_create_drafts(drafts=[
    {
        "temp_id": -1,
        "draft": {
            "scene": "LLM",
            "name": "LLMProviderDraftSetting",
            "setting_name": "My GPT",
            "config": {"model": "gpt-4"}
        }
    },
    {
        "temp_id": -2,
        "draft": {
            "scene": "ROBOT",
            "name": "RobotBrainDraftSetting",
            "setting_name": "My Robot",
            "config": {
                "llm_provider": {"setting_id": -1, "category": "Draft"}
            }
        }
    }
])
```

### Updating and Releasing

```python
# Update configuration (partial)
update_draft(
    setting_id=123,
    setting_name="My Robot Config (Updated)",
    config={"temperature": 0.8}  # Only update temperature
)

# Release all drafts to production
release_draft()
```

## Architecture

```
src/roboteditmcp/
├── __init__.py           # Package initialization
├── config.py             # Configuration management
├── client.py             # HTTP API client
├── server.py             # MCP server implementation
├── main.py               # CLI entry point
├── logging_config.py     # Logging setup
├── models/
│   └── __init__.py       # Data models
└── tools/
    ├── __init__.py       # Tools registry
    ├── draft.py          # Draft configuration tools
    ├── online.py         # Online configuration tools
    ├── template.py       # Template management tools
    └── metadata.py       # Metadata tools
```

## Authentication

RobotEditMCP uses the `admin_key` header for authentication (consistent with frontend implementation):

```python
headers = {
    "admin_key": ROBOT_ADMIN_TOKEN,
    "Content-Type": "application/json"
}
```

## Error Handling

All API responses follow the TFSResponse format:

```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

Errors are raised with detailed messages for debugging.

## Development

### Running Tests

```bash
# Run tests (if available)
pytest tests/

# Or with poetry
poetry run pytest
```

### Code Structure

- **client.py**: Low-level HTTP client with all API endpoints
- **tools/*.py**: MCP tool definitions and handlers
- **server.py**: MCP server orchestration
- **config.py**: Configuration and validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions:
- API Documentation: `/Users/huruize/PycharmProjects/TFRobotServer/tfrobotserver/api/v1/robot_factory/`
- Example Configurations: `/Users/huruize/PycharmProjects/RobotEditMCP/机器人配置json.txt`

## Version History

- **0.1.0** (2025): Initial release
  - Draft, Online, Template configuration management
  - Batch operations with references
  - Action triggering (sync/async)
  - Metadata discovery tools
