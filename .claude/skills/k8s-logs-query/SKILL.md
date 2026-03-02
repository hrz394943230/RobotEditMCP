---
name: k8s-logs-query
description: 查询 Kubernetes Pod 日志以调试 API 调用问题。当需要分析 API 请求失败、追踪调用链路或查看 Robot 实例运行状态时使用。
---

# K8s 日志查询

## Quick start

最常见的用例：查询最近的 API 错误日志

```bash
# 查询前端/API 服务最近的错误日志
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep -i "error\|exception"

# 查询特定 Robot 实例的日志
kubectl logs --namespace=staging-tenant tfrobotserver-friday --tail=50 --kubeconfig={baseDir}/../cls-n9fgew8r-config
```

## Basic usage

### 核心模式：理解请求链路

根据网络拓扑（参考 [network-topology.md]({baseDir}/../docs/network-topology.md)），API 请求经过以下链路：

```
Client → CLB → Istio Ingress Gateway → Gateway → VirtualService → EnvoyFilter → Backend Service
```

**调试策略**：从入口到后端，逐层查询日志

#### Step 1: 检查入口网关日志

```bash
# 查看 Istio Ingress Gateway 日志（检查请求是否到达集群）
kubectl logs --namespace=istio-ingress -l app=istio-ingressgateway --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config
```

**预期输出**：包含 HTTP 请求记录，显示 Host、Path、Headers

#### Step 2: 检查租户 API 服务日志

```bash
# 查看 TFRobot 前端/API 服务日志
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config

# 过滤特定请求路径
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep "/v1/robot"
```

**预期输出**：API 请求处理记录，包含 200/4xx/5xx 状态码

#### Step 3: 检查 Robot 实例日志

```bash
# 查看特定 Robot 实例日志
kubectl logs --namespace=staging-tenant tfrobotserver-friday --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config
```

**预期输出**：Robot 实例的详细运行日志，包含配置加载、Socket.IO 连接等

### 环境配置

默认配置（从 [.env]({baseDir}/../../..env) 读取）：
- Kubeconfig: `{baseDir}/../cls-n9fgew8r-config`
- Namespace: `staging-tenant`
- Robot ID: `friday`

### 关键服务映射

| 服务 | DNS 名称 | 端口 | 查询命令 |
|------|----------|------|----------|
| TFRobot 前端/API | `tfrobotfront.staging-tenant.svc.cluster.local` | 3000 | `kubectl logs -n staging-tenant -l app=tfrobotfront --all-containers=true` |
| Robot 实例 | `tfrobotserver-friday.staging-tenant.svc.cluster.local` | 8080 | `kubectl logs -n staging-tenant tfrobotserver-friday` |
| Istio Gateway | `istio-ingressgateway.istio-ingress.svc.cluster.local` | 80 | `kubectl logs -n istio-ingress -l app=istio-ingressgateway` |

## Advanced usage

### 场景 1: 追踪完整请求链路

当 API 调用失败时，按以下顺序追踪：

```bash
# 1. 检查 Ingress Gateway（请求是否进入集群）
kubectl logs --namespace=istio-ingress -l app=istio-ingressgateway --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep "{request_path}"

# 2. 检查前端/API 服务（请求是否被路由）
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep "{request_id}"

# 3. 检查 Robot 实例（配置是否生效）
kubectl logs --namespace=staging-tenant tfrobotserver-friday --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep "{config_key}"
```

### 场景 2: 过滤时间范围

```bash
# 查看最近 10 分钟的日志
kubectl logs --namespace=staging-tenant tfrobotserver-friday --since=10m --kubeconfig={baseDir}/../cls-n9fgew8r-config

# 查看特定时间段（需要 jq 支持）
kubectl logs --namespace=staging-tenant tfrobotserver-friday --kubeconfig={baseDir}/../cls-n9fgew8r-config | \
  jq -r 'select(.timestamp >= "2026-03-02T10:00:00" and .timestamp <= "2026-03-02T11:00:00")'
```

### 场景 3: 多 Pod 日志聚合

```bash
# 当服务有多个 Pod 时，使用 -l 标签选择所有 Pod
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --tail=100 --all-containers=true --kubeconfig={baseDir}/../cls-n9fgew8r-config

# 实时流式查看所有 Pod 日志
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --follow=true --kubeconfig={baseDir}/../cls-n9fgew8r-config
```

### 场景 4: 调试路由问题

根据网络拓扑，EnvoyFilter 负责动态路由：

```bash
# 检查路由是否正确配置（查看 X-TF-Namespace 和 X-TF-RobotId Headers）
kubectl logs --namespace=istio-ingress -l app=istio-ingressgateway --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | \
  grep -i "X-TF-Namespace\|X-TF-RobotId"
```

## 常见问题诊断

### 问题: 401 Unauthorized

**可能原因**：缺少 Cookie 或 Header

**诊断命令**：
```bash
# 检查 Ingress Gateway 是否收到必要的 Headers
kubectl logs --namespace=istio-ingress -l app=istio-ingressgateway --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep "401"
```

**解决方案**：确保请求包含 `adminToken` Cookie 或 `X-TF-Namespace` Header

### 问题: 502 Bad Gateway

**可能原因**：后端服务不可达

**诊断命令**：
```bash
# 检查后端 Pod 状态
kubectl get pods --namespace=staging-tenant --kubeconfig={baseDir}/../cls-n9fgew8r-config

# 检查 Pod 日志中的错误
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true --tail=100 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep -i "error\|exception"
```

### 问题: 配置未生效

**可能原因**：Draft 未发布或 Robot 实例未重启

**诊断命令**：
```bash
# 查看 Robot 实例启动日志，检查配置加载时间
kubectl logs --namespace=staging-tenant tfrobotserver-friday --tail=200 --kubeconfig={baseDir}/../cls-n9fgew8r-config | grep -i "config\|reload"
```

## 最佳实践

### 1. 使用标签而非 Pod 名称

```bash
# ✅ 推荐：使用标签选择器
kubectl logs --namespace=staging-tenant -l app=tfrobotfront --all-containers=true

# ❌ 避免：直接使用 Pod 名称（Pod 可能重建）
kubectl logs --namespace=staging-tenant tfrobotfront-7fc8b4b9d7-jzdjj
```

### 2. 实时日志流用于调试

```bash
# 实时查看日志（Ctrl+C 退出）
kubectl logs --namespace=staging-tenant tfrobotserver-friday --follow=true --kubeconfig={baseDir}/../cls-n9fgew8r-config
```

### 3. 组合 grep 和 jq 进行高级过滤

```bash
# 查找特定 JSON 字段
kubectl logs --namespace=staging-tenant tfrobotserver-friday --kubeconfig={baseDir}/../cls-n9fgew8r-config | \
  jq -r 'select(.level == "ERROR") | .message'
```

## 参考资源

- 网络拓扑: [docs/network-topology.md]({baseDir}/../docs/network-topology.md)
- 环境配置: [.env]({baseDir}/../../.env)
- K8s 配置文件: `{baseDir}/../cls-n9fgew8r-config`
- RobotEditMCP 项目结构: [CLAUDE.md]({baseDir}/../../CLAUDE.md)
