本项目是Chrome插件激活码验证服务，接口分为两大部分：

- 插件客户端接口：供Chrome插件客户端调用，用于验证激活、查询状态、获取权限

- 管理端接口：供管理后台调用，用于管理激活码和设备

- API Base URL: https://api.example.com/v1

- Content-Type: application/json

- 认证方式: API Key 放在请求头 X-API-Key

## 插件客户端接口

这些接口供 Chrome 插件客户端调用，用于激活验证、状态查询和权限获取。

### 激活码验证接口

接口路径: /auth/verify
请求方法: POST
功能: 验证激活码是否合规、是否过期、是否被其他设备绑定

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |
| machine_code | string | 是 | 机器码（设备唯一标识） |
| client_type | string | 是 | 客户端类型：<br>browser-extension（浏览器插件（支持Chrome、Edge等））/ pc-client（电脑客户端），服务端根据类型分配不同token有效期和验证策略 |
| plugin_version | string | 是 | 插件/客户端版本号 |
| current_expiry_date | string | 否 | 当前过期时间（ISO格式，可选） |

| client_type | 说明 |
|-------------|------|
| browser-extension | 浏览器插件（支持Chrome、Edge等） |
| pc-client | 电脑端客户端 |

**请求示例：**
```json
{
 "auth_code": "1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "machine_code": "abc123def456",
 "client_type": "browser-extension",
 "plugin_version": "1.0.0",
 "current_expiry_date": "2026-03-14T12:00:00Z"
}
```

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 验证状态："valid"（有效）、"invalid"（无效）、"expired"（过期）、"used"（已被其他设备使用） |
| message | string | 状态描述 |
| data | object | 验证成功时返回的详细信息 |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.activated_date | string | 激活时间（ISO格式） |
| data.machine_code | string | 绑定的机器码 |
| data.package_type | string | 套餐类型 |
| data.max_devices | integer | 最大设备数（-1表示不限制） |
| data.max_daily_runs | integer | 每日最大养号次数（-1表示不限制，仅pc-client返回） |
| data.max_daily_creates | integer | 每日内容创作次数（-1表示不限制） |
| data.max_daily_exports | integer | 每日导出分享次数（-1表示不限制） |

**成功响应:**

```json
{
 "status": "valid",
 "message": "激活码验证成功",
 "data": {
 "expiry_date": "2026-12-31T23:59:59Z",
 "activated_date": "2026-03-13T12:00:00Z",
 "machine_code": "abc123def456",
 "package_type": "basic",
 "max_devices": 2,
 "max_daily_runs": 10,
 "max_daily_creates": 20,
 "max_daily_exports": 20
 }
}
```

**失败响应:**

```json
{
 "status": "expired",
 "message": "激活码已过期",
 "data": null
}
```

### 设备信息查询接口

接口路径: /device/info
请求方法: POST
功能: 查询当前设备激活状态、过期时间、剩余天数、功能权限

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码（设备唯一标识） |
| client_type | string | 是 | 客户端类型：<br>browser-extension / pc-client，服务端根据类型返回对应token有效期配置 |
| plugin_version | string | 是 | 插件/客户端版本号 |

**请求示例：**
```json
{
 "machine_code": "abc123def456",
 "client_type": "browser-extension",
 "plugin_version": "1.0.0"
}
```

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 设备信息 |
| data.machine_code | string | 机器码 |
| data.client_type | string | 客户端类型 |
| data.is_active | boolean | 是否处于激活状态 |
| data.auth_code | string | 当前绑定的激活码 |
| data.package_type | string | 当前套餐类型 |
| data.activated_date | string | 激活时间（ISO格式） |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.expired | boolean | 是否已过期 |
| data.days_remaining | integer | 剩余有效期天数（过期时为 0，永久有效则为 -1） |
| data.first_activation | boolean | 是否首次激活 |
| data.last_verify_time | string | 上次验证时间（ISO格式） |
| data.created_at | string | 设备首次记录时间（ISO格式） |
| data.permissions | object | 功能权限信息 |
| data.permissions.prompt_word | object | 提示词管理功能权限 |
| data.permissions.prompt_word.daily_limit | integer | 每天最多使用次数（-1表示不限制） |
| data.permissions.prompt_word.enable_like_filter | boolean | 是否启用点赞数过滤功能 |
| data.permissions.download | object | 下载功能权限 |
| data.permissions.download.daily_limit | integer | 每天最多使用次数（-1表示不限制） |
| data.permissions.search | object | 搜索页面功能权限 |
| data.permissions.search.high_value_notes | object | 显示高价值笔记功能权限 |
| data.permissions.search.high_value_notes.daily_limit | integer | 每天最多使用次数（-1表示不限制） |
| data.permissions.search.keyword_expansion | object | 关键词拓展功能权限 |
| data.permissions.search.keyword_expansion.daily_limit | integer | 每天最多使用次数（-1表示不限制） |
| data.max_devices | integer | 最大设备数（-1表示不限制） |
| data.max_daily_runs | integer | 每日最大养号次数（-1表示不限制，仅pc-client返回） |
| data.max_daily_creates | integer | 每日内容创作次数（-1表示不限制） |
| data.max_daily_exports | integer | 每日导出分享次数（-1表示不限制） |

### PC客户端权限配额

权限配额根据 客户端类型(browser-extension/pc-client) + 套餐类型(basic/premium/vip) 动态分配，设计如下：

| 客户端 | 套餐 | prompt_word 每日限额 | download 每日限额 | high_value_notes 每日限额 | keyword_expansion 每日限额 | max_devices | max_daily_runs | max_daily_creates | max_daily_exports |
|--------|------|---------------------|-------------------|---------------------------|-----------------------------|-------------|-----------------|-------------------|-------------------|
| browser-extension | basic | 20 | 20 | 30 | 10 | -1 | - | 20 | 20 |
| browser-extension | premium | 50 | 20 | 100 | 50 | -1 | - | 50 | 50 |
| browser-extension | vip | 100 | 50 | 200 | 100 | -1 | - | -1 | -1 |
| pc-client | basic | 30 | 30 | 50 | 20 | 2 | 10 | 20 | 20 |
| pc-client | premium | 80 | 50 | 150 | 80 | -1 | -1 | 50 | 50 |
| pc-client | vip | 150 | 100 | 300 | 150 | -1 | -1 | -1 | -1 |

💡 设计说明：pc-client 整体配额比 browser-extension 更高，因为客户端使用频率通常更高。新增套餐或调整配额只需要修改服务端配置表，不需要改接口，客户端会自动拿到最新配额。

**已激活且有效(PC客户端):**

```json
{
 "status": "success",
 "message": "查询成功",
 "data": {
 "machine_code": "abc123def456",
 "client_type": "pc-client",
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
 "max_devices": 2,
 "max_daily_runs": 10,
 "max_daily_creates": 20,
 "max_daily_exports": 20,
 "permissions": {
 "prompt_word": {
 "daily_limit": 30,
 "enable_like_filter": false
 },
 "download": {
 "daily_limit": 30
 },
 "search": {
 "high_value_notes": {
 "daily_limit": 50
 },
 "keyword_expansion": {
 "daily_limit": 20
 }
 }
 }
 }
}
```

**未激活:**

```json
{
 "status": "success",
 "message": "查询成功",
 "data": {
 "machine_code": "abc123def456",
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
 "max_devices": 1,
 "max_daily_runs": 3,
 "max_daily_creates": 3,
 "max_daily_exports": 3,
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

**永久有效示例:**

```json
{
 "status": "success",
 "message": "查询成功",
 "data": {
 "machine_code": "abc123def456",
 "is_active": true,
 "auth_code": "-1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "package_type": "lifetime",
 "activated_date": "2026-03-14T10:30:00Z",
 "expiry_date": "9999-12-31T23:59:59",
 "expired": false,
 "days_remaining": -1,
 "first_activation": true,
 "last_verify_time": "2026-03-18T09:00:00Z",
 "created_at": "2026-03-14T10:30:00Z",
 "max_devices": -1,
 "max_daily_runs": -1,
 "max_daily_creates": -1,
 "max_daily_exports": -1,
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

## 管理端接口

这些接口供管理后台调用，用于管理激活码和设备。

### 生成激活码接口

接口路径: /auth/generate
请求方法: POST
功能: 生成新的激活码，包含生成时间

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| duration | integer | 是 | 有效期天数（1、7、30、365、-1表示永久） |
| count | integer | 否 | 生成激活码的数量，默认为1 |
| package_type | string | 是 | 套餐类型（如：basic、premium、vip） |
| client_type | string | 是 | 目标客户端类型：<br>browser-extension / pc-client，激活码绑定到特定客户端类型，服务端按类型分配不同策略 |

```json
{
 "duration": 30,
 "count": 5,
 "package_type": "premium",
 "client_type": "browser-extension"
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 生成状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 生成成功时返回的详细信息 |
| data.auth_codes | array | 生成的激活码数组 |
| data.duration | integer | 有效期天数 |
| data.client_type | string | 目标客户端类型 |
| data.generate_date | string | 生成时间（ISO格式） |
| data.package_type | string | 套餐类型 |

**成功响应:**

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
 "client_type": "browser-extension",
 "generate_date": "2026-03-13T12:00:00Z",
 "package_type": "premium"
 }
}
```

**失败响应:**

```json
{
 "status": "error",
 "message": "生成激活码失败：参数错误",
 "data": null
}
```

### 查询激活码信息接口

接口路径: /auth/info
请求方法: POST
功能: 查询激活码的详细信息，包括状态、绑定设备、过期时间等

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |

```json
{
 "auth_code": "1_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA=="
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 激活码详细信息 |
| data.auth_code | string | 激活码 |
| data.status | string | 激活码状态："unused"（未使用）、"used"（已使用）、"expired"（已过期）、"revoked"（已吊销） |
| data.duration | integer | 有效期天数 |
| data.package_type | string | 套餐类型 |
| data.client_type | string | 客户端类型：browser-extension / pc-client |
| data.generate_date | string | 生成时间（ISO格式） |
| data.activated_date | string | 激活时间（ISO格式，未使用时为null） |
| data.expiry_date | string | 过期时间（ISO格式） |
| data.machine_code | string | 绑定的机器码，未使用时为null |
| data.created_at | string | 创建时间（ISO格式） |
| data.updated_at | string | 最后更新时间（ISO格式） |
| data.max_devices | integer | 最大设备数（-1表示不限制） |
| data.max_daily_runs | integer | 每日最大养号次数（-1表示不限制，仅pc-client返回） |
| data.max_daily_creates | integer | 每日内容创作次数（-1表示不限制） |
| data.max_daily_exports | integer | 每日导出分享次数（-1表示不限制） |

**成功响应（已使用）:**

```json
{
 "status": "success",
 "message": "查询成功",
 "data": {
 "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "status": "used",
 "duration": 30,
 "package_type": "premium",
 "client_type": "browser-extension",
 "generate_date": "2026-03-13T12:00:00Z",
 "activated_date": "2026-03-14T10:30:00Z",
 "expiry_date": "2026-04-13T10:30:00Z",
 "machine_code": "abc123def456",
 "created_at": "2026-03-13T12:00:00Z",
 "updated_at": "2026-03-14T10:30:00Z",
 "max_devices": -1,
 "max_daily_creates": 50,
 "max_daily_exports": 50
 }
}
```

**成功响应（未使用）:**

```json
{
 "status": "success",
 "message": "查询成功",
 "data": {
 "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "status": "unused",
 "duration": 30,
 "package_type": "premium",
 "client_type": "browser-extension",
 "generate_date": "2026-03-13T12:00:00Z",
 "activated_date": null,
 "expiry_date": null,
 "machine_code": null,
 "created_at": "2026-03-13T12:00:00Z",
 "updated_at": "2026-03-13T12:00:00Z",
 "max_devices": -1,
 "max_daily_creates": 50,
 "max_daily_exports": 50
 }
}
```

**失败响应:**

```json
{
 "status": "error",
 "message": "激活码不存在",
 "data": null
}
```

### 更新激活码信息接口

接口路径: /auth/update
请求方法: POST
功能: 更新激活码信息，包括延期、更改套餐、解除绑定等

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |
| update_data | object | 是 | 需要更新的字段 |
| update_data.status | string | 否 | 更新状态："unused"、"used"、"expired"、"revoked" |
| update_data.expiry_date | string | 否 | 新的过期时间（ISO格式） |
| update_data.duration | integer | 否 | 新的有效期天数，更新后会重新计算过期时间 |
| update_data.package_type | string | 否 | 新的套餐类型 |
| update_data.client_type | string | 否 | 新的客户端类型：browser-extension / pc-client |
| update_data.unbind_machine | boolean | 否 | 是否解除设备绑定，true表示解除 |
| update_data.max_devices | integer | 否 | 最大设备数（-1表示不限制） |
| update_data.max_daily_runs | integer | 否 | 每日最大养号次数（-1表示不限制） |
| update_data.max_daily_creates | integer | 否 | 每日内容创作次数（-1表示不限制） |
| update_data.max_daily_exports | integer | 否 | 每日导出分享次数（-1表示不限制） |

```json
{
 "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "update_data": {
 "duration": 90,
 "package_type": "premium",
 "max_devices": 2,
 "max_daily_runs": 10
 }
}
```

**解除绑定示例:**

```json
{
 "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA==",
 "update_data": {
 "unbind_machine": true
 }
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 更新后的激活码信息 |

**成功响应:**

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
 "machine_code": null,
 "max_devices": 2,
 "max_daily_runs": 10
 }
}
```

**失败响应:**

```json
{
 "status": "error",
 "message": "激活码不存在",
 "data": null
}
```

### 删除激活码接口

接口路径: /auth/delete
请求方法: POST
功能: 删除指定激活码

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| auth_code | string | 是 | 激活码 |

```json
{
 "auth_code": "30_DEcaW1tMEQMDVhQCXBFVSUwdQ1RWW0cJW1tfUEBXXklSVlFBGA=="
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 删除结果 |
| data.deleted | boolean | 是否删除成功 |

**成功响应:**

```json
{
 "status": "success",
 "message": "激活码删除成功",
 "data": {
 "deleted": true
 }
}
```

**失败响应:**

```json
{
 "status": "error",
 "message": "激活码不存在",
 "data": {
 "deleted": false
 }
}
```

### 激活码列表接口

接口路径: /auth/list
请求方法: POST
功能: 分页列出所有激活码，支持按状态筛选

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | string | 否 | 按状态筛选，可选值：unused, used, expired, revoked |
| package_type | string | 否 | 按套餐类型筛选 |
| client_type | string | 否 | 按客户端类型筛选：browser-extension / pc-client |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20，最大 100 |

```json
{
 "status": "unused",
 "package_type": "premium",
 "page": 1,
 "page_size": 20
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 返回数据 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.page_size | integer | 每页数量 |
| data.items | array | 激活码信息列表 |

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
 "package_type": "premium",
 "client_type": "browser-extension",
 "generate_date": "2026-03-13T12:00:00Z",
 "expiry_date": null,
 "machine_code": null
 }
 ]
 }
}
```

### 查询设备信息接口

接口路径: /device/info
请求方法: POST
功能: 查询设备的激活状态和详细信息

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码（设备唯一标识） |
| client_type | string | 是 | 客户端类型：browser-extension / pc-client |

```json
{
 "machine_code": "abc123def456"
}
```

参数同插件客户端接口 /device/info，返回完整设备信息包含权限。

### 设备列表接口

接口路径: /device/list
请求方法: POST
功能: 分页列出所有设备，支持按激活状态筛选

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| is_active | boolean | 否 | 是否只返回已激活设备 |
| expired | boolean | 否 | 是否只返回已过期设备 |
| client_type | string | 否 | 按客户端类型筛选：browser-extension / pc-client |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20，最大 100 |

```json
{
 "is_active": true,
 "page": 1,
 "page_size": 20
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 返回数据 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.page_size | integer | 每页数量 |
| data.items | array | 设备信息列表 |

### 解除设备绑定接口

接口路径: /device/unbind
请求方法: POST
功能: 解除设备与激活码的绑定，使激活码可以重新绑定其他设备

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 要解绑的设备机器码 |
| client_type | string | 是 | 客户端类型：browser-extension / pc-client |
| auth_code | string | 否 | 激活码（可选，如不提供则根据设备查询绑定的激活码） |

```json
{
 "machine_code": "abc123def456"
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态："success"（成功）、"error"（失败） |
| message | string | 状态描述 |
| data | object | 解绑结果 |
| data.unbound | boolean | 是否解绑成功 |
| data.auth_code | string | 解绑的激活码 |

### 删除设备接口

接口路径: /device/delete
请求方法: POST
功能: 删除设备记录

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| machine_code | string | 是 | 机器码 |
| client_type | string | 是 | 客户端类型：browser-extension / pc-client |

**成功响应:**

```json
{
 "status": "success",
 "message": "设备删除成功",
 "data": {
 "deleted": true
 }
}
```

### 套餐权限配置列表接口

接口路径: /permissions/list
请求方法: POST
功能: 列出所有套餐权限配置，需要管理端API Key

无（不需要参数）

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
| data.items[].max_devices | integer | 最大设备数（-1表示不限制） |
| data.items[].max_daily_runs | integer | 每日最大养号次数（-1表示不限制，仅pc-client返回） |
| data.items[].max_daily_creates | integer | 每日内容创作次数（-1表示不限制） |
| data.items[].max_daily_exports | integer | 每日导出分享次数（-1表示不限制） |

### 设置套餐权限配置接口

接口路径: /permissions/set
请求方法: POST
功能: 新增或更新套餐权限配置，需要管理端API Key

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| client_type | string | 是 | 客户端类型：browser-extension / pc-client |
| package_type