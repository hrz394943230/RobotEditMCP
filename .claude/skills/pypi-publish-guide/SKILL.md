---
name: pypi-publish-guide
description: Python 项目发布到 PyPI 的完整操作指南和规范。包含版本号管理、发布前检查、GitHub Actions 自动发布流程、以及发布后验证。当需要发布新版本或了解发布规范时使用。
---

# PyPI 发布规范指南

本指南基于项目的 GitHub Actions 自动发布流程，提供完整的 PyPI 发布操作规范。

## Quick start

⚠️ **重要提醒**：在创建版本标签前，**必须**在本地运行 `make lint` 和 `make test`，确保所有检查通过后才能推送标签。这是避免发布失败的最佳实践。

快速发布新版本到 PyPI（3 分钟）：

```bash
# 0. 【必须】发布前本地检查
make lint           # 确保代码格式检查通过
make test           # 确保所有测试通过

# 1. 确保在主分支且代码已提交
git status
git checkout main
git pull origin main

# 2. 更新 pyproject.toml 中的版本号
# 例如：version = "0.1.0" -> version = "0.1.1"

# 3. 提交版本更新
git add pyproject.toml
git commit -m "Bump version to 0.1.1"

# 4. 创建并推送版本标签（触发自动发布）
make tag
# 输入版本号：v0.1.1
```

GitHub Actions 将自动执行：代码检查 → 测试 → 构建 → 发布到 PyPI

## Basic usage

### 版本号规范

使用语义化版本号（Semantic Versioning）：

```
v主版本号.次版本号.修订号 (vX.Y.Z)

主版本号 (X)：不兼容的 API 变更
次版本号 (Y)：向后兼容的新功能
修订号 (Z)：向后兼容的问题修复
```

示例：
- `v0.1.0` → `v0.1.1`：修复 bug
- `v0.1.1` → `v0.2.0`：新增功能
- `v0.2.0` → `v1.0.0`：破坏性变更

### 发布前检查清单

⚠️ **发布前强制要求**：在创建版本标签**之前**，必须在本地完成以下检查：

```bash
# 必须在本地执行并确保通过
make lint           # 代码格式检查必须通过
make test           # 所有测试必须通过
```

> **为什么要在本地先检查？**
> - GitHub Actions 在测试失败时会停止发布，导致发布失败
> - 本地先检查可以快速发现和修复问题，避免浪费 CI 时间
> - 这是团队协作的最佳实践，确保发布的代码质量

在创建版本标签前，确保：

- [ ] **本地运行 `make lint` 并通过** ⚠️ 必须完成
- [ ] **本地运行 `make test` 并通过** ⚠️ 必须完成
- [ ] 所有更改已提交到主分支
- [ ] 更新了 [pyproject.toml](../pyproject.toml) 中的版本号
- [ ] 更新了 [CHANGELOG.md](../CHANGELOG.md)（如果存在）
- [ ] 构建成功：`make build`（可选，GitHub Actions 也会执行）

### 发布流程

#### 标准发布流程

1. **更新版本号**

编辑 [pyproject.toml](../pyproject.toml) 第 3 行：
```toml
version = "0.1.0"  # 修改为新版本
```

2. **提交版本更新**

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.1"
```

3. **创建版本标签**

```bash
# 使用 make 命令（推荐）
make tag

# 或手动创建
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

4. **监控自动发布**

访问 GitHub Actions 查看 [.github/workflows/publish.yml](../.github/workflows/publish.yml) 执行状态：
```
https://github.com/huruize/RobotEditMCP/actions
```

## Advanced usage

### 本地测试发布

在正式发布前，可以测试发布到 TestPyPI：

```bash
# 1. 构建
uv build

# 2. 检查构建产物
ls -lh dist/

# 3. 发布到 TestPyPI（需配置 TEST_PYPI_API_TOKEN）
uv run twine upload --repository testpypi dist/*

# 4. 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ roboteditmcp
```

### 回滚发布

如果发布出现问题：

1. **从 PyPI 删除版本**（仅限发布后 72 小时内）
   - 登录 https://pypi.org/manage/
   - 找到项目并删除有问题的版本

2. **修复问题并重新发布**
   ```bash
   # 修复后使用新版本号
   # 例如：v0.1.1 -> v0.1.2
   ```

3. **YANK 版本**（推荐）
   - 在 PyPI 上标记版本为 yanked
   - pip 安装时会跳过此版本

### 手动发布（不推荐）

如果 GitHub Actions 失败，可以手动发布：

```bash
# 1. 构建
uv build

# 2. 检查构建内容
tar -tzf dist/*.tar.gz

# 3. 发布到 PyPI（需配置 PYPI_API_TOKEN）
uv run twine upload dist/*
```

## 发布后验证

### 验证步骤

1. **检查 PyPI 页面**
   ```
   https://pypi.org/p/roboteditmcp
   ```

2. **验证安装**
   ```bash
   # 创建新的虚拟环境
   python -m venv /tmp/test_env
   source /tmp/test_env/bin/activate

   # 安装新版本
   pip install roboteditmcp

   # 验证版本
   roboteditmcp --version
   ```

3. **验证功能**
   ```bash
   # 运行基本功能测试
   roboteditmcp --help
   ```

## GitHub Actions 工作流

项目的自动发布流程定义在 [.github/workflows/publish.yml](../.github/workflows/publish.yml)：

### 触发条件

```yaml
on:
  push:
    tags:
      - 'v*.*.*'  # 匹配 v0.1.0, v1.2.3 等
```

### 发布流程

1. **代码检查** → `make lint`
2. **运行测试** → `make test`
3. **构建包** → `uv build`
4. **发布到 PyPI** → 使用 OIDC 认证自动发布

### 环境变量配置

GitHub Secrets 需配置（已在项目中配置）：
- `ROBOT_ADMIN_TOKEN` - 测试环境认证
- `ROBOT_BASE_URL` - 测试 API 地址
- `TF_NAMESPACE` - Kubernetes 命名空间
- `TF_ROBOT_ID` - Robot 实例 ID

## 常见问题

### Q: 发布失败怎么办？

1. 检查 GitHub Actions 日志
2. 确认版本号是否已存在于 PyPI
3. 验证 `pyproject.toml` 配置正确
4. 使用 `skip-existing: true` 跳过已存在版本

### Q: 如何撤销已发布的版本？

- 发布后 72 小时内可在 PyPI 管理后台删除
- 超过 72 小时可使用 yank 功能标记版本
- 最好的方式是发布新版本修复问题

### Q: 版本号冲突怎么办？

GitHub Actions 使用 `skip-existing: true`，如果版本已存在会跳过。需要：
1. 删除旧标签：`git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0`
2. 更新版本号
3. 重新创建标签

### Q: 测试未通过能否发布？

**不能。** GitHub Actions 工作流会在测试或 lint 失败时停止，不会发布到 PyPI。这是安全机制。

**最佳实践**：在推送标签前，先在本地运行 `make lint` 和 `make test` 确保通过。这样可以：
- 快速发现并修复问题
- 避免 CI/CD 资源浪费
- 确保发布一次性成功

## 相关资源

- 项目配置：[pyproject.toml](../pyproject.toml)
- 发布工作流：[.github/workflows/publish.yml](../.github/workflows/publish.yml)
- 构建命令：[Makefile](../Makefile) (第 66-80 行)
- PyPI 项目页面：https://pypi.org/p/roboteditmcp
- 语义化版本规范：https://semver.org/lang/zh-CN/
- PyPI 发布指南：https://packaging.python.org/tutorials/packaging-projects/
