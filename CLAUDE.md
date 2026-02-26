# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在处理本仓库代码时提供指导。

## 项目概述

RobotEditMCP 是一个模型上下文协议 (MCP) 服务器，为 AI Agent 提供管理 Robot 配置的工具。它通过 RESTful API 实现对草稿配置、在线（生产）配置和模板的操作。

服务器通过以下 HTTP 头部进行认证和路由：
- `admin_key`: API 认证令牌（使用 ROBOT_ADMIN_TOKEN）
- `tfNamespace`: Kubernetes 命名空间，用于 K8s 网络层 Pod 定位
- `tfRobotId`: Robot 实例标识符，用于 K8s 服务发现和路由

## 常用开发命令

### 环境设置
```bash
# 安装依赖（使用 uv 进行快速包管理）
make install          # 或者: uv sync
make dev             # 安装开发依赖

# 从示例创建 .env 文件
cp .env.example .env
# 编辑 .env 文件，填入必需的环境变量：
# - ROBOT_ADMIN_TOKEN: API 认证令牌
# - ROBOT_BASE_URL: API 基础 URL
# - TF_NAMESPACE: Kubernetes 命名空间
# - TF_ROBOT_ID: Robot 实例标识符
```

### 代码质量
```bash
make lint            # 运行 ruff linter
make format          # 使用 ruff 格式化代码
make check-fmt       # 检查格式但不修改文件
make lint-fix        # 自动修复 lint 问题
```

### 运行服务器
```bash
make run             # 启动 MCP 服务器
# 或者直接运行：
uv run roboteditmcp
python -m roboteditmcp.main
```

### 测试
```bash
make test            # 运行 pytest（目前还没有测试）
```

## 架构

### 核心组件

**client.py (RobotClient)**
- 使用 `httpx` 的底层 HTTP 客户端，支持连接池
- 所有 API 端点按类别组织（draft/online/template/metadata）
- 通过 TFSResponse 模型使用 `_handle_response()` 标准化响应
- API 错误时抛出带 code 和 message 的 `RobotAPIError`
- 认证：使用 `admin_key` 头部（不是 Bearer token）

**server.py (RobotEditMCPServer)**
- 使用 `mcp.Server` 编排 MCP 服务器
- 将工具注册委托给特定类别的函数
- 将工具调用路由到相应的处理器（draft/online/template/metadata）
- 以 `TextContent` 格式返回序列化的 JSON 结果

**tools/*.py (工具定义)**
- 每个类别（draft/online/template/metadata）都有自己的模块
- 模式：`register_*_tools()` 返回工具定义列表
- 模式：`handle_*_tool()` 执行工具调用并路由到客户端方法
- 工具使用 JSON Schema 进行输入验证

**config.py**
- 通过 `python-dotenv` 加载环境变量
- 验证必需变量：`ROBOT_ADMIN_TOKEN`、`ROBOT_BASE_URL`、`TF_NAMESPACE`、`TF_ROBOT_ID`
- 可选变量：`ROBOT_LOG_LEVEL`、`API_TIMEOUT`、`MAX_CONNECTIONS`
- `TF_NAMESPACE` 和 `TF_ROBOT_ID` 用于 Kubernetes 网络层的 Pod 定位和路由

### 工具类别（共 20 个工具）

**草稿配置（9 个工具）**
- `list_drafts`、`get_draft`、`create_draft`、`update_draft`、`delete_draft`
- `batch_create_drafts` - 通过 temp_id 支持内部引用
- `release_draft` - 将所有草稿发布到生产环境（不是单个草稿）
- `get_factory_struct` - 返回 config_schema 和 tfs_actions
- `trigger_draft_action` - 在草稿上执行操作

**在线配置（4 个工具）**
- `list_online_configs`、`get_online_config`
- `get_online_action_detail` - 获取操作元数据
- `trigger_online_action` - 执行操作（支持异步）

**模板管理（5 个工具）**
- `list_templates` - 分页（page, pageSize）
- `get_template`、`apply_template` - 从模板创建草稿
- `save_as_template` - 将草稿保存为命名模板
- `delete_template`

**元数据发现（2 个工具）**
- `list_scenes` - 返回 ["ROBOT", "LLM", "CHAIN", ...]
- `list_factories` - 返回场景/类型的工厂名称

### 数据流

1. AI Agent 调用 MCP 工具 → `server.py:call_tool()`
2. 路由到 tools/*.py 中的 `handle_*_tool()`
3. 处理器调用 client.py 中的 `RobotClient` 方法
4. 客户端发起带 `admin_key` 头部的 HTTP 请求
5. 通过 `_handle_response()` 解析响应 → TFSResponse
6. 以 TextContent 格式返回结果给 AI Agent

### 批量创建模式

创建相互关联的配置时（例如，引用 LLM 提供商的 Robot）：
- 使用 `temp_id`（负整数）作为临时标识符
- 通过 `{"setting_id": -1, "category": "Draft"}` 引用
- API 在创建后解析真实 ID
- 参见 README.md 第 167-189 行的示例

### 响应格式

所有 API 响应遵循 TFSResponse 结构：
```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

非 200 代码会抛出带详细消息的 `RobotAPIError`。

## 添加新工具

1. 按照现有模式在 `client.py` 中添加客户端方法
2. 在相应的 `tools/*.py` 文件中添加工具定义
3. 在同一文件中添加处理函数
4. 在 `server.py:_register_tools()` 中注册工具
5. 在 `server.py:tool_categories` 字典中添加路由条目

### 工具定义模式
```python
Tool(
    name="tool_name",
    description="清晰的描述，包含示例",
    inputSchema={
        "type": "object",
        "required": ["param1"],
        "properties": {
            "param1": {"type": "string", "description": "..."},
        },
    },
)
```

### 处理器模式
```python
async def handle_category_tool(tool_name: str, arguments: dict, client: RobotClient):
    handlers = {
        "tool_name": lambda: client.method(arg=arguments["arg"]),
    }
    if tool_name not in handlers:
        raise ValueError(f"Unknown tool: {tool_name}")
    return handlers[tool_name]()
```

## 配置管理

- 从 `.env` 文件加载环境变量（不在 git 中）
- 查看 `.env.example` 了解必需变量
- 在客户端初始化时调用 `config.validate()`
- 缺少必需变量会在启动时抛出 ValueError

## 日志

- 通过 `logging_config.py` 配置
- 级别由 `ROBOT_LOG_LEVEL` 环境变量控制（INFO/ERROR/DEBUG）
- 日志包括工具调用、API 请求、错误
- 使用 `logger.info/error/debug` 进行记录

## 错误处理

- `RobotAPIError`：带 code 和 message 的 API 错误
- `ValidationError`：Pydantic 验证失败
- `ValueError`：配置错误
- 所有异常都被 `call_tool()` 捕获并记录堆栈跟踪

## 包管理

本项目使用 `uv` 进行快速的 Python 包管理（比 pip/poetry 更快）。
- `uv.lock` 包含锁定版本的依赖
- 编辑 `pyproject.toml` 修改依赖
- 依赖更改后运行 `uv sync`

## API 文档参考

- RobotServer API：`/Users/huruize/PycharmProjects/TFRobotServer/tfrobotserver/api/v1/robot_factory/`
- 示例配置：`/Users/huruize/PycharmProjects/RobotEditMCP/机器人配置json.txt`
- ROBOT_CONFIG_API.md 包含详细的 API 文档

## 关键约束

- 始终使用 `admin_key` 头部进行认证（不是 Bearer token）
- `release_draft()` 发布所有草稿，不是单个草稿
- `update_draft()` 支持部分更新（仅修改的字段）
- 模板操作需要 `setting_id`（整数，不是字符串）
- 批量创建需要负的 `temp_id` 值用于引用
