# 腾讯云函数 - Chrome插件激活码接口（SQLite版）

基于腾讯云Serverless云函数Python 3.9实现，使用SQLite文件存储，无需额外数据库服务。

## 功能特性

- ✅ **激活码生成与验证**：完整的激活码生命周期管理
- ✅ **设备绑定机制**：一个激活码只能绑定一个设备，防止共享
- ✅ **完整CRUD管理**：支持生成/查询/删除/更新全部操作
- ✅ **自定义有效期**：支持任意天数的有效期，不是固定几个选项
- ✅ **激活码格式**：`{duration}_{20位随机串}`，简短易复制，碰撞概率极低
- ✅ **SQLite原生存储**：Python自带，无需额外依赖，零成本
- ✅ **支持持久化**：可挂载CFS文件系统，数据永久保存不丢失
- ✅ **关闭日志服务**：完全符合要求，避免额外费用
- ✅ **Python 3.9 完美兼容**：解决了时区解析等兼容性问题

## 部署要求

- **地域：** 北京（ap-beijing）
- **运行环境：** Python 3.9
- **日志服务：** 默认关闭（避免收费）

## 说明

SQLite是文件型数据库，不需要额外购买云数据库，适合数据量不大的场景：

- ✅ **零额外依赖**：Python标准库自带sqlite3，无需安装额外包
- ✅ **零额外成本**：不需要购买MongoDB/Redis服务
- ⚠️ **存储位置**：默认存储在 `/tmp` 临时目录，腾讯云函数实例释放后会清除
- 💡 **持久化方案**：如果需要持久保存，可以将SQLite文件放到**腾讯云CFS文件存储**或者**COS挂载**目录，数据不会丢失

## 部署步骤

### 1. 创建云函数

1. 登录[腾讯云控制台](https://console.cloud.tencent.com/scf)，切换到**北京**区域
2. 【云函数】→【函数服务】→【新建】
3. 配置：
   - 运行环境：Python 3.9
   - 创建方式：空白函数
   - 函数名称：`activation-api`
   - 地域：**北京**
   - 日志服务：取消勾选（**不要开启**，避免收费）
4. 上传代码：将项目文件打包zip上传

### 2. 配置环境变量

在云函数 → 【配置】→【环境变量】添加：

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `API_KEY` | API调用密钥，设置为复杂随机字符串 | - | `your-strong-secret-key` |
| `ENCRYPTION_KEY` | 加密签名密钥，设置为随机字符串 | - | `your-encryption-secret` |
| `RATE_LIMIT` | 每分钟请求限制 | `60` | `60` |
| `DB_PATH` | SQLite数据库文件路径 | `/tmp/activation.db` | 如果使用CFS，填写CFS挂载路径 |

### 3. 添加API网关触发器

1. 云函数 → 【触发方式】→【添加触发器】
2. 选择 **API网关**：
   - 发布环境：发布
   - API类型：公网URL
   - 请求方法：ANY
   - 跨域：启用
3. 创建后得到公网地址：
   - 验证接口：`https://<你的域名>/release/auth/verify`
   - 生成接口：`https://<你的域名>/release/auth/generate`

## 持久化存储配置

如果需要数据持久化（不会因为函数实例释放丢失）：

1. 在腾讯云控制台购买【文件存储CFS】，创建文件系统
2. 挂载CFS到云函数的VPC中
3. 修改环境变量 `DB_PATH` 为CFS挂载目录，比如：`/mnt/cfs/activation.db`
4. 数据会永久保存在CFS中，不会丢失

CFS费用非常低（按实际存储计费，1GB才几毛钱/月），适合这个场景。

## 接口说明

完全遵循协议设计：

### 请求头

必须携带：
- `X-API-Key: {你的API_KEY}`
- `Content-Type: application/json`

### 1. POST /auth/verify 验证激活码

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auth_code | string | 是 | 激活码 |
| machine_code | string | 是 | 设备唯一机器码 |
| plugin_version | string | 是 | 插件版本 |
| current_expiry_date | string | 否 | 当前存储的过期时间 |

响应状态：
- `valid`：有效，返回激活信息
- `invalid`：无效/格式错误
- `expired`：已过期
- `used`：已绑定其他设备

### 2. POST /auth/generate 生成激活码（管理接口）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| duration | integer | 是 | 有效期（天数），支持**任意自定义天数**，比如 3/30/999 |
| count | integer | 否 | 生成数量，默认 1，最多一次生成 100 个 |
| package_type | string | 是 | 套餐类型 basic/premium，可自定义 |

激活码格式：`{duration}_{20位字母数字随机字符串}`，示例：`3_2puPQRGFpSDoCUQc3c57`

响应示例：
```json
{
  "status": "success",
  "message": "成功生成 2 个激活码",
  "data": {
    "auth_codes": [
      "3_2puPQRGFpSDoCUQc3c57",
      "3_8XErIASWglbbDdz9CfCw"
    ],
    "duration": 3,
    "generate_date": "2026-03-16T14:05:30.347256"
  }
}
```

### 3. POST /auth/list 列出所有激活码（管理接口）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| offset | integer | 否 | 分页偏移，默认 0 |
| limit | integer | 否 | 每页数量，默认 10 |
| activated_only | boolean | 否 | 只看已激活的，默认 false |

响应示例：
```json
{
  "status": "success",
  "message": "获取列表成功",
  "data": {
    "total": 4,
    "offset": 0,
    "limit": 10,
    "list": [
      {
        "auth_code": "3_2puPQRGFpSDoCUQc3c57",
        "duration": 3,
        "package_type": "premium",
        "generate_date": "2026-03-16T14:05:30.347256",
        "activated_date": "2026-03-16T14:05:30.600894",
        "machine_code": "test-machine-1",
        "expiry_date": "2026-03-19T14:05:30.600904"
      }
    ]
  }
}
```

### 4. POST /auth/delete 删除激活码（管理接口）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auth_code | string | 是 | 要删除的激活码 |

响应：
```json
{
  "status": "success",
  "message": "激活码 xxx 删除成功",
  "data": null
}
```

### 5. POST /auth/update 更新激活码信息（管理接口）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auth_code | string | 是 | 要更新的激活码 |
| duration | integer | 否 | 更新有效期（天数），延期后会重新计算过期时间 |
| package_type | string | 否 | 更新套餐类型 |

响应：返回更新后的激活码信息

## 完整接口列表

| 接口 | 方法 | 用途 | 需要API Key |
|------|------|------|------------|
| `/auth/verify` | POST | 用户端验证激活码 | ✅ |
| `/auth/generate` | POST | 管理端生成新激活码 | ✅ |
| `/auth/list` | POST | 管理端列出所有激活码 | ✅ |
| `/auth/delete` | POST | 管理端删除激活码 | ✅ |
| `/auth/update` | POST | 管理端更新激活码信息 | ✅ |

## 项目结构

```
.
├── index.py             # 主程序入口
├── requirements.txt     # 依赖说明（无额外依赖）
└── README.md            # 部署说明
```

## 安全说明

1. **必须修改默认的 `API_KEY` 和 `ENCRYPTION_KEY`**，使用强随机字符串
2. API网关默认开启HTTPS，保持即可
3. 无需开启日志服务，节省费用
