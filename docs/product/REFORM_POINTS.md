# 改造点整理：xhs_helper_pc_server 新增商业化权限

## 概述

当前代码已有基础框架，需要**增量改造**新增商业化权限分级功能，按照 `docs/product/COMMERCIAL_DESIGN.md` 设计实现。

---

## 需要改造的点

| 序号 | 改造点 | 说明 | 优先级 |
|------|---------|------|----------|
| 1 | **新增数据表** | 创建 `daily_usage` 和 `user_license` 两张本地 SQLite 表 | 🔥 P0 |
| 2 | **激活码验证模块** | 新增激活码输入页面，调用云端 `activation-api` 验证，获取权限配置保存到本地 | 🔥 P0 |
| 3 | **启动权限检查** | 启动养号前检查：<br>• 授权是否过期 <br>• 是否超过设备数量限制 <br>• 是否超过今日时长限制 <br>• 不通过拒绝启动 | 🔥 P0 |
| 4 | **使用时长统计** | 启动/停止统计时长，累加到每日统计 | 🔥 P0 |
| 5 | **前端页面改造** | <br>• 新增激活标签页 <br>• 显示当前授权信息（套餐、过期时间、额度配置） <br>• 设备列表显示每个设备今日已用时长 | 🔥 P0 |
| 6 | **云端配置** | 所有权限配置从接口获取，本地缓存，不写死 | 🔥 P0 |

---

## 当前代码已有能力 ✅

- Flask Web 框架 ✓
- 设备管理模块 ✓
- 配置存储模块 ✓
- 网络请求能力 ✓
- 本地 SQLite 存储 ✓

**结论**：不需要重构现有结构，**增量开发**即可完成。

---

## 对接信息

### 云端接口

**激活码验证接口请求**
```json
POST {activation-api}/auth/verify
Content-Type: application/json

{
  "auth_code": "用户输入的激活码",
  "machine_code": "本机唯一机器码",
  "client_type": "pc-client"
}
```

**激活码验证接口响应**（成功）
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

### 数据库设计

```sql
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

-- 用户授权信息
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
