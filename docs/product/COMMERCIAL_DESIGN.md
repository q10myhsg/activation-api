# 产品设计文档：xhs_helper_pc_server 商业化权限设计

**文件路径：** `docs/product/COMMERCIAL_DESIGN.md`

---

## 1. 需求概述

项目：小红书 PC 客户端自动化养号工具
- 核心功能：多设备自动化养号，提升账号存活率
- 商业化：分级授权收费，免费用户体验 + 付费用户解锁更多额度

---

## 2. 权限分级设计

| 套餐 | 价格 | 可接入设备数 | 每日总养时长限制 | 笔记创建 |
|------|------|-------------|------------------|----------|
| **免费版** | 0 元 | ✅ 可接入**多个设备** | ⚠️ 每日**累计 30 分钟**（所有设备合计） | ❌ 暂不支持 |
| **基础版** | 19 元/月<br>199 元/年 | ✅ **2 个设备** | ✅ 每日**累计 120 分钟**（2 小时） | ❌ 暂不支持 |
| **高级版** | 39 元/月<br>399 元/年 | ✅ **设备数无限制** | ✅ **时长无限制** | ❌ 暂不支持（后续开放） |

### 设计说明

1. **免费版策略**：
   - 允许接入多个设备，提升用户体验
   - 限制每日总时长，不限制设备接入数量
   - 满足个人小号用户日常需求，降低试用门槛

2. **梯度设计**：
   - 免费 → 基础 → 高级，满足不同用户规模
   - 个人用户够用，多账号用户不限设备时长，价格梯度合理

---

## 3. 设计要点 ✅

### ⚠️ 重要：所有套餐参数**不本地写死**，全部从云端获取

- 激活码验证接口返回完整权限配置：`max_devices` / `max_daily_minutes` / `package_type` / `expire_date`
- 本地只做缓存，不从新 hardcode
- 方便后台随时调整套餐配置，不需要客户端发版

---

## 4. 核心逻辑设计

### 4.1 启动前权限检查流程

```python
def check_can_start(device_id):
    # 1. 检查授权是否有效（从本地缓存读取）
    license = get_user_license()
    if not license or not license.active or is_expired(license.expire_date):
        return False, "授权已过期，请重新激活"
    
    # 2. 从license 获取套餐配置（云端返回的，本地缓存）
    max_devices = license.max_devices
    max_daily_minutes = license.max_daily_minutes
    
    # 3. 检查设备数量
    registered_devices = get_all_registered_devices()
    if len(registered_devices) > max_devices:
        return False, f"已达到最大设备数限制({max_devices})，请升级套餐"
    
    # 4. 检查今日累计时长
    today = get_today_str()
    usage = get_daily_usage(device_id, today)
    used_minutes = usage.total_minutes if usage else 0
    
    if used_minutes >= max_daily_minutes:
        return False, f"今日已累计使用 {used_minutes} 分钟，达到今日限额，请明天再来或升级套餐"
    
    # 5. 检查通过，可以启动
    return True, "可以启动"
```

### 4.2 使用时长统计

养号启动后：
```python
start_time = time.time()
do_nurturing()
end_time = time.time()
used_minutes = int((end_time - start_time) / 60)
if used_minutes < 1:
    used_minutes = 1  # 最少统计 1 分钟
update_daily_usage(device_id, get_today(), used_minutes)
```

### 4.3 激活码绑定流程

1. 用户在 Web 界面输入激活码
2. 客户端请求激活码 API 到 `activation-api` 验证
3. **验证返回完整套餐配置**：`max_devices` / `max_daily_minutes` / `expire_date` / `package_type`
4. 验证通过后，绑定本机机器码，**写入本地数据库缓存**，开通对应套餐权限
5. 每日启动需要联网验证一次授权状态，更新缓存配置

### 4.4 复用现有激活码体系

- 直接复用现有的 `xhs_helper_api` 激活码体系
- **套餐信息通过接口返回**，本地不硬编码，配置灵活
- 一套体系支撑所有产品（浏览器插件 / PC 客户端 / 未来其他客户端），不用重复开发

---

## 5. API 接口设计（对接 activation-api）

### 激活码验证接口

**请求：**
```json
{
  "auth_code": "xxxx-xxxx-xxxx",
  "machine_code": "client-pc-xxxxxxx",
  "client_type": "pc-client"
}
```

**响应：**
```json
{
  "status": "valid",
  "data": {
    "package_type": "basic",
    "expire_date": "2026-04-20",
    "max_devices": 2,
    "max_daily_minutes": 120
  }
}
```

**关键点：**
- 所有套餐限制参数都通过接口返回，**本地不写死**
- 增加 `client_type: "pc-client"` 区分客户端类型
- 云端统一控制，方便调整

---

## 6. 数据结构设计

### 数据表设计（SQLite 本地存储）

```sql
-- 设备基本信息
CREATE TABLE registered_devices (
    device_id TEXT PRIMARY KEY,
    device_alias TEXT,
    create_time TEXT NOT NULL,
    update_time TEXT NOT NULL,
    activated BOOLEAN DEFAULT 1
);

-- 每日使用统计
CREATE TABLE daily_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    use_date TEXT NOT NULL,         -- 'YYYY-MM-DD'
    total_minutes INTEGER DEFAULT 0,  -- 今日累计使用分钟
    start_count INTEGER DEFAULT 0,      -- 今日启动次数
    update_time TEXT NOT NULL,
    UNIQUE(device_id, use_date)
);

-- 用户授权信息（绑定激活码）
CREATE TABLE user_license (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activation_code TEXT UNIQUE NOT NULL,
    machine_code TEXT UNIQUE,        -- 绑定本机机器码
    package_type TEXT NOT NULL,       -- free / basic / premium
    expire_date TEXT NOT NULL,        -- 过期日期
    max_devices INTEGER NOT NULL,      -- 最大设备数（从云端获取）
    max_daily_minutes INTEGER NOT NULL, -- 最大每日时长（从云端获取）
    create_time TEXT NOT NULL,
    update_time TEXT NOT NULL,
    active BOOLEAN DEFAULT 1
);
```

---

## 7. 前端界面设计

### 激活页面
- 输入激活码输入框
- 激活按钮
- 显示当前套餐信息：套餐类型、过期时间、**套餐额度配置**
- 显示今日总已使用时长

### 设备列表
- 显示所有已接入设备
- 显示每个设备今日已用时长

---

## 补充设计细节

### 1. 权限检查设计

| 检查点 | 时机 | 是否联网 | 说明 |
|------|------|----------|------|
| **程序启动时检查** | Web 服务启动时 | ✅ 一次联网验证 | 更新本地缓存授权，过期提示重新激活 |
| **养号启动前检查** | 每次点击启动养号时 | ❌ 不需要联网 | 使用本地缓存数据检查，高效 |

**设计优势**
- 避免频繁联网 → 本地检查快速，用户体验好
- 启动服务时联网更新一次 → 保证授权信息最新
- 断网也能使用（只要缓存没过期）

---

### 2. 使用时长统计方案

#### 统计方式

```
启动养号 → 记录开始时间戳 → 执行养号 → 养号结束（正常结束/异常退出）→ 计算实际使用分钟数 → 写入本地 SQLite
```

#### 异常处理（程序被杀死）

**方案：** 使用 `atexit` 注册退出钩子 + 全局记录开始时间/当前设备

```python
import atexit
start_time = None
current_device_id = None

def exit_hook():
    """程序退出时自动统计时长"""
    global start_time, current_device_id
    if start_time and current_device_id:
        end_time = time.time()
        used_minutes = int((end_time - start_time) / 60)
        if used_minutes < 1:
            used_minutes = 1  # 最少算 1 分钟
        update_daily_usage(current_device_id, get_today(), used_minutes)
```

**保证：** 无论正常结束还是用户杀死进程，都会统计时长，不会漏统计。

---

### 3. 数据定期清理

#### 清理规则
- 保留 **最近 7 天** 的 `daily_usage` 数据
- 每次添加新记录后，自动删除 7 天前的数据
- 节省本地存储空间，避免数据越来越大

#### 清理代码逻辑

```python
def clean_old_records(conn):
    """删除 7 天前的每日统计记录"""
    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    conn.execute("DELETE FROM daily_usage WHERE use_date < ?", (seven_days_ago,))
    conn.commit()
```

每次新增记录后执行一次清理，自动保持数据干净。

---

### 4. 默认配置设计（断网/未激活处理）

#### 默认配置（未激活时）
```python
DEFAULT_FREE_LICENSE = {
    "package_type": "free",
    "expire_date": None,       # 永不过期（免费版永远有效）
    "max_devices": 1,         # 免费版 1 个设备
    "max_daily_minutes": 30   # 免费版每日 30 分钟
}
```

#### 断网处理
- 程序启动联网更新失败 → 使用本地缓存授权
- 如果本地没有缓存 → 使用上面默认免费配置
- 永远不会完全不能用，就算断网也能继续用免费额度

---

### 5. 前端页面设计

#### 新增「授权」标签页

**包含元素：**
1. **激活码输入框** - 用户输入激活码
2. **激活按钮** - 提交激活
3. **当前授权信息展示**
   - 套餐类型
   - 过期日期
   - 最大设备数
   - 最大每日分钟数
   - 今日已用分钟数
4. **设备列表**
   - 设备名称
   - 今日已用时长
   - 剩余时长

#### 导航栏
原来的导航增加「授权」标签，顺序：
`主页 → 设备管理 → 关键词 → 授权 → 配置`

---

## 总结

| 项目 | 状态 |
|------|------|
| 数据结构设计 | ✅ 完成 |
| 核心逻辑设计 | ✅ 完成 |
| **所有参数云端配置，本地不写死** | ✅ 确认 |
| **异常处理（进程杀死计时）** | ✅ 完成 |
| **定期数据清理（保留 7 天）** | ✅ 完成 |
| **默认配置（断网降级可用）** | ✅ 完成 |
| API 接口设计 | ✅ 完成 |
| 前端界面设计要点 | ✅ 完成 |
| 复用现有激活码体系 | ✅ 完成 |

服务端开发可以按照这个设计进行开发联调 👍
