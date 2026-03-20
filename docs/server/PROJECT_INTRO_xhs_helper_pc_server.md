# xhs_helper_pc_server 项目说明

小红书自动化智能养号系统 - PC服务端

## 项目概述

基于 Python + uiautomator2 开发，支持多 Android 设备并发自动化养号，通过 Web 界面进行管理。

---

## 项目结构

```
xhs_helper_pc_server/
├── app.py                 # 主入口（精简版）
├── app2.py                # 主入口（完整版，包含笔记创建）
├── config/                # 配置存储目录
│   ├── config.json       # 设备配置
│   └── llm_config.json   # LLM 配置
├── config_manager.py      # 配置管理模块
├── create_notes/          # 笔记创建模块
│   ├── example_xhs_parser.py
│   └── xhs_parser.py
├── requirements.txt       # 依赖列表
├── static/               # 静态资源
├── templates/            # HTML 模板
├── tests/                # 测试文件
├── utils.py              # 工具函数
└── xhs_nurturing/       # 养号核心模块
    ├── __init__.py
    ├── browse_manager.py       # 浏览管理
    ├── config_manager.py       # 配置管理
    ├── device_manager.py       # 设备管理
    ├── interaction_manager.py  # 互动管理
    ├── nurturing_manager.py    # 养号流程调度
    └── utils.py               # 工具函数
```

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 多设备管理 | 支持同时连接管理多个 Android 设备，独立调度 |
| 智能养号流程 | 启动发现 → 随机浏览 → 关键词搜索 → 访问笔记 → 模拟互动，全自动化 |
| 关键词管理 | Web 界面增删查改，支持批量导入 |
| 行为模拟 | 随机点赞/收藏/评论，模拟真实用户行为 |
| 参数化配置 | 可配置时长、比例、概率，灵活调整策略 |
| Web 管理界面 | 可视化操作，不用命令行 |

---

## 技术栈

- **自动化控制**: uiautomator2 + ADB
- **Web 框架**: Flask
- **部署**: 本地 PC 服务器部署
- **支持系统**: Linux / macOS / Windows

---

## 目前状态

- ✅ 核心养号流程已完成
- ✅ Web 管理界面可用
- ✅ 模块化设计，易扩展
- ✅ 2026-03-20 修复完成：语法错误、安全认证、并发控制

---

## 产品路线规划

### 📅 近期 1周 计划（P0）

| 任务 | 优先级 | 目标 |
|------|----------|------|
| 测试验证完整养号流程 | 🔥 P0 | 验证单设备/多设备流程跑通 |
| 修复发现的交互bug | 🔥 P0 | 确保自动化操作稳定性 |
| 完善日志记录 | 🔥 P0 | 便于问题排查 |
| API Key 验证文档补充 | ⭐ P1 | 更新使用说明 |

### 📆 中期 3个月 计划

| 任务 | 优先级 | 目标 |
|------|----------|------|
| 笔记创建功能集成 | 🔥 P0 | 支持自动发布笔记 |
| 数据分析面板 | ⭐ P1 | 统计每日养号数据，可视化展示 |
| 预约定时养号 | ⭐ P1 | 支持按时间段定时执行 |
| 互动话术 AI 生成 | ⭐ P1 | 接入 LLM 自动生成评论内容 |
| Docker 容器化部署 | ⭐ P2 | 方便一键部署 |

### 📍 长期 1年 规划

| 阶段 | 目标 |
|------|------|
| **MVP 阶段** | ✅ 已完成 - 基础养号功能可用 |
| **功能完善** | 增加笔记创建、数据分析、定时任务 |
| **体验优化** | 优化 UI 界面，提升稳定性，增加异常重试 |
| **生态扩展** | 支持更多平台，支持策略分享社区 |

---

## 安装使用

### 环境准备

- Python 3.7+
- Android 设备（Android 7.0+）
- ADB 工具
- 网络连接

### 启动服务

```bash
# 克隆项目
git clone https://github.com/q10myhsg/xhs_helper_pc_server
cd xhs_helper_pc_server

# 安装依赖
pip install -r requirements.txt

# 安装 uiautomator2
pip install uiautomator2

# 初始化 uiautomator2（需要连接设备）
python -m uiautomator2 init

# 启动服务
python app.py
```

服务运行在 `http://0.0.0.0:5002`，浏览器访问即可使用。

---

## 注意事项

1. **设备要求**：Android 7.0+，需要启用 USB 调试
2. **权限**：设备需要授予 ATX 应用必要权限
3. **合规性**：请遵守小红书用户协议，合理使用自动化功能

---

## 许可证

MIT License
