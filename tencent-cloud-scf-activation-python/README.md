# 腾讯云函数 - Chrome插件激活码接口（Python版）

基于腾讯云Serverless云函数Python 3.9实现的Chrome插件激活码管理接口。

## 部署要求

- **地域：** 北京（ap-beijing）
- **运行环境：** Python 3.9
- **日志服务：** 默认关闭（避免收费）

## 部署步骤

### 1. 创建云函数

1. 登录[腾讯云控制台](https://console.cloud.tencent.com/scf)，进入北京区域
2. 【云函数】→【函数服务】→【新建】
3. 配置：
   - 运行环境：Python 3.9
   - 创建方式：空白函数
   - 函数名称：`activation-api`
   - 地域：**北京**
   - 日志服务：取消勾选（**不要开启**，避免收费）
4. 上传代码：将 `index.py` 复制进去，或者打包zip上传

### 2. 配置环境变量

在云函数 → 【配置】→【环境变量】添加：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `API_KEY` | API调用密钥，设置为复杂随机字符串 | `your-strong-secret-key` |
| `ENCRYPTION_KEY` | 加密签名密钥，设置为随机字符串 | `your-encryption-secret` |
| `RATE_LIMIT` | 每分钟请求限制，默认60 | `60` |
| `MONGO_URI` | MongoDB连接URI（腾讯云MongoDB地址） | `mongodb://user:password@host:port/db` |
| `MONGO_DB` | 数据库名，默认 `activation_db` | `activation_db` |
| `MONGO_COLLECTION` | 集合名，默认 `activation_codes` | `activation_codes` |

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

## 接口说明

完全遵循协议设计：

### 请求头

必须携带：
- `X-API-Key: {你的API_KEY}`
- `Content-Type: application/json`

### 1. POST /auth/verify 验证激活码

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auth_code | string | 是 | 激活码 |
| machine_code | string | 是 | 设备唯一机器码 |
| plugin_version | string | 是 | 插件版本 |
| current_expiry_date | string | 否 | 当前存储的过期时间 |

**响应状态：**
- `valid`：有效，返回激活信息
- `invalid`：无效/格式错误
- `expired`：已过期
- `used`：已绑定其他设备

### 2. POST /auth/generate 生成激活码

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| duration | integer | 是 | 有效期：1/7/30/365/-1（永久） |
| count | integer | 否 | 生成数量，默认1 |
| package_type | string | 是 | 套餐类型 basic/premium |

**响应：** 返回生成的激活码数组

## 存储说明

已实现**持久化MongoDB存储**：
- ✅ 数据永久保存，云函数重启/重新部署不会丢失
- ✅ 自动降级：如果MongoDB连接失败，自动降级到内存存储，保证服务可用
- ✅ 使用腾讯云MongoDB时，建议开启VPC内网访问，更安全更快

### 准备MongoDB（腾讯云）：
1. 控制台购买[云数据库MongoDB](https://console.cloud.tencent.com/mongodb)
2. 创建数据库实例，选择和云函数相同的VPC网络
3. 创建数据库 `activation_db` 和集合 `activation_codes`
4. 获取连接URI，填写到环境变量 `MONGO_URI`

## 安全说明

1. **必须修改默认的 `API_KEY` 和 `ENCRYPTION_KEY`**，使用强随机字符串
2. API网关默认开启HTTPS，保持即可
3. 无需开启日志服务，节省费用

## 项目结构

```
.
├── index.py             # 主程序入口
├── requirements.txt     # Python依赖
└── README.md            # 部署说明
```

## 依赖安装

腾讯云函数会自动安装 `requirements.txt` 中的依赖，无需手动操作。
