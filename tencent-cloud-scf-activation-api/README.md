# 腾讯云函数 - Chrome插件激活码接口

基于腾讯云Serverless云函数实现的Chrome插件激活码管理接口，包含激活码验证和生成功能。

## 功能特性

- ✅ 激活码验证：检查有效性、过期时间、设备绑定状态
- ✅ 生成激活码：支持自定义有效期（1/7/30/365天、永久），可批量生成
- ✅ API Key鉴权：保证接口安全
- ✅ 请求频率限制：防止接口滥用
- ✅ 跨域支持：支持浏览器端直接调用
- ✅ AES加密：激活码采用AES-256加密存储

## 部署步骤

### 1. 创建云函数

1. 登录[腾讯云控制台](https://console.cloud.tencent.com/scf)
2. 进入【云函数】->【函数服务】->【新建】
3. 选择：
   - 运行环境：Node.js 16.x/18.x/20.x
   - 创建方式：空白函数
   - 函数名称：`activation-api`
   - 提交方式：本地上传zip包
4. 将代码打包为zip上传（或者在线编辑粘贴index.js内容）

### 2. 配置环境变量

在云函数【配置】->【环境变量】中添加：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `API_KEY` | API调用密钥，请设置为复杂随机字符串 | `your-secret-api-key-xxx` |
| `ENCRYPTION_KEY` | AES加密密钥，请设置为随机字符串 | `your-encryption-secret-xxx` |
| `RATE_LIMIT` | 每分钟请求限制，默认60 | `60` |

### 3. 配置API网关触发器

1. 在云函数【触发方式】->【添加触发器】
2. 选择【API网关】
3. 配置：
   - 发布环境：发布
   - API类型：公网URL
   - 请求方法：ANY
   - 跨域配置：启用（代码中已处理，也可以在API网关配置）
4. 创建完成后会得到一个公网访问地址，比如：`https://xxxx-xxxx.gz.apigw.tencentcs.com/release/`

你的接口地址就是：
- 验证激活码：`https://xxxx-xxxx.gz.apigw.tencentcs.com/release/auth/verify`
- 生成激活码：`https://xxxx-xxxx.gz.apigw.tencentcs.com/release/auth/generate`

### 4. 持久化存储说明

当前代码使用**内存存储**，云函数重启/重新部署后数据会丢失。生产环境建议：

- 对接腾讯云MongoDB（云数据库MongoDB）
- 或者使用腾讯云Redis
- 或者使用腾讯云对象存储COS存储JSON文件

修改`activationCodes`的读写逻辑即可。

## 接口调用说明

### 请求头

所有请求需要携带API Key：
```
X-API-Key: your-api-key-here
```
Content-Type: `application/json`

### 1. 验证激活码 /auth/verify

**请求示例**:
```json
{
  "auth_code": "30_xxxencryptedxxx",
  "machine_code": "abc123def456",
  "plugin_version": "1.0.0",
  "current_expiry_date": "2026-04-16T12:00:00Z"
}
```

**响应示例**:
```json
{
  "status": "valid",
  "message": "激活码验证成功",
  "data": {
    "expiry_date": "2026-04-16T12:00:00Z",
    "activated_date": "2026-03-16T12:00:00Z",
    "machine_code": "abc123def456"
  }
}
```

状态说明：
- `valid`: 有效
- `invalid`: 无效
- `expired`: 过期
- `used`: 已被其他设备使用

### 2. 生成激活码 /auth/generate

**请求示例**:
```json
{
  "duration": 30,
  "count": 5,
  "package_type": "premium"
}
```
参数说明：
- `duration`: 有效期天数，支持 `1`、`7`、`30`、`365`、`-1`（永久）
- `count`: 生成数量，默认1
- `package_type`: 套餐类型（basic/premium等）

**响应示例**:
```json
{
  "status": "success",
  "message": "成功生成 5 个激活码",
  "data": {
    "auth_codes": [
      "30_xxx1",
      "30_xxx2"
    ],
    "duration": 30,
    "generate_date": "2026-03-16T12:00:00Z"
  }
}
```

## 本地测试

可以使用`serverless`工具本地测试：

```bash
npm install -g serverless
serverless login
# 本地运行
serverless offline
```

## 安全建议

1. 修改默认的 `API_KEY` 和 `ENCRYPTION_KEY` 为复杂随机字符串
2. 腾讯云API网关开启HTTPS（默认已经开启）
3. 如果对接数据库，使用腾讯云VPC内网访问，不要暴露数据库公网
4. 定期备份激活码数据

## License

MIT
