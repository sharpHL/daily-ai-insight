# 迁移指南：从子类到 Factory/Callback

## 📚 概述

本指南帮助你从旧的子类方式迁移到新的 Factory/Callback 模式。

### 为什么迁移？

- ✅ 代码更简洁（50 行 → 1 行）
- ✅ 更灵活（动态组合）
- ✅ 更易测试（纯函数）
- ✅ 零维护成本（不需要单独文件）

## 🚨 已删除的类

以下类已被删除，请使用新的替代方案：

### `AIMixedCollector` ❌ 已删除

**旧代码：**
```python
from daily_ai_insight.collectors import AIMixedCollector

collector = AIMixedCollector()
data = await collector.fetch()
```

**新代码（方式 1 - Factory）：**
```python
from daily_ai_insight.collectors import create_mixed_collector

collector = create_mixed_collector()
data = await collector.fetch()
```

**新代码（方式 2 - Callback）：**
```python
from daily_ai_insight.collectors import FollowCollector
from daily_ai_insight.collectors.transformers import auto_detect_transform

collector = FollowCollector(
    name="mixed",
    list_id_env="AI_MIXED_LIST_ID",
    transform_callback=auto_detect_transform
)
data = await collector.fetch()
```

### `AIMixedEnhancedCollector` ❌ 已删除

**旧代码：**
```python
from daily_ai_insight.collectors import AIMixedEnhancedCollector

collector = AIMixedEnhancedCollector()
```

**新代码（完全相同功能）：**
```python
from daily_ai_insight.collectors import create_mixed_collector

# auto_detect_transform 已包含所有增强功能
collector = create_mixed_collector()
```

## ✅ 推荐的迁移方式

### 现有子类（仍可用）

以下子类仍然可用，但推荐迁移到新方式：

#### TwitterCollector

**旧方式（仍可用）：**
```python
from daily_ai_insight.collectors import TwitterCollector

collector = TwitterCollector()
```

**新方式 1 - Factory（推荐）：**
```python
from daily_ai_insight.collectors import create_twitter_collector

collector = create_twitter_collector()
```

**新方式 2 - Callback（最灵活）：**
```python
from daily_ai_insight.collectors import FollowCollector
from daily_ai_insight.collectors.transformers import twitter_transform

collector = FollowCollector(
    name="twitter",
    list_id_env="TWITTER_LIST_ID",
    transform_callback=twitter_transform
)
```

#### RedditCollector

**旧方式：**
```python
from daily_ai_insight.collectors import RedditCollector

collector = RedditCollector()
```

**新方式 - Factory：**
```python
from daily_ai_insight.collectors import create_reddit_collector

collector = create_reddit_collector()
```

#### PapersCollector

**旧方式：**
```python
from daily_ai_insight.collectors import PapersCollector

collector = PapersCollector()
```

**新方式 - Factory：**
```python
from daily_ai_insight.collectors import create_papers_collector

collector = create_papers_collector()
```

#### 其他 FollowCollector 子类

所有其他子类（AIBaseCollector, JiqizhixinCollector, 等）都可以用通用工厂函数：

**旧方式：**
```python
from daily_ai_insight.collectors import AIBaseCollector

collector = AIBaseCollector()
```

**新方式：**
```python
from daily_ai_insight.collectors import create_collector

collector = create_collector(
    name="aibase",
    feed_id_env="AIBASE_FEED_ID",
    source_name="AI Base",
    home_url="https://www.aibase.com",
    item_type="news"
)
```

## 🎨 新功能：Preset 配置

使用 preset 快速创建常用收集器：

```python
from daily_ai_insight.collectors import create_from_preset

# 使用 preset
twitter = create_from_preset("twitter")
reddit = create_from_preset("reddit")
mixed = create_from_preset("mixed")

# 覆盖 preset 配置
custom_twitter = create_from_preset(
    "twitter",
    list_id_env="MY_CUSTOM_LIST"
)
```

可用的 preset：
- `twitter` - Twitter 收集器
- `reddit` - Reddit 收集器
- `papers` - 学术论文收集器
- `mixed` - 混合来源收集器

## 💡 最佳实践

### 1. 优先使用 Factory 函数

```python
# ✅ 好 - 简洁清晰
from daily_ai_insight.collectors import create_twitter_collector
collector = create_twitter_collector()

# ❌ 避免 - 更啰嗦
from daily_ai_insight.collectors import TwitterCollector
collector = TwitterCollector()
```

### 2. 需要自定义时使用 Callback

```python
# 自定义 transform 逻辑
def my_custom_transform(entries, feeds, **kwargs):
    # 自定义处理
    ...

from daily_ai_insight.collectors import create_collector
collector = create_collector(
    name="custom",
    list_id_env="MY_LIST",
    transform_callback=my_custom_transform
)
```

### 3. 混合来源必须使用新方式

```python
# ✅ 正确 - 自动检测所有平台
from daily_ai_insight.collectors import create_mixed_collector
collector = create_mixed_collector()

# ❌ 错误 - AIMixedCollector 已删除
# from daily_ai_insight.collectors import AIMixedCollector
```

## 🔄 迁移检查清单

- [ ] 搜索代码中的 `AIMixedCollector` 并替换为 `create_mixed_collector()`
- [ ] 搜索代码中的 `AIMixedEnhancedCollector` 并替换为 `create_mixed_collector()`
- [ ] （可选）将其他子类迁移到 Factory 函数
- [ ] 更新测试代码
- [ ] 更新文档和示例

## ❓ FAQ

**Q: 旧的子类还能用吗？**

A: 除了 `AIMixedCollector` 和 `AIMixedEnhancedCollector`（已删除），其他子类仍然可用。但推荐迁移到新方式。

**Q: 新方式有什么优势？**

A:
- 代码更简洁
- 更灵活（可动态配置）
- 更易测试（纯函数）
- 零文件维护成本

**Q: 迁移会破坏现有代码吗？**

A: 只有使用 `AIMixedCollector` 或 `AIMixedEnhancedCollector` 的代码需要修改。其他代码完全向后兼容。

**Q: 如何选择 Factory 还是 Callback？**

A:
- 简单场景 → Factory 函数
- 需要自定义 → Callback
- 混合来源 → Factory (`create_mixed_collector`)

**Q: 旧子类什么时候删除？**

A: 计划在未来大版本（3.0）中删除。会提前充分通知。

## 📚 相关文档

- [CALLBACK_PATTERN.md](CALLBACK_PATTERN.md) - Callback 模式详解
- [factory.py](src/daily_ai_insight/collectors/factory.py) - Factory 函数源码
- [transformers.py](src/daily_ai_insight/collectors/transformers.py) - Transform 函数库

## 🎉 总结

迁移步骤：
1. 替换 `AIMixedCollector` → `create_mixed_collector()`
2. 替换 `AIMixedEnhancedCollector` → `create_mixed_collector()`
3. （可选）其他子类迁移到 Factory 函数

记住：新方式更简洁、更灵活、更易维护！🚀
