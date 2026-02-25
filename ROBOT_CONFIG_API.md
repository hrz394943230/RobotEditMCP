# 机器人配置 API 接口文档

## 概述

本文档描述了 TFRobotServer 中用于管理机器人配置的所有 API 接口。机器人配置分为三种类型：

- **草稿配置 (Draft)**: 用于编辑和测试的配置，支持完整的 CRUD 操作
- **在线配置 (Online)**: 正在运行的机器人配置，仅支持查询和触发 Action
- **模板配置 (Template)**: 可复用的配置模板，支持查询、应用和删除

**基础路径**: `/v1/factory`

---

## 通用响应格式

所有接口的响应格式统一如下：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

---

## 一、草稿配置接口 (Draft Settings)

草稿配置是主要的编辑区域，支持创建、更新、删除和发布操作。

### 1.1 查询接口

#### 1.1.1 获取所有场景

```
GET /v1/factory/drafts/scenes
```

**描述**: 获取所有草稿配置的构建场景

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": ["robot", "chain", "memory", "llm"]
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:52`

---

#### 1.1.2 获取指定场景下的工厂列表

```
GET /v1/factory/drafts/{scene}/factories
```

**路径参数**:
- `scene` (string): 场景名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "factory_names": ["Brain", "Chain", "Memory", "LLM"]
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:64`

---

#### 1.1.3 获取工厂配置结构

```
GET /v1/factory/drafts/struct/{scene}/{factory_name}
```

**路径参数**:
- `scene` (string): 场景名称
- `factory_name` (string): 工厂名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "scene": "robot",
    "factory_name": "Brain",
    "config_schema": {
      "type": "object",
      "properties": {
        "model": {"type": "string"},
        "temperature": {"type": "number"}
      }
    }
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:77`

---

#### 1.1.4 查询草稿配置列表

```
GET /v1/factory/drafts/query
```

**查询参数**:
- `scene` (string, 可选): 场景名称
- `factoryName` (string, 可选): 工厂名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "scene": "robot",
      "name": "Brain",
      "setting_name": "默认大脑配置",
      "config": {
        "model": "gpt-4",
        "temperature": 0.7
      }
    }
  ]
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:96`

---

#### 1.1.5 获取单个草稿配置

```
GET /v1/factory/drafts/{setting_id}
```

**路径参数**:
- `setting_id` (integer): 草稿配置ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "scene": "robot",
    "name": "Brain",
    "setting_name": "默认大脑配置",
    "config": {
      "model": "gpt-4",
      "temperature": 0.7
    }
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:114`

---

### 1.2 修改接口 (核心接口)

#### 1.2.1 创建草稿配置

```
POST /v1/factory/drafts/
```

**描述**: 创建新的草稿配置

**请求体** (Body):
```json
{
  "draftInfo": {
    "scene": "robot",
    "name": "Brain",
    "setting_name": "新大脑配置",
    "config": {
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
}
```

**字段说明**:
- `scene`: 场景名称（必需）
- `name`: 工厂名称（必需）
- `setting_name`: 配置名称（必需）
- `config`: 配置对象（必需）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "scene": "robot",
    "name": "Brain",
    "setting_name": "新大脑配置",
    "config": {
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
}
```

**错误响应** (500):
```json
{
  "code": 500,
  "message": "Config duplicate",
  "data": {}
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:129`

---

#### 1.2.2 批量创建草稿配置

```
POST /v1/factory/drafts/batch
```

**描述**: 批量创建多个相互关联的草稿配置节点。支持复制粘贴场景，使用临时ID处理节点间的引用关系。

**请求体** (Body):
```json
{
  "batchRequest": {
    "drafts": [
      {
        "temp_id": -1,
        "draft": {
          "scene": "robot",
          "name": "Brain",
          "setting_name": "主大脑",
          "config": {
            "chain": {
              "setting_id": -2,
              "category": "Draft"
            }
          }
        }
      },
      {
        "temp_id": -2,
        "draft": {
          "scene": "chain",
          "name": "Chain",
          "setting_name": "对话链",
          "config": {
            "steps": ["step1", "step2"]
          }
        }
      }
    ]
  }
}
```

**字段说明**:
- `temp_id`: 临时ID（建议使用负数），用于标识节点
- `draft`: 草稿配置对象
  - `config` 中的 `setting_id` 可以引用临时ID，系统会自动替换为真实ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "index": 0,
        "success": true,
        "setting_id": 123,
        "setting_dto": {
          "id": 123,
          "scene": "robot",
          "name": "Brain",
          "setting_name": "主大脑",
          "config": {
            "chain": {
              "setting_id": 124,
              "category": "Draft"
            }
          }
        },
        "error_message": null
      },
      {
        "index": 1,
        "success": true,
        "setting_id": 124,
        "setting_dto": {
          "id": 124,
          "scene": "chain",
          "name": "Chain",
          "setting_name": "对话链",
          "config": {
            "steps": ["step1", "step2"]
          }
        },
        "error_message": null
      }
    ],
    "success_count": 2,
    "failure_count": 0,
    "total_count": 2
  }
}
```

**工作流程**:
1. 用户在前端选中多个节点并复制
2. 前端为每个节点分配临时ID（如负数：-1, -2, -3...）
3. 前端提取节点配置，配置中的SettingID引用使用临时ID
4. 后端首先创建所有节点，建立临时ID到真实ID的映射
5. 后端递归扫描每个节点的配置，自动将临时ID替换为真实ID
6. 后端更新所有节点的配置，完成依赖关系的建立
7. 返回每个节点的创建结果

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:164`

---

#### 1.2.3 更新草稿配置 ⭐

```
PUT /v1/factory/drafts/{setting_id}
```

**描述**: 更新现有草稿配置的名称和配置内容（最常用的修改接口）

**路径参数**:
- `setting_id` (integer): 草稿配置ID

**请求体** (Body):
```json
{
  "draftInfo": {
    "setting_name": "更新后的配置名称",
    "config": {
      "model": "gpt-4-turbo",
      "temperature": 0.8,
      "max_tokens": 3000,
      "new_field": "新字段值"
    }
  }
}
```

**字段说明**:
- `setting_name`: 新的配置名称（可选）
- `config`: 新的配置对象（必需）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "scene": "robot",
    "name": "Brain",
    "setting_name": "更新后的配置名称",
    "config": {
      "model": "gpt-4-turbo",
      "temperature": 0.8,
      "max_tokens": 3000,
      "new_field": "新字段值"
    }
  }
}
```

**使用示例 (cURL)**:
```bash
curl -X PUT "http://localhost:8000/v1/factory/drafts/123" \
  -H "Content-Type: application/json" \
  -d '{
    "draftInfo": {
      "setting_name": "生产环境配置",
      "config": {
        "model": "gpt-4-turbo",
        "temperature": 0.8,
        "max_tokens": 3000
      }
    }
  }'
```

**使用示例 (Python)**:
```python
import requests

url = "http://localhost:8000/v1/factory/drafts/123"
payload = {
    "draftInfo": {
        "setting_name": "生产环境配置",
        "config": {
            "model": "gpt-4-turbo",
            "temperature": 0.8,
            "max_tokens": 3000
        }
    }
}

response = requests.put(url, json=payload)
result = response.json()

if result["code"] == 200:
    print("配置更新成功!")
    print(f"配置ID: {result['data']['id']}")
    print(f"配置名称: {result['data']['setting_name']}")
else:
    print(f"更新失败: {result['message']}")
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:265`

---

#### 1.2.4 触发草稿配置 Action

```
PUT /v1/factory/drafts/{setting_id}/action/{action}
```

**描述**: 在草稿配置中触发指定的 Action 操作

**路径参数**:
- `setting_id` (integer): 草稿配置ID
- `action` (string): Action名称

**请求体** (Body, 可选):
```json
{
  "param1": "value1",
  "param2": "value2"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "action executed successfully"
  }
}
```

**使用示例**:
```bash
# 重启机器人
curl -X PUT "http://localhost:8000/v1/factory/drafts/123/action/restart" \
  -H "Content-Type: application/json" \
  -d '{}'

# 执行带参数的Action
curl -X PUT "http://localhost:8000/v1/factory/drafts/123/action/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "advanced",
    "timeout": 60
  }'
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:302`

---

### 1.3 删除接口

#### 1.3.1 删除草稿配置

```
DELETE /v1/factory/drafts/{setting_id}
```

**路径参数**:
- `setting_id` (integer): 草稿配置ID

**描述**: 删除草稿配置，系统会：
1. 查询所有引用此草稿的其它草稿配置
2. 在其它草稿配置中删除此草稿的引用
3. 删除草稿配置

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:284`

---

### 1.4 发布接口

#### 1.4.1 发布草稿配置

```
POST /v1/factory/drafts/release
```

**描述**: 将草稿配置发布为在线配置

**发布条件**:
1. 草稿配置有可用Robot配置
2. 满足上线条件

**请求体**: 无

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "onlineRobotId": 456
  }
}
```

**使用示例**:
```bash
curl -X POST "http://localhost:8000/v1/factory/drafts/release" \
  -H "Content-Type: application/json"
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:321`

---

### 1.5 模板接口

#### 1.5.1 将草稿保存为模板

```
POST /v1/factory/drafts/{setting_id}/savetemplate
```

**描述**: 将当前的草稿配置存储为模板，方便其他位置引用。存储时会级联处理相关的配置。

**路径参数**:
- `setting_id` (integer): 草稿配置ID

**请求体** (Body):
```json
{
  "name": "模板名称"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "templateId": 789
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/draft_setting.py:340`

---

## 二、在线配置接口 (Online Settings)

在线配置是正在运行的机器人配置，仅支持查询和触发Action操作，不支持增删改。

### 2.1 查询接口

#### 2.1.1 获取所有场景

```
GET /v1/factory/online/scenes
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": ["robot", "chain", "memory", "llm"]
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:52`

---

#### 2.1.2 获取指定场景下的工厂列表

```
GET /v1/factory/online/{scene}/factories
```

**路径参数**:
- `scene` (string): 场景名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "factory_names": ["Brain", "Chain", "Memory"]
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:64`

---

#### 2.1.3 获取工厂配置结构

```
GET /v1/factory/online/struct/{scene}/{factory_name}
```

**路径参数**:
- `scene` (string): 场景名称
- `factory_name` (string): 工厂名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "scene": "robot",
    "factory_name": "Brain",
    "config_schema": {...}
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:78`

---

#### 2.1.4 查询在线配置列表

```
GET /v1/factory/online/query
```

**查询参数**:
- `scene` (string, 可选): 场景名称
- `factoryName` (string, 可选): 工厂名称
- `settingName` (string, 可选): 配置名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 456,
      "scene": "robot",
      "name": "Brain",
      "setting_name": "生产环境配置",
      "config": {...}
    }
  ]
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:95`

---

#### 2.1.5 获取单个在线配置

```
GET /v1/factory/online/{setting_id}
```

**路径参数**:
- `setting_id` (integer): 在线配置ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 456,
    "scene": "robot",
    "name": "Brain",
    "setting_name": "生产环境配置",
    "config": {...}
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:118`

---

### 2.2 修改接口

#### 2.2.1 触发在线配置 Action

```
PUT /v1/factory/online/{setting_id}/action/{action}
```

**描述**: 在在线配置中触发指定的 Action 操作

**路径参数**:
- `setting_id` (integer): 在线配置ID
- `action` (string): Action名称

**请求体** (Body, 可选):
```json
{
  "param1": "value1"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "action executed successfully"
  }
}
```

**使用示例**:
```bash
# 重启在线机器人
curl -X PUT "http://localhost:8000/v1/factory/online/456/action/restart" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:132`

---

#### 2.2.2 获取在线配置 Action 详情

```
GET /v1/factory/online/{setting_id}/action/{action}/detail
```

**路径参数**:
- `setting_id` (integer): 在线配置ID
- `action` (string): Action名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "action_name": "restart",
    "description": "重启机器人服务",
    "parameters": {
      "force": {
        "type": "boolean",
        "description": "强制重启标志",
        "required": false
      }
    }
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/online_setting.py:151`

---

## 三、模板配置接口 (Template Settings)

模板配置是可复用的配置模板，支持查询、应用和删除操作。

### 3.1 查询接口

#### 3.1.1 获取所有场景

```
GET /v1/factory/templates/scenes
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": ["robot", "chain", "memory", "llm"]
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:52`

---

#### 3.1.2 获取指定场景下的工厂列表

```
GET /v1/factory/templates/{scene}/factories
```

**路径参数**:
- `scene` (string): 场景名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "factory_names": ["Brain", "Chain", "Memory"]
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:64`

---

#### 3.1.3 获取工厂配置结构

```
GET /v1/factory/templates/struct/{scene}/{factory_name}
```

**路径参数**:
- `scene` (string): 场景名称
- `factory_name` (string): 工厂名称

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "scene": "robot",
    "factory_name": "Brain",
    "config_schema": {...}
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:78`

---

#### 3.1.4 查询模板配置列表（支持分页）

```
GET /v1/factory/templates/query
```

**查询参数**:
- `scene` (string, 可选): 场景名称
- `factoryName` (string, 可选): 工厂名称
- `settingName` (string, 可选): 配置名称
- `templateName` (string, 可选): 模板名称
- `page` (integer, 默认=1): 页码
- `pageSize` (integer, 默认=10): 每页数量

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "templates": [
      {
        "id": 789,
        "scene": "robot",
        "name": "Brain",
        "setting_name": "标准大脑模板",
        "template_name": "默认大脑模板",
        "config": {...}
      }
    ]
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:96`

---

#### 3.1.5 获取单个模板配置

```
GET /v1/factory/templates/{setting_id}
```

**路径参数**:
- `setting_id` (integer): 模板配置ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 789,
    "scene": "robot",
    "name": "Brain",
    "setting_name": "标准大脑模板",
    "template_name": "默认大脑模板",
    "config": {...}
  }
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:134`

---

### 3.2 删除接口

#### 3.2.1 删除模板配置

```
DELETE /v1/factory/templates/{setting_id}
```

**路径参数**:
- `setting_id` (integer): 模板配置ID

**描述**: 删除模板配置，系统会级联删除引用此模板的其他配置。

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:149`

---

### 3.3 应用接口

#### 3.3.1 应用模板配置到草稿

```
POST /v1/factory/templates/apply
```

**查询参数**:
- `templateSettingId` (integer, 必需): 模板配置ID

**描述**: 将模板配置应用到草稿中，创建新的草稿配置。

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "draftId": 321
  }
}
```

**使用示例**:
```bash
curl -X POST "http://localhost:8000/v1/factory/templates/apply?templateSettingId=789" \
  -H "Content-Type: application/json"
```

**代码位置**: `tfrobotserver/api/v1/robot_factory/template_setting.py:167`

---

## 四、使用流程

### 4.1 标准配置修改流程

```
┌─────────────────┐
│ 1. 查询配置     │
│ GET /drafts/query │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 更新草稿配置 │
│ PUT /drafts/{id} │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 测试验证     │
│ (手动或自动化)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 发布配置     │
│ POST /drafts/release │
└─────────────────┘
```

### 4.2 完整示例：创建并发布新配置

```python
import requests
import json

BASE_URL = "http://localhost:8000/v1/factory"

# Step 1: 创建草稿配置
print("Step 1: 创建草稿配置...")
create_payload = {
    "draftInfo": {
        "scene": "robot",
        "name": "Brain",
        "setting_name": "测试配置",
        "config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
}

response = requests.post(f"{BASE_URL}/drafts/", json=create_payload)
result = response.json()
draft_id = result["data"]["id"]
print(f"✓ 草稿创建成功，ID: {draft_id}")

# Step 2: 更新配置
print("\nStep 2: 更新草稿配置...")
update_payload = {
    "draftInfo": {
        "setting_name": "生产环境配置",
        "config": {
            "model": "gpt-4-turbo",
            "temperature": 0.8,
            "max_tokens": 3000
        }
    }
}

response = requests.put(f"{BASE_URL}/drafts/{draft_id}", json=update_payload)
print("✓ 配置更新成功")

# Step 3: 验证配置
print("\nStep 3: 验证配置...")
response = requests.get(f"{BASE_URL}/drafts/{draft_id}")
config = response.json()["data"]
print(f"✓ 当前配置: {config['config']}")

# Step 4: 发布配置
print("\nStep 4: 发布配置...")
response = requests.post(f"{BASE_URL}/drafts/release")
online_id = response.json()["data"]["onlineRobotId"]
print(f"✓ 配置发布成功，在线配置ID: {online_id}")

# Step 5: 触发在线机器人Action
print("\nStep 5: 触发在线机器人重启...")
response = requests.put(f"{BASE_URL}/online/{online_id}/action/restart", json={})
print("✓ 机器人重启成功")
```

### 4.3 批量创建关联配置示例

```python
import requests

BASE_URL = "http://localhost:8000/v1/factory"

# 批量创建相互关联的配置节点
batch_payload = {
    "batchRequest": {
        "drafts": [
            {
                "temp_id": -1,
                "draft": {
                    "scene": "robot",
                    "name": "Brain",
                    "setting_name": "主大脑",
                    "config": {
                        "model": "gpt-4",
                        "chain": {
                            "setting_id": -2,  # 引用临时ID
                            "category": "Draft"
                        }
                    }
                }
            },
            {
                "temp_id": -2,
                "draft": {
                    "scene": "chain",
                    "name": "Chain",
                    "setting_name": "对话链",
                    "config": {
                        "steps": ["greeting", "processing", "response"]
                    }
                }
            }
        ]
    }
}

response = requests.post(f"{BASE_URL}/drafts/batch", json=batch_payload)
result = response.json()

print(f"成功创建 {result['data']['success_count']} 个配置")
print(f"失败 {result['data']['failure_count']} 个配置")

for item in result["data"]["results"]:
    if item["success"]:
        print(f"✓ 配置 {item['index']}: ID={item['setting_id']}")
    else:
        print(f"✗ 配置 {item['index']}: {item['error_message']}")
```

---

## 五、常见使用场景

### 5.1 修改机器人模型参数

```bash
# 修改温度和token限制
curl -X PUT "http://localhost:8000/v1/factory/drafts/123" \
  -H "Content-Type: application/json" \
  -d '{
    "draftInfo": {
      "config": {
        "temperature": 0.9,
        "max_tokens": 4000,
        "top_p": 0.95
      }
    }
  }'
```

### 5.2 保存常用配置为模板

```bash
# 1. 将当前草稿保存为模板
curl -X POST "http://localhost:8000/v1/factory/drafts/123/savetemplate" \
  -H "Content-Type: application/json" \
  -d '{"name": "高性能配置模板"}'

# 2. 应用模板到新草稿
curl -X POST "http://localhost:8000/v1/factory/templates/apply?templateSettingId=789" \
  -H "Content-Type: application/json"
```

### 5.3 批量复制配置

```python
import requests

# 复制多个配置节点并保持引用关系
batch_data = {
    "batchRequest": {
        "drafts": [
            {"temp_id": -1, "draft": {...}},  # 节点1
            {"temp_id": -2, "draft": {...}},  # 节点2
            {"temp_id": -3, "draft": {...}},  # 节点3
        ]
    }
}

response = requests.post(
    "http://localhost:8000/v1/factory/drafts/batch",
    json=batch_data
)
```

### 5.4 重启在线机器人

```bash
# 方式1: 通过草稿配置发布
curl -X POST "http://localhost:8000/v1/factory/drafts/release"

# 方式2: 直接触发在线机器人Action
curl -X PUT "http://localhost:8000/v1/factory/online/456/action/restart" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

---

## 六、错误处理

### 6.1 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式 |
| 404 | 资源不存在 | 检查setting_id是否正确 |
| 500 | 服务器内部错误 | 查看错误消息，可能是配置重复或验证失败 |

### 6.2 错误响应示例

```json
{
  "code": 500,
  "message": "Config duplicate",
  "data": {}
}
```

### 6.3 Python 错误处理示例

```python
import requests

def update_robot_config(setting_id, new_config):
    url = f"http://localhost:8000/v1/factory/drafts/{setting_id}"
    payload = {
        "draftInfo": {
            "config": new_config
        }
    }

    try:
        response = requests.put(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result["code"] == 200:
            print("✓ 配置更新成功")
            return result["data"]
        else:
            print(f"✗ 更新失败: {result['message']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ 网络错误: {e}")
        return None

# 使用示例
config = {
    "model": "gpt-4-turbo",
    "temperature": 0.8
}

result = update_robot_config(123, config)
if result:
    print(f"配置ID: {result['id']}")
```

---

## 七、附录

### 7.1 代码文件位置

| 功能 | 文件路径 |
|------|----------|
| 草稿配置路由 | `tfrobotserver/api/v1/robot_factory/draft_setting.py` |
| 在线配置路由 | `tfrobotserver/api/v1/robot_factory/online_setting.py` |
| 模板配置路由 | `tfrobotserver/api/v1/robot_factory/template_setting.py` |
| 路由注册 | `tfrobotserver/api/v1/robot_factory/base.py` |

### 7.2 DTO 数据模型

所有DTO定义位于：
- 草稿配置: `tfrobotserver/dtos/v1/robot_factory/draft_factory.py`
- 在线配置: `tfrobotserver/dtos/v1/robot_factory/online_factory.py`
- 模板配置: `tfrobotserver/dtos/v1/robot_factory/template_factory.py`

### 7.3 服务层

所有业务逻辑位于：
- 草稿服务: `tfrobotserver/services/robot_factory_service/draft_factory_service.py`
- 在线服务: `tfrobotserver/services/robot_factory_service/online_factory_service.py`
- 模板服务: `tfrobotserver/services/robot_factory_service/template_factory_service.py`

---

## 八、快速参考

### 最常用的修改接口

```
PUT /v1/factory/drafts/{setting_id}
```

### 典型请求示例

```bash
curl -X PUT "http://localhost:8000/v1/factory/drafts/123" \
  -H "Content-Type: application/json" \
  -d '{
    "draftInfo": {
      "setting_name": "新配置名称",
      "config": {
        "key1": "value1",
        "key2": "value2"
      }
    }
  }'
```

### 标准工作流程

1. **修改草稿**: `PUT /drafts/{id}`
2. **测试验证**: 手动测试或自动化测试
3. **发布上线**: `POST /drafts/release`
4. **触发Action**: `PUT /online/{id}/action/{action}`

---

**文档版本**: 1.0
**最后更新**: 2024-12-17
**维护者**: TFRobotServer Team
