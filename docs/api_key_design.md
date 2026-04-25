# API Key 安全设计方案 - 三级权限分离

## 设计目标

1. **权限分离**：客户端 / 服务端 / 管理端 使用不同的API Key，每个端只有必需权限
2. **最小权限原则**：客户端Key无法访问管理接口，就算泄露影响范围可控
3. **动态可管理**：支持随时添加/删除API Key，不需要修改代码
4. **可审计**：每个Key可以对应到使用者，方便追踪
5. **可吊销**：单个Key泄露可以单独吊销，不影响其他Key

## 三级API Key 结构

| 级别 | 用途 | 允许访问接口 | 泄露影响 | 推荐轮换频率 |
|------|------|--------------|------------|--------------|
| **客户端API Key** | 浏览器插件 / PC客户端 调用公开接口（verify/device/info） | 用户端接口（`/auth/verify`, `/device/info`） | 只能调用用户端接口，无法管理激活码，影响可控 | 数月（如果泄露单独删除即可） |
| **管理端API Key** | 管理后台调用生成/删除/修改激活码 | 所有管理接口（`/auth/generate`, `/auth/list`, `/auth/delete` 等） | 完全控制激活码，影响很大 | 严格保密，3-6个月轮换 |
| **服务端API Key** | 其他后端服务调用本API | 需要的用户端接口 | 取决于授权范围 | 按需轮换 |

## 环境变量配置

在腾讯云函数 → 配置 → 环境变量 中配置：

```env
# 客户端API Key，支持多个，逗号分隔
CLIENT_API_KEYS=client_dev_key_1,client_dev_key_2
# 管理端API Key，只能有一个（仅管理员用）
ADMIN_API_KEY=your_secure_admin_key_here
# 服务端API Key（可选，有其他服务调用时配置）
# SERVER_API_KEY=your_server_key_here
```

## 权限控制表

| 接口路径 | 允许的Key级别 |
|---------|---------------|
| `/auth/verify` | client, server, admin |
| `/device/info` | client, server, admin |
| `/auth/generate` | admin |
| `/auth/info` | admin |
| `/auth/list` | admin |
| `/auth/update` | admin |
| `/auth/delete` | admin |
| `/device/list` | admin |
| `/device/unbind` | admin |
| `/device/delete` | admin |

## 代码实现

### 1. 配置读取

```python
# 读取环境变量
CONFIG = {
    # ... 其他配置
    "admin_api_key": os.environ.get("ADMIN_API_KEY", ""),
    "client_api_keys": [k.strip() for k in os.environ.get("CLIENT_API_KEYS", "").split(",") if k.strip()],
}

# 如果没配置客户端Key，允许空（开发环境）
if len(CONFIG["client_api_keys"]) == 0:
    CONFIG["client_api_keys"] = ["test"]
```

### 2. API Key 验证

```python
def verify_api_key(request_api_key):
    """Verify API key and return role
    Returns:
        (role, is_valid)
        role: "admin" / "client" / "server" / None
        is_valid: bool
    """
    if not request_api_key:
        return None, False
    
    request_api_key = request_api_key.strip()
    
    # 检查管理端
    if request_api_key == CONFIG["admin_api_key"]:
        return "admin", True
    
    # 检查客户端
    if request_api_key in CONFIG["client_api_keys"]:
        return "client", True
    
    # 检查服务端
    if "server_api_key" in CONFIG and request_api_key == CONFIG["server_api_key"]:
        return "server", True
    
    return None, False
```

### 3. 主入口认证

```python
# 兼容大小写不同的header名称
request_api_key = None
for header_name, header_value in event.get("headers", {}).items():
    if header_name.lower() == "x-api-key":
        request_api_key = header_value
        break

role, valid = verify_api_key(request_api_key)
if not valid:
    return {
        "statusCode": 401,
        "headers": headers,
        "body": json.dumps({
            "status": "error",
            "message": "API Key invalid",
            "data": None
        }, ensure_ascii=False)
    }

# 权限检查
path = event.get("path", "")
if path.endswith("/auth/generate") and role != "admin":
    return {
        "statusCode": 403,
        "headers": headers,
        "body": json.dumps({
            "status": "error",
            "message": "Forbidden: this endpoint requires admin role",
            "data": None
        }, ensure_ascii=False)
    }
# 对其他管理接口重复上述检查...
```

## 使用方式

### 开发联调阶段

```env
# 所有开发人员共用一个客户端Key，方便调试
CLIENT_API_KEYS=dev_shared_key
ADMIN_API_KEY=admin_dev_key
```

### 生产发布阶段

- 每个分发渠道/每个用户使用不同的客户端API Key
- 在环境变量中逗号分隔添加
- 如果某个Key泄露或滥用，直接从环境变量中删除，重新部署云函数即可吊销
- 添加新Key只需要添加到环境变量，重新部署

示例：
```env
CLIENT_API_KEYS=user_alice_key,user_bob_key,dist_channel_github_key
ADMIN_API_KEY=my_secure_admin_key
```

## 安全增强建议

1. **强制HTTPS**：腾讯云API网关默认开启，保持即可 ✅
2. **足够长度**：API Key至少使用32位随机字符串
3. **日志不记录**：代码中不要把API Key写入日志
4. **频率限制**：已实现频率限制，防止暴力枚举
5. **定期轮换**：管理端Key建议3-6个月轮换一次
6. **WAF防护**：腾讯云开启WAF，防止恶意爬取

## 对比其他方案

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **三级API Key（本方案）** | 实现简单，权限清晰，动态可管理 | 客户端Key长期有效 | 激活码API项目，非常适合 |
| JWT Token | 客户端不需要长期存储Key，短期Token过期自动失效 | 需要改认证流程，引入PyJWT依赖 | 更优雅，但复杂度高一点 |
| OAuth2.0 | 标准协议，功能强大 | 过于复杂，不适合这个项目 | 大型多服务系统 |

## 总结

**三级API Key** 方案适合当前激活码API项目：
- ✅ 实现简单，不需要改数据库
- ✅ 权限分离，最小权限原则
- ✅ 动态添加删除Key，方便管理
- ✅ 泄露影响可控，可单独吊销
- ✅ 符合项目规模，不会过度设计

