# 混合来源收集器使用指南

## 📚 概述

当你在 Follow.is 中创建一个 **List**，包含多个不同来源（Twitter、微博、Reddit 等）的内容时，**不需要为每个来源创建单独的收集器**。

现有的 `FollowCollector` 架构已经完美支持混合来源！

## 🏗️ 架构原理

### Follow.is List vs Feed

- **Feed**: 单一数据源（如一个 RSS feed）
- **List**: 多个 Feed 的聚合集合

### API 数据结构

当使用 `listId` 获取数据时，API 会自动包含每个 item 的来源信息：

```json
{
  "data": [
    {
      "entries": {
        "id": "123",
        "title": "内容标题",
        "author": "作者名",
        "publishedAt": "2025-11-25T03:00:00Z"
      },
      "feeds": {
        "title": "Twitter @作者名",  ← 来源标识
        "type": "feed",
        "url": "rsshub://twitter/user/..."
      }
    }
  ]
}
```

### FollowCollector 的处理

`FollowCollector` 基类会：
1. 从每个 item 的 `feeds` 字段提取来源信息
2. 使用 `custom_source_format` 函数格式化来源名称
3. 在最终数据中保留 `source` 和 `_metadata.feed_title` 字段

## 🎯 创建混合来源收集器

### 步骤 1: 创建收集器类

```python
# src/daily_ai_insight/collectors/ai_mixed.py

from .base import FollowCollector

class AIMixedCollector(FollowCollector):
    """Collect AI content from mixed sources."""

    def __init__(self):
        def format_mixed_source(author, feeds):
            """智能识别并格式化不同来源."""
            feed_title = feeds.get("title", "")
            feed_url = feeds.get("url", "")

            # 根据 URL 或标题识别来源
            if "twitter" in feed_url.lower():
                return f"twitter-{author}"
            elif "weibo" in feed_url.lower():
                return f"weibo-{author}"
            elif "reddit" in feed_url.lower():
                return f"reddit-{author}"
            else:
                return f"{feed_title} - {author}"

        super().__init__(
            name="ai_mixed",
            list_id_env="AI_MIXED_LIST_ID",
            source_name="AI Mixed Sources",
            home_url="https://app.follow.is",
            item_type="article",
            custom_source_format=format_mixed_source
        )
```

### 步骤 2: 配置环境变量

在 `.env` 中添加：

```bash
# Follow.is List ID (包含多个来源)
AI_MIXED_LIST_ID=your_list_id_here

# Follow.is Cookie
FOLO_COOKIE=your_cookie_here
```

### 步骤 3: 注册收集器

在 `__init__.py` 中导出：

```python
from .ai_mixed import AIMixedCollector

__all__ = [
    # ...
    "AIMixedCollector",
]
```

### 步骤 4: 使用收集器

```python
from daily_ai_insight.collectors import AIMixedCollector

# 初始化
collector = AIMixedCollector()

# 获取数据
data = await collector.fetch()

# 查看结果
for item in data["items"]:
    print(f"来源: {item['source']}")
    print(f"标题: {item['title']}")
    print(f"作者: {item['authors']}")
    print(f"详细来源: {item['_metadata']['feed_title']}")
    print()
```

## 📊 输出示例

```python
{
    "title": "Claude Opus 4.5 发布了",
    "url": "https://x.com/someone/status/123",
    "source": "twitter-张三",  # 自定义格式化后的来源
    "authors": [{"name": "张三"}],
    "_metadata": {
        "type": "article",
        "feed_title": "Twitter @张三"  # 原始来源信息
    }
}

{
    "title": "AI 最新进展",
    "url": "https://weibo.com/123/456",
    "source": "weibo-李四",  # 自动识别为微博
    "authors": [{"name": "李四"}],
    "_metadata": {
        "feed_title": "微博 @李四"
    }
}
```

## 🎨 高级自定义

### 场景 1: 按主题分类

```python
def format_by_topic(author, feeds):
    """按主题分类来源."""
    feed_title = feeds.get("title", "").lower()

    # 识别主题
    if "research" in feed_title or "paper" in feed_title:
        return f"研究-{author}"
    elif "news" in feed_title:
        return f"新闻-{author}"
    else:
        return f"其他-{author}"
```

### 场景 2: 保留完整来源

```python
def format_full_source(author, feeds):
    """保留完整的来源信息."""
    return feeds.get("title", "Unknown")
```

### 场景 3: 简化来源

```python
def format_simple(author, feeds):
    """只显示作者名."""
    return author if author else "Anonymous"
```

## 💡 最佳实践

### 1. List 组织建议

在 Follow.is 中创建主题明确的 List：
- ✅ "AI 资讯" List: 聚合 AI 相关的 Twitter、微博、博客
- ✅ "技术前沿" List: 聚合技术论文、GitHub、Reddit
- ❌ 不要: 把所有内容混在一个 List 里

### 2. 来源识别策略

优先级顺序：
1. **Feed URL** (最可靠): `rsshub://twitter/...`
2. **Feed Title** (次可靠): `"Twitter @用户名"`
3. **Entry 字段** (作为补充): author, url pattern

### 3. 测试建议

```python
# 测试不同来源的格式化
test_cases = [
    {
        "author": "张三",
        "feeds": {"title": "Twitter @张三", "url": "rsshub://twitter/..."}
    },
    {
        "author": "李四",
        "feeds": {"title": "微博 @李四", "url": "rsshub://weibo/..."}
    }
]

for case in test_cases:
    result = format_mixed_source(case["author"], case["feeds"])
    print(f"输入: {case['feeds']['title']}")
    print(f"输出: {result}\n")
```

## 🔧 故障排除

### 问题 1: 所有 item 的 source 都一样

**原因**: `custom_source_format` 函数没有正确识别不同来源

**解决**: 打印 `feeds` 字段，检查实际的数据格式：

```python
def format_mixed_source(author, feeds):
    print(f"DEBUG - feeds: {feeds}")  # 调试输出
    # ... 格式化逻辑
```

### 问题 2: 某些来源没有被识别

**原因**: 识别逻辑不完整

**解决**: 添加更多识别条件，并提供默认分支：

```python
# 添加 fallback
if "twitter" in url:
    return "twitter"
elif "weibo" in url:
    return "weibo"
else:
    # 默认：使用 feed title
    return feeds.get("title", "Unknown")
```

## 🚀 现成示例

项目中已包含一个完整示例：`AIMixedCollector`

使用方法：

```bash
# 1. 配置 .env
AI_MIXED_LIST_ID=你的List_ID

# 2. 测试
python -c "
import asyncio
from daily_ai_insight.collectors import AIMixedCollector

async def test():
    collector = AIMixedCollector()
    data = await collector.fetch()
    print(f'获取了 {len(data[\"items\"])} 条数据')

    # 统计各来源数量
    sources = {}
    for item in data['items']:
        source = item['source'].split('-')[0]
        sources[source] = sources.get(source, 0) + 1

    print('来源分布:', sources)

asyncio.run(test())
"
```

## 📚 相关文档

- [FollowCollector API 文档](src/daily_ai_insight/collectors/base.py)
- [Follow.is API 文档](https://api.follow.is)
- [收集器测试脚本](test_real_data.py)

## ❓ FAQ

**Q: 需要为每个新的混合 List 创建新的收集器类吗？**

A: 不需要！你可以：
- 复用现有收集器，只需更改环境变量名
- 或创建一个通用的 `MixedCollector`，通过参数传入 List ID

**Q: List 里的 Feed 数量有限制吗？**

A: Follow.is API 会分页返回，`FollowCollector` 默认获取 3 页数据（约 60 items）。可以通过修改 `fetch_pages` 参数获取更多。

**Q: 如何过滤特定来源的内容？**

A: 在收集器的 `fetch()` 或 `transform()` 方法中添加过滤逻辑，或在使用时过滤：

```python
data = await collector.fetch()
twitter_only = [
    item for item in data["items"]
    if item["source"].startswith("twitter-")
]
```
