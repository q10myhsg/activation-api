# Activation API - Chrome 插件激活码管理系统

一个完整的 Chrome 插件激活码验证系统，部署在腾讯云 Serverless 云函数，支持多客户端类型、多套餐、动态权限管理。

## 项目结构

本项目采用 **Git Submodule** 管理多个子项目：

```
activation-api/
├── docs/                              # 📚 项目文档
│   ├── 接口协议.md                     # 完整 API 接口文档
│   ├── api_key_design.md              # API Key 三级权限设计
│   └── 腾讯云函数Python开发经验.md      # 开发经验总结
│
├── xhs_helper_api_server/             # 🖥️ 服务端（腾讯云函数）
│   └── README.md                      # 部署文档
│
├── activation-admin/                  # 🔧 管理端（浏览器插件）
│   ├── popup.html/js/css              # 插件界面
│   └── README.md
│
└── xhs_helper_browser_extension/      # 📱 客户端（小红书助手）
    ├── content.js                     # 核心功能脚本
    ├── auth.js                        # 认证模块
    └── README.md
```

## 功能特性

### 服务端
- ✅ **激活码管理**：生成、查询、更新、删除
- ✅ **设备绑定**：一码一机，防止共享
- ✅ **多客户端支持**：浏览器插件、PC 客户端
- ✅ **多套餐类型**：basic、premium、vip 等
- ✅ **动态权限配置**：API 控制权限配额，无需改代码
- ✅ **有效期累计**：同一设备多次激活自动累计
- ✅ **三级 API Key**：客户端/管理端权限分离

### 管理端（浏览器插件）
- ✅ 生成激活码（批量）
- ✅ 查询激活码详情
- ✅ 列出激活码（支持筛选）
- ✅ 修改激活码（延期、更改套餐）
- ✅ 解除设备绑定
- ✅ 设备管理

### 客户端（小红书助手）
- ✅ 提示词管理（多平台支持）
- ✅ 小红书搜索优化
- ✅ 图片下载
- ✅ 激活码认证

## 快速开始

### 1. 克隆项目

```bash
# 克隆主仓库 + 所有子模块
git clone --recursive https://github.com/q10myhsg/activation-api.git

# 如果已经克隆，拉取子模块
git submodule update --init --recursive
```

### 2. 部署服务端

详细步骤见 [xhs_helper_api_server/README.md](./xhs_helper_api_server/README.md)

```bash
# 1. 创建腾讯云函数（北京地域，Python 3.9）
# 2. 打包上传代码
# 3. 配置环境变量
ADMIN_API_KEY=your-admin-key
CLIENT_API_KEYS=client-key-1,client-key-2
# 4. 添加 API 网关触发器
```

### 3. 安装管理端

```bash
# Chrome 浏览器
# 1. 打开 chrome://extensions/
# 2. 开启「开发者模式」
# 3. 点击「加载已解压的扩展程序」
# 4. 选择 activation-admin 目录
```

### 4. 安装客户端

同上，选择 `xhs_helper_browser_extension` 目录。

## 接口文档

完整接口文档见 [docs/接口协议.md](./docs/接口协议.md)

### 接口概览

| 接口 | 方法 | 用途 | 权限 |
|------|------|------|------|
| `/auth/verify` | POST | 验证激活码 | client |
| `/device/info` | POST | 查询设备状态 | client |
| `/auth/generate` | POST | 生成激活码 | admin |
| `/auth/list` | POST | 列出激活码 | admin |
| `/auth/info` | POST | 查询激活码详情 | admin |
| `/auth/update` | POST | 更新激活码 | admin |
| `/auth/delete` | POST | 删除激活码 | admin |
| `/device/list` | POST | 列出设备 | admin |
| `/device/unbind` | POST | 解除设备绑定 | admin |
| `/device/delete` | POST | 删除设备 | admin |
| `/permissions/list` | POST | 列出权限配置 | admin |
| `/permissions/set` | POST | 设置权限配置 | admin |

### 激活码格式

```
{duration}_{encrypted_string}
```

示例：
- `30_xxxxxxxxxxxx` - 30天有效期
- `-1_xxxxxxxxxxxx` - 永久有效

## API Key 设计

采用三级权限分离设计，详见 [docs/api_key_design.md](./docs/api_key_design.md)

| 级别 | 用途 | 权限范围 |
|------|------|----------|
| 客户端 Key | 浏览器插件/PC客户端 | `/auth/verify`, `/device/info` |
| 管理端 Key | 管理后台 | 所有接口 |
| 服务端 Key | 其他后端服务 | 按需授权 |

## 权限配额

根据 **客户端类型 + 套餐类型** 动态分配：

| 客户端 | 套餐 | 提示词限额 | 下载限额 | 高价值笔记 | 关键词拓展 |
|--------|------|-----------|---------|-----------|-----------|
| browser-extension | basic | 20/天 | 20/天 | 30/天 | 10/天 |
| browser-extension | premium | 50/天 | 20/天 | 100/天 | 50/天 |
| browser-extension | vip | 100/天 | 50/天 | 200/天 | 100/天 |
| pc-client | basic | 30/天 | 30/天 | 50/天 | 20/天 |
| pc-client | premium | 80/天 | 50/天 | 150/天 | 80/天 |

> `-1` 表示无限制

## 部署架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   客户端插件     │────▶│   API 网关      │────▶│   云函数服务     │
│  (Chrome/Edge)  │     │   (HTTPS)       │     │   (Python 3.9)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   SQLite 数据库  │
                                                │   (本地/CFS)     │
                                                └─────────────────┘
```

## 成本说明

| 项目 | 费用 |
|------|------|
| 云函数 | 免费额度足够 |
| SQLite | 免费（Python 自带） |
| CFS 文件存储（可选） | ~0.3元/GB/月 |
| API 网关 | 免费额度 |
| **总成本** | **接近零** |

## 开发文档

- [接口协议](./docs/接口协议.md) - 完整 API 文档
- [API Key 设计](./docs/api_key_design.md) - 三级权限方案
- [腾讯云函数开发经验](./docs/腾讯云函数Python开发经验.md) - 踩坑记录

## 子项目

| 项目 | 说明 | 地址 |
|------|------|------|
| activation-admin | 管理端浏览器插件 | [GitHub](https://github.com/q10myhsg/activation-admin) |
| xhs_helper_browser_extension | 小红书助手客户端 | [GitHub](https://github.com/q10myhsg/xhs_helper_browser_extension) |

## License

MIT

## Author

q10myhsg
