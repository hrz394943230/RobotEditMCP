# RobotEditMCP 规格说明

## 项目概述

为 AI Agent 提供操作 Robot 草稿和生产配置的工具，最终实现一个 MCP 服务。用户通过环境变量获取 `admin_token` 和 `base_url` 来请求 RobotServer 暴露的接口。

**核心目标**：让大模型能够操作配置的生成和修改，同时通过 **渐进式披露** 策略处理复杂的 schema 和大量数据。

**API 代码实现**：`/Users/huruize/PycharmProjects/TFRobotServer/tfrobotserver/api/v1/robot_factory/`

---

## 环境配置

| 环境变量 | 必需 | 说明 |
|---------|------|------|
| `ROBOT_ADMIN_TOKEN` | 是 | Admin API Token，用于 Bearer 认证 |
| `ROBOT_BASE_URL` | 是 | RobotServer 的基础 URL，如 `https://api.robot.com` |
| `ROBOT_LOG_LEVEL` | 否 | 日志级别，默认 `INFO`，可选 `ERROR`/`DEBUG` |

---

## 认证机制

使用 **Admin Key** 在请求头中传递 admin_token：

```
admin_key: {ROBOT_ADMIN_TOKEN}
```

**注意**：这与前端实现保持一致，前端使用 `admin_key` header 而非标准的 `Authorization: Bearer`。

---

## 工具列表

### Draft 配置管理

#### 1. `list_drafts`
列出草稿配置，支持可选过滤。

**参数**：
- `scene` (可选): 过滤特定场景，如 `"ROBOT"`, `"LLM"`, `"CHAIN"`
- `factoryName` (可选): 过滤特定工厂类型，如 `"RobotBrainDraftSetting"`
- `settingName` (可选): 过滤配置名称

**返回**：`{code, message, data: DraftFactorySettingDto[]}`

**注意**：后端始终返回完整的 DTO，包含 `config_schema`、`tfs_actions` 等完整信息。MCP 层可根据需要实现字段过滤。

#### 2. `get_draft`
获取单个草稿配置的详细信息。

**参数**：
- `setting_id` (必需): 配置 ID

**返回**：`{code, message, data: DraftFactorySettingDto}`

**注意**：
- DTO 包含 `config_schema`、`tfs_actions` 等完整信息
- 引用始终以 `{setting_id, category}` 形式返回，不支持展开
- `tfs_actions` 字段包含该配置支持的所有操作及元数据

#### 3. `create_draft`
创建新的草稿配置。

**参数**：
- `scene` (必需): 场景类型
- `name` (必需): 工厂名称
- `setting_name` (必需): 配置名称
- `config` (必需): 配置内容（JSON 对象）

**返回**：`{code, message, data: DraftDetail}`

#### 4. `update_draft`
更新草稿配置（支持部分更新）。

**参数**：
- `setting_id` (必需): 配置 ID
- `setting_name` (必需): 配置名称
- `config` (必需): 要更新的配置内容（只传需要修改的字段）

**返回**：`{code, message, data: DraftFactorySettingDto}`

**注意**：
- `setting_name` 是必需参数
- `config` 支持部分更新，使用 Pydantic 的 `model_copy(update=...)` 实现

#### 5. `delete_draft`
删除草稿配置。

**参数**：
- `setting_id` (必需): 配置 ID

**返回**：`{code, message, data: {...}}`

#### 6. `batch_create_drafts`
批量创建相互关联的草稿配置。

**参数**：
- `drafts` (必需): 草稿数组，每个包含 `temp_id`（负数）、`draft` 对象
  - `temp_id`: 临时 ID（负数），用于在 batch 内部建立引用关系
  - `draft.scene`: 场景
  - `draft.name`: 工厂名称
  - `draft.setting_name`: 配置名称
  - `draft.config`: 配置内容

**返回**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "index": 0,
        "temp_id": -1,
        "success": true,
        "setting_id": 123,
        "setting_dto": {...},
        "error_message": null
      }
    ],
    "success_count": 1,
    "failure_count": 0,
    "total_count": 1
  }
}
```

**注意**：
- 引用解析由服务端处理，MCP 直接透传请求
- 使用负数 temp_id（如 -1, -2）建立内部引用
- 返回详细结果列表，包含每个草稿的成功/失败状态

#### 7. `release_draft`
发布整套草稿配置到生产环境。

**参数**：无

**返回**：`{code, message, data: {onlineRobotId: int}}`

**说明**：
- 发布当前所有的草稿配置到生产环境
- 要求草稿中必须包含一个且仅一个 Robot 配置
- 会先清理当前线上配置，再发布（失败会回滚）
- 返回发布后的线上 Robot 配置 ID

**重要**：这不是发布单个草稿，而是发布整个草稿环境！

#### 8. `get_factory_struct`
获取特定场景和工厂类型的结构信息。

**参数**：
- `scene` (必需): 场景类型
- `factoryName` (必需): 工厂名称

**返回**：`{code, message, data: DraftFactoryStructDto}`

**说明**：
- 返回工厂的结构信息，包括 `config_schema` 和 `tfs_actions`
- `tfs_actions` 包含该工厂类型支持的所有操作及元数据
- 适用于了解某个工厂类型的功能而不需要具体配置实例

#### 9. `trigger_draft_action`
触发草稿的操作。

**参数**：
- `setting_id` (必需): 配置 ID
- `action` (必需): 操作名称
- `params` (可选): 操作参数（JSON 对象）

**返回**：`{code, message, data: ActionResult}`

**注意**：
- Actions 列表已包含在 `get_draft` 返回的 `tfs_actions` 字段中
- 草稿配置不能触发 CELERY 异步任务（仅在线配置支持）

---

### Online（生产）配置管理

#### 10. `list_online_configs`
列出生产环境配置。

**参数**：
- `scene` (可选): 过滤特定场景
- `factoryName` (可选): 过滤特定工厂类型
- `settingName` (可选): 过滤配置名称

**返回**：`{code, message, data: OnlineFactorySettingDto[]}`

#### 11. `get_online_config`
获取单个生产配置详情。

**参数**：
- `setting_id` (必需): 配置 ID

**返回**：`{code, message, data: OnlineFactorySettingDto}`

**注意**：
- DTO 包含 `config_schema`、`tfs_actions` 等完整信息
- `tfs_actions` 字段包含该配置支持的所有操作及元数据

#### 12. `get_online_action_detail`
获取单个操作的详细信息。

**参数**：
- `setting_id` (必需): 配置 ID
- `action` (必需): 操作名称

**返回**：`{code, message, data: OnlineActionDetailDto}`

**说明**：
- 返回操作的参数 schema、返回值 schema、描述等详细信息
- 仅 Online 配置支持此端点

#### 13. `trigger_online_action`
触发生产配置的操作。

**参数**：
- `setting_id` (必需): 配置 ID
- `action` (必需): 操作名称
- `params` (可选): 操作参数（JSON 对象）

**返回**：`{code, message, data: ActionResult}`

**注意**：
- Actions 列表已包含在 `get_online_config` 返回的 `tfs_actions` 字段中
- Online 配置支持触发 CELERY 异步任务

---

### Template 模板管理

#### 14. `list_templates`
列出可用的模板。

**参数**：
- `scene` (可选): 过滤特定场景
- `factoryName` (可选): 过滤特定工厂类型
- `settingName` (可选): 过滤配置名称
- `templateName` (可选): 过滤模板名称
- `page` (必需): 页码，默认 1
- `pageSize` (必需): 每页数量，默认 10

**返回**：`{code, message, data: {templates: [...], total: int}}`

#### 15. `get_template`
获取单个模板详情。

**参数**：
- `setting_id` (必需): 模板 ID

**返回**：`{code, message, data: TemplateFactorySettingDto}`

#### 16. `apply_template`
从模板创建新的草稿配置。

**参数**：
- `templateSettingId` (必需): 模板 ID

**返回**：`{code, message, data: {draftId: int}}`

**注意**：
- 不支持指定新配置名称
- 应用后需要通过 `update_draft` 修改名称

#### 17. `save_as_template`
将草稿保存为模板。

**参数**：
- `setting_id` (必需): 草稿 ID
- `name` (必需): 模板名称（通过请求体传递）

**返回**：`{code, message, data: TemplateFactorySettingDto}`

#### 18. `delete_template`
删除模板。

**参数**：
- `setting_id` (必需): 模板 ID

**返回**：`{code, message, data: {...}}`

---

### 元信息工具

#### 19. `list_scenes`
列出所有可用的场景类型。

**返回**：`{code, message, data: ["ROBOT", "LLM", "CHAIN", ...]}`

#### 20. `list_factories`
列出指定场景下的所有工厂类型。

**参数**：
- `scene` (必需): 场景类型
- `type` (可选): 配置类型，`"draft"` | `"online"` | `"template"`，默认 `"draft"`

**返回**：`{code, message, data: {factory_names: ["RobotBrainDraftSetting", ...]}}`

---

## 配置引用说明

配置之间存在引用关系，通过以下结构表示：

```json
{
  "setting_id": 123,
  "category": "Draft"
}
```

- `setting_id`: 被引用配置的 ID（负数表示 batch 内的临时引用）
- `category`: `"Draft"` | `"Online"` | `"Template"`

**Batch 创建中的引用解析**：
1. 使用负数作为 `temp_id`（如 -1, -2）
2. 在 config 中通过 `{setting_id: -2, category: "Draft"}` 引用
3. 服务端自动解析并替换为真实 ID

---

## 响应格式

所有工具返回完整的 TFSResponse 格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

- `code`: HTTP 状态码
- `message`: 响应消息
- `data`: 实际数据

**错误处理**：
- MCP 透传服务端错误，不做额外处理
- 验证错误时，服务端返回格式化的错误详情（字段路径、期望值、实际值）

---

## 渐进式披露策略

**重要**：后端 API 不支持渐进式披露，始终返回完整 DTO。以下策略需要在 **MCP 层实现**。

### 1. 层级探索

按层级逐步获取信息：
- 先 `list_scenes()` 了解有哪些场景
- 再 `list_factories(scene)` 了解场景下的工厂类型
- 最后 `get_draft(setting_id)` 深入单个配置

### 2. 字段过滤

MCP 层实现可选的字段过滤：

```python
def _filter_dto(dto: DraftFactorySettingDto, verbose: bool = False) -> dict:
    """根据 verbose 参数过滤返回字段"""
    if verbose:
        return dto.model_dump()

    # 默认只返回关键字段
    return {
        "setting_id": dto.setting_id,
        "setting_name": dto.setting_name,
        "name": dto.name,
        "scene": dto.scene,
        "factory_version": dto.factory_version,
    }
```

### 3. 引用处理

- 引用始终以 `{setting_id, category}` 形式返回
- 如需获取被引用配置的详情，需要额外调用 `get_draft(setting_id)`
- 建议在 MCP 层提供可选的 `resolve_refs` 参数来自动解析引用

### 4. Schema 按需获取

- `get_draft` 返回的 DTO 始终包含 `config_schema`
- 如需了解工厂类型而不需要具体实例，使用 `get_factory_struct(scene, factoryName)`

---

## 示例配置

参考 `/Users/huruize/PycharmProjects/RobotEditMCP/机器人配置json.txt` 获取完整的配置示例，包含：
- Robot 配置（BRAIN, DRIVE, MEMORY）
- Chain 配置（思维链）
- LLM 配置（GPT）
- Prompt 配置
- DocStore 配置
- ConversationManager 配置

---

## 工具命名约定

采用 **动词优先** 风格：
- `list_*`: 列出集合
- `get_*`: 获取单个详情
- `create_*`: 创建新资源
- `update_*`: 更新资源
- `delete_*`: 删除资源
- `trigger_*`: 触发操作

## 参数命名约定

- 使用驼峰命名（camelCase）：`factoryName`, `settingName`, `templateSettingId`
- 与后端 API 保持一致

---

## 主要修正摘要

### 与后端 API 的关键差异

1. **release_draft**：发布整套草稿环境（无参数），而非单个草稿
2. **update_draft**：`setting_name` 是必需参数
3. **batch_create_drafts**：返回详细结果列表，而非简单映射
4. **clone_draft**：后端不存在此端点（已删除）
5. **apply_template**：不支持 `name` 参数
6. **Action 系统**：Actions 已包含在 DTO 的 `tfs_actions` 字段中
7. **参数命名**：使用 `factoryName` 而非 `factory`

### 不存在的特性

以下参数后端不支持，需要在 MCP 层实现：
- `expand_refs`：引用始终以 `{setting_id, category}` 返回
- `detail_level`：后端始终返回完整 DTO
- `include_schema`：schema 始终包含在 DTO 中

### 新增工具

- **get_factory_struct**：获取工厂类型结构信息（包含 schema 和 actions）
- **get_online_action_detail**：获取单个 Action 的详细信息（仅 Online）

### 认证方式

使用 `admin_key` header（与前端一致），而非标准的 `Authorization: Bearer`。
