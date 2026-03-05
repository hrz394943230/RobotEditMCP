# PyPI 发布指南

本文档说明如何将 RobotEditMCP 发布到 PyPI。

## 发布流程概览

RobotEditMCP 使用 GitHub Actions 自动化发布流程到 PyPI。当推送以 `v` 开头的版本标签时（例如 `v0.1.0`），GitHub Actions 会自动：

1. 运行代码检查 (lint)
2. 运行测试套件
3. 构建分发包
4. 发布到 PyPI

## 发布前准备

### 1. 配置 PyPI 信任的发布者

首次发布需要在 PyPI 上配置信任的发布者（Trusted Publishers）：

1. 访问 [PyPI](https://pypi.org) 并登录
2. 进入您的账户设置 -> Publishing
3. 添加以下 GitHub Actions 配置：
   - **PyPI Project Name**: `roboteditmcp`
   - **Owner**: `huruize` (您的 GitHub 用户名)
   - **Repository name**: `RobotEditMCP`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

这样配置后，GitHub Actions 可以使用 OIDC 认证自动发布，无需存储 PyPI API token。

### 2. 配置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets (Settings -> Secrets and variables -> Actions):

- `ROBOT_ADMIN_TOKEN` - Robot API 认证令牌 (用于测试)
- `ROBOT_BASE_URL` - Robot API 基础 URL (用于测试)
- `TF_NAMESPACE` - Kubernetes 命名空间 (用于测试)
- `TF_ROBOT_ID` - Robot 实例 ID (用于测试)

这些 Secrets 仅用于运行测试环境验证。

## 发布新版本

### 步骤 1: 更新版本号

编辑 `pyproject.toml` 文件，更新版本号：

```toml
[project]
version = "0.1.1"  # 更新到新版本
```

### 步骤 2: 更新 CHANGELOG (可选)

建议在 README.md 或创建 CHANGELOG.md 中记录版本变更。

### 步骤 3: 提交代码

```bash
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git push
```

### 步骤 4: 创建并推送标签

```bash
# 使用 Makefile 命令
make tag

# 或手动创建
git tag v0.1.1
git push origin v0.1.1
```

### 步骤 5: 等待 GitHub Actions

推送标签后，GitHub Actions 会自动触发发布流程。您可以在这里查看进度：

```
https://github.com/huruize/RobotEditMCP/actions
```

### 步骤 6: 验证发布

发布成功后，在 PyPI 上验证：

```
https://pypi.org/project/roboteditmcp/
```

## 本地测试发布

在正式发布前，可以本地测试构建：

```bash
# 构建分发包
make build

# 检查生成的文件
ls -lh dist/

# (可选) 发布到 TestPyPI 进行测试
uv run twine upload --repository testpypi dist/*
```

## Makefile 命令

- `make build` - 构建分发包
- `make publish` - 手动发布到 PyPI (需要配置 TWINE_USERNAME 和 TWINE_PASSWORD)
- `make tag` - 创建并推送版本标签

## 版本号规范

遵循语义化版本 (Semantic Versioning):

- **主版本号 (MAJOR)**: 不兼容的 API 变更
- **次版本号 (MINOR)**: 向下兼容的功能新增
- **修订号 (PATCH)**: 向下兼容的问题修复

示例: `v1.2.3`

## 回滚发布

如果发布出现问题，可以通过 PyPI Web 界面手动删除版本，或发布新版本修复问题。

注意: PyPI 不允许覆盖已存在的版本号，如有问题需要发布新版本。

## 参考资源

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publish](https://github.com/pypa/gh-action-pypi-publish)
- [Semantic Versioning](https://semver.org/)
