# activation-api 接口协议设计

## 1. 接口概述

本项目是Chrome插件和pc客户端激活码验证服务，接口分为两大部分：
- **客户端接口**：供Chrome插件客户端、pc客户端调用，用于验证激活、查询状态、获取权限
- **管理端接口**：供管理后台调用，用于管理激活码和设备

## 2. 基础信息

- **API Base URL**: `https://api.example.com/v1`
- **Content-Type**: `application/json`
- **认证方式**: `API Key` 放在请求头 `X-API-Key`

---

## 第一部分：插件客户端接口（Chrome 插件、pc客户端均 调用）

这些接口供 Chrome 插件客户端、pc客户端均  调用，用于激活验证、状态查询和权限获取。

### 1.1 验证激活码接口

**接口路径**: `/auth/verify`
**请求方法**: `POST`
**功能**: 验证激活码是否合规、是否过期、是否被其他设备绑定

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |
| machine_code | string | 是 | 机器码（设备唯一标识） |
| **client_type** | string | 是 | **客户端类型**：&lt;br&gt;`browser-extension`（浏览器插件（支持Chrome、Edge等））/ `pc-client`（电脑客户端），服务端根据类型分配不同token有效期和验证策略 |
| plugin_version | string | 是 | 插件/客户端版本号 |
| current_expiry_date | string | 否 | 当前过期时间（ISO格式，可选） |

#### 客户端类型说明

| client_type | 说明 |
|------------|------|
| `browser-extension` | 浏览器插件（支持Chrome、Edge等） |
| `pc-client` | 电脑端客户端 |

#### 请求示例

```json
{
  "auth_code": "1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
  "machine_code": "abc123def456",
  "client_type": "browser-extension",
  "plugin_version": "1.0.0",
  "current_expiry_date": "2026-03-14T12:00:00Z"
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 验证状态："valid"（有效）、"invalid"（无效）、"expired"（过期）、"used"（已被其他设备使用） |
| message | string | 状态描述 |
| data | object | 验证成功时返回的详细信息 |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.activated_date | string | 激活时间（ISO格式） |
| data.machine_code | string | 绑定的机器码 |

#### 响应示例

**成功响应**:
```json
{
  "status": "valid",
  "message": "激活码验证成功",
  "data": {
    "expiry_date": "2026-12-31T23:59:59Z",
    "activated_date": "2026-03-13T12:00:00Z",
    "machine_code": "abc123def456"
  }
}
```

**失败响应**:
```json
{
  "status": "expired",
  "message": "激活码已过期",
  "data": null
}
```

### 1.2 查询设备信息接口

**接口路径**: `/device/info`
**请求方法**: `POST`
**功能**: 查询当前设备激活状态、过期时间、剩余天数、功能权限

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码（设备唯一标识） |
| **client_type** | string | 是 | **客户端类型**：&lt;br&gt;`browser-extension` / `pc-client`，服务端根据类型返回对应token有效期配置 |
| plugin_version | string | 是 | 插件/客户端版本号 |

#### 请求示例

```json
{
  "machine_code": "abc123def456",
  "client_type": "browser-extension",
  "plugin_version": "1.0.0"
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 设备信息 |
| data.machine_code | string | 机器码 |
| data.client_type | string | 客户端类型 |
| data.is_active | boolean | 是否处于激活状态 |
| data.auth_code | string | 当前绑定的激活码 |
| data.package_type | string | 当前套餐类型：free（免费版）/ basic（基础版）/ premium（高级版） |
| data.activated_date | string | 激活时间（ISO格式） |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.expired | boolean | 是否已过期 |
| data.days_remaining | integer | 剩余有效期天数（过期时为 0，永久有效则为 -1） |
| data.first_activation | boolean | 是否首次激活 |
| data.last_verify_time | string | 上次验证时间（ISO格式） |
| data.created_at | string | 设备首次记录时间（ISO格式） |
| data.permissions | object | 功能权限信息 |
| data.permissions.prompt_word | object | 提示词管理功能权限 （浏览器插件专用）|
| data.permissions.prompt_word.daily_limit | integer | 每天最多使用次数（-1表示不限制）  （浏览器插件专用）|
| data.permissions.prompt_word.enable_like_filter | boolean | 是否启用点赞数过滤功能  （浏览器插件专用）|
| data.permissions.download | object | 下载功能权限 （浏览器插件专用） |
| data.permissions.download.daily_limit | integer | 每天最多使用次数（-1表示不限制） （浏览器插件专用）|
| data.permissions.search | object | 搜索页面功能权限 （浏览器插件专用） |
| data.permissions.search.high_value_notes | object | 显示高价值笔记功能权限 （浏览器插件专用） |
| data.permissions.search.high_value_notes.daily_limit | integer | 每天最多使用次数（-1表示不限制） （浏览器插件专用） |
| data.permissions.search.keyword_expansion | object | 关键词拓展功能权限 （浏览器插件专用） |
| data.permissions.search.keyword_expansion.daily_limit | integer | 每天最多使用次数（-1表示不限制） （浏览器插件专用） |
| data.permissions.auto_use | object | 自动养号功能权限（PC客户端专用） |
| data.permissions.auto_use.device_count | integer | 每天养号设备数量(-1 表示不限制)（PC客户端专用） |
| data.permissions.auto_use.device_time | integer | 每天单设备养号最长时间设置（-1表示不限制）（PC客户端专用） |
| data.permissions.auto_use.daily_count | integer | 每天总养号次数(-1 表示不限制)（PC客户端专用） |
| data.permissions.create | object | 内容创作功能权限（PC客户端专用） |
| data.permissions.create.daily_limit | integer | 每日内容创作次数(-1 表示不限制)（PC客户端专用） |
| data.permissions.pdf | object | PDF生成功能权限（PC客户端专用） |
| data.permissions.pdf.daily_limit | integer | 每天使用生成PDF数量（-1表示不限制）（PC客户端专用） |
| data.permissions.cover | object | 封面生成功能权限（PC客户端专用） |
| data.permissions.cover.daily_limit | integer | 每日生成封面功能使用次数（-1表示不限制）（PC客户端专用） |
| data.permissions.transfer | object | 文件传输功能权限（PC客户端专用） |
| data.permissions.transfer.daily_limit | integer | 每日文件传输到手机功能使用次数（-1表示不限制）（PC客户端专用） |

#### 响应示例

**示例1：浏览器插件 - 基础版已激活**
```json
{
  "status": "success",
  "message": "查询成功",
  "data": {
    "machine_code": "abc123def456",
    "client_type": "browser-extension",
    "is_active": true,
    "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
    "package_type": "basic",
    "activated_date": "2026-03-14T10:30:00Z",
    "expiry_date": "2026-04-13T10:30:00Z",
    "expired": false,
    "days_remaining": 25,
    "first_activation": false,
    "last_verify_time": "2026-03-18T09:00:00Z",
    "created_at": "2026-03-14T10:30:00Z",
    "permissions": {
      "prompt_word": {
        "daily_limit": 50,
        "enable_like_filter": false
      },
      "download": {
        "daily_limit": 20
      },
      "search": {
        "high_value_notes": {
          "daily_limit": 100
        },
        "keyword_expansion": {
          "daily_limit": 50
        }
      }
    }
  }
}
```

**示例2：PC客户端 - 高级版已激活**
```json
{
  "status": "success",
  "message": "查询成功",
  "data": {
    "machine_code": "pc-abc123def456",
    "client_type": "pc-client",
    "is_active": true,
    "auth_code": "-1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
    "package_type": "premium",
    "activated_date": "2026-03-14T10:30:00Z",
    "expiry_date": "9999-12-31T23:59:59",
    "expired": false,
    "days_remaining": -1,
    "first_activation": true,
    "last_verify_time": "2026-03-18T09:00:00Z",
    "created_at": "2026-03-14T10:30:00Z",
    "permissions": {
      "auto_use": {
        "device_count": -1,
        "device_time": -1,
        "daily_count": -1
      },
      "create": {
        "daily_limit": -1
      },
      "pdf": {
        "daily_limit": -1
      },
      "cover": {
        "daily_limit": -1
      },
      "transfer": {
        "daily_limit": -1
      }
    }
  }
}
```

**未激活示例**
```json
{
  "status": "success",
  "message": "查询成功",
  "data": {
    "machine_code": "abc123def456",
    "client_type": "browser-extension",
    "is_active": false,
    "auth_code": null,
    "package_type": null,
    "activated_date": null,
    "expiry_date": null,
    "expired": false,
    "days_remaining": 0,
    "first_activation": true,
    "last_verify_time": null,
    "created_at": "2026-03-14T10:30:00Z",
    "permissions": {
      "prompt_word": {
        "daily_limit": 20,
        "enable_like_filter": true
      },
      "download": {
        "daily_limit": 20
      },
      "search": {
        "high_value_notes": {
          "daily_limit": 30
        },
        "keyword_expansion": {
          "daily_limit": 10
        }
      }
    }
  }
}
```

---

## 第二部分：管理端接口（管理后台调用）

这些接口供管理后台调用，用于管理激活码和设备。

### 2.1 生成激活码接口

**接口路径**: `/auth/generate`
**请求方法**: `POST`
**功能**: 生成新的激活码，包含生成时间

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| duration | integer | 是 | 有效期天数（1、7、30、365、-1表示永久） |
| count | integer | 否 | 生成激活码的数量，默认为1 |
| package_type | string | 是 | 套餐类型：free（免费版）/ basic（基础版）/ premium（高级版） |
| **client_type** | string | 是 | **目标客户端类型**：&lt;br&gt;`browser-extension` / `pc-client`，激活码绑定到特定客户端类型，服务端按类型分配不同策略 |

#### 请求示例

```json
{
  "duration": 30,
  "count": 5,
  "package_type": "basic",
  "client_type": "browser-extension"
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 生成状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 生成成功时返回的详细信息 |
| data.auth_codes | array | 生成的激活码数组 |
| data.duration | integer | 有效期天数 |
| data.package_type | string | 套餐类型 |
| data.client_type | string | 目标客户端类型 |
| data.generate_date | string | 生成时间（ISO格式） |

#### 响应示例

**成功响应**:
```json
{
  "status": "success",
  "message": "激活码生成成功",
  "data": {
    "auth_codes": [
      "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
      "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGB==",
      "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGC==",
      "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGD==",
      "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGE=="
    ],
    "duration": 30,
    "package_type": "basic",
    "client_type": "browser-extension",
    "generate_date": "2026-03-13T12:00:00Z"
  }
}
```

**失败响应**:
```json
{
  "status": "error",
  "message": "生成激活码失败：参数错误",
  "data": null
}
```

### 2.2 查询激活码信息接口

**接口路径**: `/auth/info`
**请求方法**: `POST`
**功能**: 查询激活码的详细信息，包括状态、绑定设备、过期时间等

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |

#### 请求示例

```json
{
  "auth_code": "1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA=="
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 激活码详细信息 |
| data.auth_code | string | 激活码 |
| data.status | string | 激活码状态："unused"（未使用）、"used"（已使用）、"expired"（已过期）、"revoked"（已吊销） |
| data.duration | integer | 有效期天数 |
| data.package_type | string | 套餐类型：free / basic / premium |
| data.client_type | string | 客户端类型：`browser-extension` / `pc-client` |
| data.generate_date | string | 生成时间（ISO格式） |
| data.activated_date | string | 激活时间（ISO格式，未使用时为null） |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.machine_code | string | 绑定的机器码，未使用时为null |
| data.created_at | string | 创建时间（ISO格式） |
| data.updated_at | string | 最后更新时间（ISO格式） |

#### 响应示例

**成功响应（已使用）**:
```json
{
  "status": "success",
  "message": "查询成功",
  "data": {
    "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
    "status": "used",
    "duration": 30,
    "package_type": "basic",
    "client_type": "browser-extension",
    "generate_date": "2026-03-13T12:00:00Z",
    "activated_date": "2026-03-14T10:30:00Z",
    "expiry_date": "2026-04-13T10:30:00Z",
    "machine_code": "abc123def456",
    "created_at": "2026-03-13T12:00:00Z",
    "updated_at": "2026-03-14T10:30:00Z"
  }
}
```

**成功响应（未使用）**:
```json
{
  "status": "success",
  "message": "查询成功",
  "data": {
    "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
    "status": "unused",
    "duration": 30,
    "package_type": "basic",
    "client_type": "browser-extension",
    "generate_date": "2026-03-13T12:00:00Z",
    "activated_date": null,
    "expiry_date": null,
    "machine_code": null,
    "created_at": "2026-03-13T12:00:00Z",
    "updated_at": "2026-03-13T12:00:00Z"
  }
}
```

**失败响应**:
```json
{
  "status": "error",
  "message": "激活码不存在",
  "data": null
}
```

### 2.3 更新激活码信息接口

**接口路径**: `/auth/update`
**请求方法**: `POST`
**功能**: 更新激活码信息，包括延期、更改套餐、解除绑定等

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |
| update_data | object | 是 | 需要更新的字段 |
| update_data.status | string | 否 | 更新状态："unused"、"used"、"expired"、"revoked" |
| update_data.expiry_date | string | 否 | 新的过期时间（ISO格式） |
| update_data.duration | integer | 否 | 新的有效期天数，更新后会重新计算过期时间 |
| update_data.package_type | string | 否 | 新的套餐类型：free / basic / premium |
| update_data.client_type | string | 否 | 新的客户端类型：`browser-extension` / `pc-client` |
| update_data.unbind_machine | boolean | 否 | 是否解除设备绑定，true表示解除 |

#### 请求示例

```json
{
  "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
  "update_data": {
    "duration": 90,
    "package_type": "premium"
  }
}
```

**解除绑定示例**:
```json
{
  "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
  "update_data": {
    "unbind_machine": true
  }
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 更新后的激活码信息 |

#### 响应示例

**成功响应**:
```json
{
  "status": "success",
  "message": "激活码更新成功",
  "data": {
    "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
    "status": "unused",
    "duration": 90,
    "package_type": "premium",
    "expiry_date": "2026-06-12T10:30:00Z",
    "machine_code": null
  }
}
```

**失败响应**:
```json
{
  "status": "error",
  "message": "激活码不存在",
  "data": null
}
```

### 2.4 删除激活码接口

**接口路径**: `/auth/delete`
**请求方法**: `POST`
**功能**: 删除指定激活码

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |

#### 请求示例

```json
{
  "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA=="
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 删除结果 |
| data.deleted | boolean | 是否删除成功 |

#### 响应示例

**成功响应**:
```json
{
  "status": "success",
  "message": "激活码删除成功",
  "data": {
    "deleted": true
  }
}
```

**失败响应**:
```json
{
  "status": "error",
  "message": "激活码不存在",
  "data": {
    "deleted": false
  }
}
```

### 2.5 列出所有激活码接口

**接口路径**: `/auth/list`
**请求方法**: `POST`
**功能**: 分页列出所有激活码，支持按状态筛选

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | string | 否 | 按状态筛选，可选值：unused, used, expired, revoked |
| package_type | string | 否 | 按套餐类型筛选：free / basic / premium |
| client_type | string | 否 | 按客户端类型筛选：`browser-extension` / `pc-client` |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20，最大 100 |

#### 请求示例

```json
{
  "status": "unused",
  "package_type": "basic",
  "page": 1,
  "page_size": 20
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 返回数据 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.page_size | integer | 每页数量 |
| data.items | array | 激活码信息列表 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取列表成功",
  "data": {
    "total": 45,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
        "status": "unused",
        "duration": 30,
        "package_type": "basic",
        "client_type": "browser-extension",
        "generate_date": "2026-03-13T12:00:00Z",
        "expiry_date": null,
        "machine_code": null
      }
    ]
  }
}
```

### 2.6 设备管理 - 查询设备信息接口

**接口路径**: `/device/info`
**请求方法**: `POST`
**功能**: 查询设备的激活状态和详细信息

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码（设备唯一标识） |
| client_type | string | 是 | 客户端类型：`browser-extension` / `pc-client` |

#### 请求示例

```json
{
  "machine_code": "abc123def456"
}
```

#### 响应参数

参数同**插件客户端接口 /device/info**，返回完整设备信息包含权限。

### 2.7 设备管理 - 列出设备接口

**接口路径**: `/device/list`
**请求方法**: `POST`
**功能**: 分页列出所有设备，支持按激活状态筛选

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| is_active | boolean | 否 | 是否只返回已激活设备 |
| expired | boolean | 否 | 是否只返回已过期设备 |
| client_type | string | 否 | 按客户端类型筛选：`browser-extension` / `pc-client` |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20，最大 100 |

#### 请求示例

```json
{
  "is_active": true,
  "page": 1,
  "page_size": 20
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 返回数据 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.page_size | integer | 每页数量 |
| data.items | array | 设备信息列表 |

### 2.8 设备管理 - 解绑设备接口

**接口路径**: `/device/unbind`
**请求方法**: `POST`
**功能**: 解除设备与激活码的绑定，使激活码可以重新绑定其他设备

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 要解绑的设备机器码 |
| client_type | string | 是 | 客户端类型：`browser-extension` / `pc-client` |
| auth_code | string | 否 | 激活码（可选，如不提供则根据设备查询绑定的激活码） |

#### 请求示例

```json
{
  "machine_code": "abc123def456"
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 解绑结果 |
| data.unbound | boolean | 是否解绑成功 |
| data.auth_code | string | 解绑的激活码 |

### 2.9 设备管理 - 删除设备接口

**接口路径**: `/device/delete`
**请求方法**: `POST`
**功能**: 删除设备记录

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码 |
| client_type | string | 是 | 客户端类型：`browser-extension` / `pc-client` |

#### 响应示例

**成功响应**:
```json
{
  "status": "success",
  "message": "设备删除成功",
  "data": {
    "deleted": true
  }
}
```

### 2.10 权限管理 - 列出所有权限配置

**接口路径**: `/permissions/list`
**请求方法**: `POST`
**功能**: 列出所有套餐权限配置，需要管理端API Key

#### 请求参数
无（不需要参数）

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态 |
| message | string | 状态描述 |
| data.total | integer | 总配置数 |
| data.items | array | 权限配置列表 |
| data.items[].client_type | string | 客户端类型 |
| data.items[].package_type | string | 套餐类型 |
| data.items[].permissions | object | 权限配置JSON |
| data.items[].created_at | string | 创建时间 |
| data.items[].updated_at | string | 更新时间 |

### 2.11 权限管理 - 设置/更新权限配置

**接口路径**: `/permissions/set`
**请求方法**: `POST`
**功能**: 新增或更新套餐权限配置，需要管理端API Key

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| client_type | string | 是 | 客户端类型：`browser-extension` / `pc-client` |
| package_type | string | 是 | 套餐类型：free / basic / premium |
| permissions | object | 是 | 完整权限配置JSON |

**浏览器插件 permissions 结构示例**:
```json
{
  "prompt_word": {
    "daily_limit": 50,
    "enable_like_filter": false
  },
  "download": {
    "daily_limit": 20
  },
  "search": {
    "high_value_notes": {
      "daily_limit": 100
    },
    "keyword_expansion": {
      "daily_limit": 50
    }
  }
}
```

**PC客户端 permissions 结构示例**:
```json
{
  "auto_use": {
    "device_count": 3,
    "device_time": 60,
    "daily_count": 9
  },
  "create": {
    "daily_limit": 15
  },
  "pdf": {
    "daily_limit": 30
  },
  "cover": {
    "daily_limit": 30
  },
  "transfer": {
    "daily_limit": 30
  }
}
```

#### 请求示例

**示例1：设置浏览器插件高级版权限**
```json
{
  "client_type": "browser-extension",
  "package_type": "premium",
  "permissions": {
    "prompt_word": {
      "daily_limit": 50,
      "enable_like_filter": false
    },
    "download": {
      "daily_limit": 20
    },
    "search": {
      "high_value_notes": {
        "daily_limit": 100
      },
      "keyword_expansion": {
        "daily_limit": 50
      }
    }
  }
}
```

**示例2：设置PC客户端基础版权限**
```json
{
  "client_type": "pc-client",
  "package_type": "basic",
  "permissions": {
    "auto_use": {
      "device_count": 3,
      "device_time": 60,
      "daily_count": 9
    },
    "create": {
      "daily_limit": 15
    },
    "pdf": {
      "daily_limit": 30
    },
    "cover": {
      "daily_limit": 30
    },
    "transfer": {
      "daily_limit": 30
    }
  }
}
```