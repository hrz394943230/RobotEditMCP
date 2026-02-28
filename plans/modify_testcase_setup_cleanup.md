# RobotEditMCP 集成测试 Setup & Cleanup 规格文档

## 概述

为 `/Users/huruize/PycharmProjects/RobotEditMCP/tests/api` 的集成测试添加完整的 setup 和 cleanup 机制。这些测试对真实 API 进行操作，需要确保每个测试用例执行后恢复到初始状态，避免残留数据影响其他测试。

## 设计原则

基于用户访谈确定的架构决策：

1. **测试隔离**: 每个测试函数完全独立，支持并行执行（pytest-xdist）
2. **自动清理**: 使用基类自动追踪资源，测试失败时也总是清理
3. **明确性**: 显式调用清理方法，代码注释说明行为
4. **简单性**: 默认行为不需要配置，不支持复杂的条件清理
5. **可靠性**: 清理失败时记录警告，不阻塞测试，提供组合恢复策略

## 架构设计

### 1. 基类结构

创建 `BaseRobotTest` 基类，提供统一的 setup/cleanup 功能：

```python
# tests/api/base_test.py
import logging
from typing import Dict, List, Optional
from roboteditmcp.client import RobotClient

logger = logging.getLogger(__name__)

class BaseRobotTest:
    """集成测试基类，提供自动资源追踪和清理功能。"""

    # 资源类型
    RESOURCE_DRAFT = "draft"
    RESOURCE_TEMPLATE = "template"
    RESOURCE_ONLINE = "online"

    # 测试资源命名前缀
    RESOURCE_PREFIX = "mcp_test_"

    def setup_method(self):
        """每个测试方法执行前的 setup。"""
        self._client: Optional[RobotClient] = None
        self._resources: Dict[str, List[int]] = {
            self.RESOURCE_DRAFT: [],
            self.RESOURCE_TEMPLATE: [],
            self.RESOURCE_ONLINE: [],
        }
        self._resource_counter: int = 0

    def teardown_method(self):
        """每个测试方法执行后的 cleanup。

        使用 LIFO 顺序清理资源（后创建先删除）。
        清理失败时记录警告，不抛出异常。
        """
        errors = []

        # LIFO 顺序：按类型倒序清理（template -> draft -> online）
        for resource_type in [self.RESOURCE_TEMPLATE, self.RESOURCE_DRAFT, self.RESOURCE_ONLINE]:
            resource_ids = self._resources.get(resource_type, [])

            # LIFO：从后往前删除
            for resource_id in reversed(resource_ids):
                try:
                    self._delete_resource(resource_type, resource_id)
                    logger.info(f"清理成功: {resource_type} id={resource_id}")
                except Exception as e:
                    error_msg = f"清理失败: {resource_type} id={resource_id}, error={e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

        # 报告清理错误
        if errors:
            logger.warning(f"清理完成但有 {len(errors)} 个错误:")
            for error in errors:
                logger.warning(f"  - {error}")

            # 生成手动清理建议
            self._generate_cleanup_report(errors)

    def _delete_resource(self, resource_type: str, resource_id: int):
        """删除指定类型的资源。"""
        if resource_type == self.RESOURCE_DRAFT:
            self.client.draft.delete_draft(resource_id)
        elif resource_type == self.RESOURCE_TEMPLATE:
            self.client.template.delete_template(resource_id)
        elif resource_type == self.RESOURCE_ONLINE:
            # Online 配置通常不支持直接删除
            logger.warning(f"Online 资源不支持删除: id={resource_id}")

    def _generate_cleanup_report(self, errors: List[str]):
        """生成清理失败的报告，包含手动清理命令。"""
        logger.warning("=" * 60)
        logger.warning("清理失败报告 - 手动清理建议:")
        logger.warning("=" * 60)

        for resource_type, ids in self._resources.items():
            if ids:
                ids_str = ", ".join(map(str, ids))
                logger.warning(f"  {resource_type}: [{ids_str}]")

        logger.warning("=" * 60)

    @property
    def client(self) -> RobotClient:
        """获取 RobotClient 实例（延迟初始化）。"""
        if self._client is None:
            self._client = RobotClient()
        return self._client

    def _generate_resource_name(self, suffix: str = "") -> str:
        """生成唯一的测试资源名称。

        格式: mcp_test_<类名>_<计数器>_<后缀>

        示例: mcp_test_TestDraftAPI_001_create
        """
        class_name = self.__class__.__name__
        self._resource_counter += 1
        counter_str = str(self._resource_counter).zfill(3)

        parts = [self.RESOURCE_PREFIX, class_name, counter_str]
        if suffix:
            parts.append(suffix)

        return "_".join(parts)

    def _track_resource(self, resource_type: str, resource_id: int):
        """追踪创建的资源，用于后续清理。"""
        if resource_type in self._resources:
            self._resources[resource_type].append(resource_id)
            logger.info(f"追踪资源: {resource_type} id={resource_id}")

    def _verify_resource_created(self, response: dict, expected_key: str = "settingId") -> int:
        """验证资源创建成功，返回资源 ID。

        执行基本存在性验证：
        - 检查响应不为 None
        - 检查包含预期的 ID 字段
        - ID 值不为空

        Raises:
            AssertionError: 验证失败
        """
        assert response is not None, "创建响应不应为 None"

        # 尝试多种可能的 ID 字段名
        possible_keys = [expected_key, expected_key.lower(), "id"]
        resource_id = None

        for key in possible_keys:
            if key in response:
                resource_id = response[key]
                break

        assert resource_id is not None, f"响应应包含资源 ID (检查字段: {possible_keys})"
        assert resource_id, f"资源 ID 不应为空: {resource_id}"

        logger.info(f"资源创建验证成功: id={resource_id}")
        return resource_id

    # ===== 创建方法 =====

    def create_draft(
        self,
        scene: str,
        name: str,
        setting_name: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> int:
        """创建草稿配置并自动追踪。

        Args:
            scene: 场景名称
            name: 工厂名称
            setting_name: 配置名称（可选，默认自动生成）
            config: 配置内容（可选）

        Returns:
            创建的草稿 ID
        """
        if setting_name is None:
            setting_name = self._generate_resource_name("draft")

        if config is None:
            config = {}

        response = self.client.draft.create_draft(
            scene=scene,
            name=name,
            setting_name=setting_name,
            config=config,
        )

        draft_id = self._verify_resource_created(response)
        self._track_resource(self.RESOURCE_DRAFT, draft_id)
        return draft_id

    def create_template(self, draft_id: int, name: Optional[str] = None) -> int:
        """从草稿创建模板并自动追踪。

        Args:
            draft_id: 源草稿 ID
            name: 模板名称（可选，默认自动生成）

        Returns:
            创建的模板 ID
        """
        if name is None:
            name = self._generate_resource_name("template")

        response = self.client.draft.save_as_template(
            draft_id=draft_id,
            name=name,
        )

        template_id = self._verify_resource_created(response, "templateId")
        self._track_resource(self.RESOURCE_TEMPLATE, template_id)
        return template_id

    def create_draft_from_template(self, template_id: int) -> int:
        """从模板创建草稿并自动追踪。

        Args:
            template_id: 模板 ID

        Returns:
            创建的草稿 ID
        """
        response = self.client.template.apply_template(
            templateSettingId=template_id
        )

        draft_id = self._verify_resource_created(response, "draftId")
        self._track_resource(self.RESOURCE_DRAFT, draft_id)
        return draft_id

    def batch_create_drafts(self, drafts: List[dict]) -> List[int]:
        """批量创建草稿并自动追踪。

        Args:
            drafts: 草稿配置列表

        Returns:
            创建的草稿 ID 列表
        """
        response = self.client.draft.batch_create_drafts(drafts)

        # 提取所有创建的 ID 并追踪
        draft_ids = []
        results = response.results if hasattr(response, 'results') else []

        for result in results:
            draft_id = self._verify_resource_created(result)
            self._track_resource(self.RESOURCE_DRAFT, draft_id)
            draft_ids.append(draft_id)

        return draft_ids

    # ===== 清理方法 =====

    def cleanup_all(self):
        """手动触发清理所有追踪的资源。

        通常不需要调用此方法，teardown 会自动清理。
        仅在特殊情况下使用（如测试中途需要清理状态）。
        """
        self.teardown_method()
```

### 2. 测试文件改造示例

```python
# tests/api/test_draft.py（改造后）
"""集成测试 - Draft API 端点。"""

import pytest
from .base_test import BaseRobotTest


@pytest.fixture
def client(env_vars):
    """创建 RobotClient 实例用于测试。"""
    from roboteditmcp.client import RobotClient
    return RobotClient()


@pytest.fixture
def sample_config(client):
    """从 API 获取示例配置用于测试数据生成。"""
    drafts = client.draft.list_drafts()
    if not drafts:
        pytest.skip("系统中没有可用的草稿配置")
    return drafts[0]


class TestDraftAPI(BaseRobotTest):
    """Draft API 端点测试用例。"""

    def test_list_drafts(self):
        """测试 GET /factory/drafts/query - 列出草稿配置。"""
        response = self.client.draft.list_drafts()
        assert isinstance(response, list), "响应应为列表"

    def test_get_draft(self, sample_config):
        """测试 GET /factory/drafts/:settingId - 获取单个草稿。"""
        draft_id = sample_config.get('settingId') or sample_config.get('id')
        response = self.client.draft.get_draft(draft_id)
        assert isinstance(response, dict), "响应应为字典"

    def test_create_draft(self, sample_config):
        """测试 POST /factory/drafts - 创建新草稿。

        验证:
        - 端点创建新草稿成功
        - 响应包含草稿详情
        - teardown 自动清理
        """
        scene = sample_config.get('scene')
        factory_name = sample_config.get('name')

        # 使用基类方法创建（自动追踪和清理）
        draft_id = self.create_draft(
            scene=scene,
            name=factory_name,
            config={"test": "value"},
        )

        # 验证创建成功
        assert draft_id is not None
        assert draft_id > 0

    def test_update_draft(self, sample_config):
        """测试 PUT /factory/drafts/:settingId - 更新草稿。

        验证:
        - 端点更新草稿配置成功
        - 响应包含更新后的草稿详情
        - teardown 自动清理测试数据
        """
        # 创建用于更新的测试草稿
        scene = sample_config.get('scene')
        factory_name = sample_config.get('name')
        draft_id = self.create_draft(scene=scene, name=factory_name)

        # 执行更新
        response = self.client.draft.update_draft(
            setting_id=draft_id,
            setting_name="test_updated",
            config={"test": "updated_value"},
        )

        assert isinstance(response, dict), "响应应为字典"

    def test_delete_draft(self, sample_config):
        """测试 DELETE /factory/drafts/:settingId - 删除草稿。

        验证:
        - 端点删除草稿成功
        - teardown 不会重复删除（已从追踪列表移除）
        """
        # 创建用于删除的测试草稿
        scene = sample_config.get('scene')
        factory_name = sample_config.get('name')
        draft_id = self.create_draft(scene=scene, name=factory_name)

        # 从追踪列表移除（因为我们要手动测试删除）
        self._resources[self.RESOURCE_DRAFT].remove(draft_id)

        # 执行删除
        response = self.client.draft.delete_draft(draft_id)
        assert isinstance(response, dict), "删除响应应为字典"

    def test_batch_create_drafts(self, sample_config):
        """测试 POST /factory/drafts/batch - 批量创建草稿。

        验证:
        - 端点处理批量创建
        - 响应包含批量结果
        - teardown 逐个清理所有创建的草稿
        """
        scene = sample_config.get('scene')
        factory_name = sample_config.get('name')

        # 使用基类方法批量创建（自动追踪和清理）
        draft_ids = self.batch_create_drafts([
            {
                "temp_id": -1,
                "draft": {
                    "scene": scene,
                    "name": factory_name,
                    "settingName": "test_batch_1",
                    "config": {"test": "1"},
                },
            },
            {
                "temp_id": -2,
                "draft": {
                    "scene": scene,
                    "name": factory_name,
                    "settingName": "test_batch_2",
                    "config": {"test": "2"},
                },
            },
        ])

        # 验证批量创建成功
        assert len(draft_ids) == 2
        assert all(did > 0 for did in draft_ids)
```

## 实现细节

### 资源命名规范

| 组件 | 格式 | 示例 |
|------|------|------|
| 前缀 | `mcp_test_` | 固定 |
| 类名 | 测试类名 | `TestDraftAPI` |
| 计数器 | 3 位数字 | `001`, `002`, `003` |
| 后缀 | 可选描述 | `create`, `update`, `delete` |

完整示例: `mcp_test_TestDraftAPI_001_create`

### 清理顺序（LIFO）

1. 模板（Template）- 可能有依赖关系
2. 草稿（Draft）
3. 在线配置（Online）- 通常不支持删除

### 错误处理策略

1. **清理失败**: 记录警告日志，继续清理其他资源
2. **清理报告**: 在测试结束时汇总所有错误
3. **手动清理建议**: 生成清理失败的资源列表
4. **不阻塞测试**: 清理错误不影响测试结果

### 并发支持

- 使用类名 + 计数器确保资源名称唯一
- 每个测试独立创建和清理资源
- 支持 `pytest-xdist` 的 `-n` 参数并行执行

## 使用示例

### 基本测试

```python
class TestMyAPI(BaseRobotTest):
    def test_something(self):
        # 创建资源（自动追踪）
        draft_id = self.create_draft(scene="ROBOT", name="MyFactory")

        # 测试逻辑
        response = self.client.draft.get_draft(draft_id)
        assert response is not None

        # teardown 会自动清理，无需手动删除
```

### 自定义清理

```python
def test_manual_cleanup(self):
    draft_id = self.create_draft(...)

    # 手动从追踪列表移除
    self._resources[self.RESOURCE_DRAFT].remove(draft_id)

    # 手动删除并测试
    response = self.client.draft.delete_draft(draft_id)
    assert response is not None
```

### 批量操作

```python
def test_batch(self):
    # 批量创建（自动追踪所有 ID）
    draft_ids = self.batch_create_drafts([...])

    # teardown 会逐个清理所有创建的草稿
    assert len(draft_ids) == 3
```

## 迁移步骤

1. 创建 `tests/api/base_test.py` 基类
2. 更新 `test_draft.py` 继承 `BaseRobotTest`
3. 移除内联的 cleanup 代码
4. 移除测试编号前缀（test_1_, test_2_, ...）
5. 更新 `test_template.py` 和 `test_online.py`
6. 运行测试验证 cleanup 正常工作
7. 配置 CI/CD 添加清理失败报告检查

## 注意事项

1. **在线配置删除**: Online 配置通常不支持直接删除，只记录警告
2. **资源 ID 字段**: 不同 API 返回的 ID 字段名可能不同（settingId, templateId, id）
3. **测试失败保留**: 当前设计总是清理，需要调试时可临时注释掉 `teardown_method`
4. **并发执行**: 确保资源命名唯一，避免并行测试冲突
5. **日志级别**: 设置 `ROBOT_LOG_LEVEL=DEBUG` 查看详细的 cleanup 日志

## 未来扩展

- [ ] 支持配置化的清理行为（环境变量控制）
- [ ] 添加清理失败的统计和报告
- [ ] 实现资源依赖关系的智能排序
- [ ] 添加测试资源清理的 CLI 命令
- [ ] 支持测试数据工厂模式