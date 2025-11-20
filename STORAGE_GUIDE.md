# Storage Architecture Guide

## 概述

Daily AI Insight 支持**混合存储架构**，默认使用**本地文件存储 + Git 自动提交**，同时支持切换到 Cloudflare KV 等云存储后端。

## 架构设计

```
应用层 (CLI/Collectors/Analyzer)
         │
         ▼
   StorageBackend (抽象接口)
         │
    ┌────┴────┬─────────┐
    │         │         │
FileStorage  KVStorage  (更多后端...)
    │
    └─► GitSync (自动提交)
```

## 功能特性

### ✅ 已实现的后端

1. **FileStorage (默认)**
   - 本地文件系统存储
   - 三层目录结构（data/processed/archives）
   - 自动 Git 提交归档报告
   - 支持自动推送到远程
   - 灵活的查询和清理

2. **KVStorage (可选)**
   - Cloudflare KV 云存储
   - 自动 TTL 过期
   - 全球分布式访问
   - 无需维护

### 🔧 配置方式

#### 方法 1: 环境变量（推荐）

```bash
# .env
STORAGE_BACKEND=file              # 或 kv
STORAGE_PATH=storage              # 本地存储路径
STORAGE_GIT_SYNC=true             # 自动 Git 提交
STORAGE_AUTO_PUSH=false           # 自动推送到远程

# Cloudflare KV 配置（可选）
# CF_ACCOUNT_ID=your_account_id
# CF_KV_NAMESPACE_ID=your_namespace_id
# CF_API_TOKEN=your_api_token
```

#### 方法 2: 代码配置

```python
from daily_ai_insight.storage import create_storage

# 默认：本地存储 + Git
storage = create_storage()

# 显式配置
storage = create_storage(
    backend="file",
    base_path="storage",
    git_sync=True,
    auto_push=False
)

# Cloudflare KV
storage = create_storage(backend="kv")
```

## 使用示例

### 基本操作

```python
import asyncio
from daily_ai_insight.storage import create_storage

async def main():
    storage = create_storage()

    # 保存原始数据（临时，不提交 Git）
    items = [{"title": "Item 1", "content": "..."}]
    await storage.save_raw(items, source="reddit")

    # 保存处理后数据（临时，不提交 Git）
    analysis = {"summary": "..."}
    await storage.save_processed(analysis, report_type="daily")

    # 保存最终报告（提交到 Git）
    report = "# Daily Report\n\n..."
    report_path = await storage.save_report(report)
    print(f"Report saved and committed: {report_path}")

    # 加载最近数据
    recent = await storage.load_recent(hours=24)
    print(f"Found {len(recent)} recent items")

    # 清理旧文件
    await storage.cleanup(days=7)

asyncio.run(main())
```

### CLI 使用

```bash
# 使用默认配置（本地 + Git）
uv run daily-ai-insight analyze

# 切换到 KV（修改 .env 后）
STORAGE_BACKEND=kv uv run daily-ai-insight analyze

# 清理旧文件
uv run python -m daily_ai_insight --cleanup
```

## 目录结构

```
storage/
├── .gitignore           # 自动生成
├── data/               # 原始数据（本地临时，不提交）
│   ├── reddit_20251120_143000.json
│   └── github_20251120_143010.json
├── processed/          # 处理后数据（本地临时，不提交）
│   └── daily_2025-11-20.json
└── archives/           # 最终报告（提交到 Git）
    ├── report_2025-11-20.md
    └── report_2025-11-21.md
```

## Git 集成

### 自动提交流程

1. **数据收集** → `storage/data/` (不提交)
2. **数据处理** → `storage/processed/` (不提交)
3. **生成报告** → `storage/archives/` ✅ **自动提交**

### Git 提交消息格式

```
feat: daily report 2025-11-20

🤖 Generated with daily-ai-insight

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 自动推送到 GitHub

```bash
# .env
STORAGE_AUTO_PUSH=true  # ⚠️ 谨慎使用！
```

或手动推送：

```bash
git push origin main
```

## 场景选择

### 📁 使用本地存储 + Git（推荐）

**适合：**
- ✅ 个人项目
- ✅ 需要版本控制
- ✅ 想要完全控制数据
- ✅ 使用 GitHub Actions 自动化

**配置：**
```bash
STORAGE_BACKEND=file
STORAGE_GIT_SYNC=true
```

### ☁️ 使用 Cloudflare KV

**适合：**
- ✅ 部署在 Cloudflare Workers
- ✅ 需要全球分布式访问
- ✅ 不关心历史版本
- ✅ 临时数据存储

**配置：**
```bash
STORAGE_BACKEND=kv
CF_ACCOUNT_ID=xxx
CF_KV_NAMESPACE_ID=xxx
CF_API_TOKEN=xxx
```

### 🔀 混合方案

```python
from daily_ai_insight.storage import FileStorage, KVStorage

# 临时数据用 KV
kv = KVStorage()
await kv.save_raw(items, source="temp")

# 最终报告用本地 + Git
local = FileStorage(git_sync=True)
await local.save_report(report)  # 自动提交
```

## 成本对比

| 方案 | 存储 | 带宽 | 运行成本 | 总结 |
|------|------|------|---------|------|
| **本地 + GitHub** | 免费无限 | 免费 | GitHub Actions 2000分钟/月 | **完全免费** |
| **Cloudflare KV** | 免费 1GB | 免费 100k 读/天 | Workers 免费 100k 请求/天 | **免费额度大** |
| **云服务器** | $5-20/月 | 按量 | $5-50/月 | 成本较高 |

## 迁移指南

### 从旧版 StorageManager 迁移

**旧代码：**
```python
from daily_ai_insight.storage import StorageManager

storage = StorageManager()
storage.save_raw_data(items, source="test")
storage.load_recent_data(hours=24)
```

**新代码：**
```python
from daily_ai_insight.storage import create_storage

storage = create_storage()  # 自动读取 .env
await storage.save_raw(items, source="test")
await storage.load_recent(hours=24)
```

### 向后兼容

旧的 `StorageManager()` 仍然可用（会显示 deprecation 警告）：

```python
# 仍然有效，但会警告
from daily_ai_insight.storage import StorageManager
storage = StorageManager()  # 返回 FileStorage 实例
```

## 高级功能

### 1. 禁用 Git 自动提交

```python
storage = create_storage(backend="file", git_sync=False)
```

### 2. 自定义存储路径

```python
storage = create_storage(
    backend="file",
    base_path="/custom/path"
)
```

### 3. 查询历史数据

```python
from datetime import datetime, timedelta

# 按模式查询
results = await storage.query("reddit_*.json")

# 按日期范围查询
start = datetime.now() - timedelta(days=7)
results = await storage.query(
    "*.json",
    start_date=start
)
```

### 4. 获取统计信息

```python
stats = storage.get_statistics()
print(f"Raw files: {stats['raw_files']}")
print(f"Storage size: {stats['total_size_mb']} MB")
```

## 故障排查

### Git 提交失败

**症状：** 看到 "Git commit skipped" 警告

**原因：**
- Git 未初始化
- 不在 Git 仓库中
- Git 配置缺失

**解决：**
```bash
git init
git config user.name "Your Name"
git config user.email "your@email.com"
```

### KV 认证失败

**症状：** `ValueError: Missing Cloudflare credentials`

**解决：** 确保 `.env` 包含：
```bash
CF_ACCOUNT_ID=...
CF_KV_NAMESPACE_ID=...
CF_API_TOKEN=...
```

### 文件权限错误

**症状：** `PermissionError` 创建目录失败

**解决：**
```bash
chmod +w storage/
# 或指定其他路径
STORAGE_PATH=/tmp/storage uv run daily-ai-insight analyze
```

## 测试

运行存储测试：

```bash
# 所有存储测试
uv run pytest tests/unit/test_storage.py -v

# 只测试文件存储
uv run pytest tests/unit/test_storage.py::TestFileStorage -v

# 只测试 KV 存储
uv run pytest tests/unit/test_storage.py::TestKVStorage -v
```

## 扩展新后端

添加新的存储后端（如 S3）：

1. 创建 `src/daily_ai_insight/storage/backends/s3.py`
2. 实现 `StorageBackend` 协议
3. 在 `create_storage()` 添加分支
4. 添加测试

示例骨架：

```python
# backends/s3.py
class S3Storage:
    async def save_raw(self, items, source, metadata=None): ...
    async def save_processed(self, data, report_type="daily"): ...
    async def save_report(self, content, format="markdown"): ...
    async def load_recent(self, hours=24): ...
    async def query(self, pattern, start_date=None, end_date=None): ...
    async def cleanup(self, days=7): ...
    def get_statistics(self): ...
```

## 总结

✅ **默认方案：本地文件 + Git**
- 零成本
- 完全控制
- 版本历史
- GitHub Actions 自动化

✅ **可选方案：Cloudflare KV**
- 全球分布
- 自动过期
- 无需维护

✅ **灵活架构**
- 配置驱动
- 运行时切换
- 易于扩展

---

更新时间：2025-11-20
