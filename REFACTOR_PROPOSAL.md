# Collectors 重构方案

## 当前问题

1. **环境变量冗余**：每个 collector 4+ 个环境变量
2. **样板代码**：3 个 collector 类只有 ~25 行，几乎完全相同
3. **HTML 重复**：模板代码在基类和子类中重复

## 方案对比

### 方案 A：快速优化（推荐先做）

**改动范围：** 最小
**时间：** 20-30 分钟
**风险：** 低

#### 具体改动

1. **简化环境变量**
   ```python
   # 移除：HGPAPERS_FETCH_PAGES, REDDIT_FETCH_PAGES, ...
   # 统一使用：FOLO_FETCH_PAGES, FOLO_FILTER_DAYS

   # FollowBaseCollector.__init__()
   def __init__(self, name: str, feed_id_env: str | None = None,
                list_id_env: str | None = None):
       self.fetch_pages = int(os.getenv("FOLO_FETCH_PAGES", "3"))
       self.filter_days = int(os.getenv("FOLO_FILTER_DAYS", "3"))
   ```

2. **统一 HTML 模板**
   ```python
   # FollowBaseCollector 添加配置
   def __init__(self, ..., read_more_text: str = "阅读更多"):
       self.read_more_text = read_more_text

   # HuggingFacePapersCollector
   def __init__(self):
       super().__init__(
           name="HuggingFace Papers",
           feed_id_env="HGPAPERS_FEED_ID",
           read_more_text="在 ArXiv/来源 阅读"
       )
       # 移除 generate_html() 重写
   ```

3. **清理空字符串**
   ```python
   # 改：feed_id_env=""
   # 为：feed_id_env=None
   ```

**优点：**
- ✓ 减少 80% 环境变量
- ✓ 删除 ~30 行重复代码
- ✓ 保持现有架构不变

**缺点：**
- 仍然需要为每个 collector 写一个类

---

### 方案 B：配置驱动重构

**改动范围：** 中等
**时间：** 1-2 小时
**风险：** 中等（需要更新测试）

#### 设计思路

用配置文件定义 collectors，动态创建实例。

#### 1. 配置文件

```yaml
# configs/collectors.yaml
collectors:
  - name: "HuggingFace Papers"
    type: follow_feed
    config:
      feed_id_env: HGPAPERS_FEED_ID
      home_url: https://huggingface.co/papers
      read_more_text: "在 ArXiv/来源 阅读"

  - name: "Reddit"
    type: follow_list
    config:
      list_id_env: REDDIT_LIST_ID
      home_url: https://www.reddit.com

  - name: "Xiaohu.AI"
    type: follow_feed
    config:
      feed_id_env: XIAOHU_FEED_ID
      home_url: https://www.xiaohu.ai

  - name: "News Aggregator"
    type: follow_list
    config:
      list_id_env: NEWS_AGGREGATOR_LIST_ID
      home_url: https://example.com/news

# 全局配置
defaults:
  fetch_pages: 3
  filter_days: 3
```

#### 2. 工厂模式

```python
# collectors/factory.py
from typing import List
import yaml
from .follow_base import FollowBaseCollector

class CollectorConfig:
    """Collector configuration."""
    def __init__(self, name: str, config: dict):
        self.name = name
        self.feed_id_env = config.get("feed_id_env")
        self.list_id_env = config.get("list_id_env")
        self.home_url = config.get("home_url", "https://follow.is")
        self.read_more_text = config.get("read_more_text", "阅读更多")

class CollectorFactory:
    """Factory for creating collectors from configuration."""

    @staticmethod
    def load_config(config_path: str = "configs/collectors.yaml") -> dict:
        """Load collector configuration from YAML."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    @staticmethod
    def create_collector(config: CollectorConfig) -> FollowBaseCollector:
        """Create a collector from configuration."""
        return FollowBaseCollector(
            name=config.name,
            feed_id_env=config.feed_id_env,
            list_id_env=config.list_id_env,
            home_url=config.home_url,
            read_more_text=config.read_more_text
        )

    @classmethod
    def create_all(cls, config_path: str = "configs/collectors.yaml") -> List[FollowBaseCollector]:
        """Create all collectors from configuration."""
        data = cls.load_config(config_path)
        collectors = []

        for item in data["collectors"]:
            config = CollectorConfig(item["name"], item["config"])
            collector = cls.create_collector(config)
            collectors.append(collector)

        return collectors

# 使用
collectors = CollectorFactory.create_all()
```

#### 3. 更新 FollowBaseCollector

```python
class FollowBaseCollector(BaseCollector):
    def __init__(
        self,
        name: str,
        feed_id_env: str | None = None,
        list_id_env: str | None = None,
        home_url: str = "https://follow.is",
        read_more_text: str = "阅读更多"
    ):
        super().__init__(name)
        self.feed_id = os.getenv(feed_id_env) if feed_id_env else None
        self.list_id = os.getenv(list_id_env) if list_id_env else None
        self.home_url = home_url
        self.read_more_text = read_more_text

        # 全局配置
        self.fetch_pages = int(os.getenv("FOLO_FETCH_PAGES", "3"))
        self.filter_days = int(os.getenv("FOLO_FILTER_DAYS", "3"))
        self.cookie = os.getenv("FOLO_COOKIE", "")
        self.api_url = os.getenv("FOLO_DATA_API", "https://api.follow.is/entries")

    def _get_home_url(self) -> str:
        return self.home_url

    def generate_html(self, item: dict) -> str:
        return f"""
            <strong>{escape_html(item['title'])}</strong><br>
            <small>来源: {escape_html(item.get('source', '未知'))} |
                   发布日期: {format_date_to_chinese(item.get('published_date', ''))}</small>
            <div class="content-html">
                {item.get('details', {}).get('content_html', '无内容。')}
            </div>
            <a href="{escape_html(item['url'])}" target="_blank"
               rel="noopener noreferrer">{self.read_more_text}</a>
        """
```

#### 4. 删除冗余类

可以删除：
- `huggingface_papers.py`
- `reddit.py`
- `xiaohu.py`
- `news_aggregator.py`

总共删除 ~100 行代码。

#### 5. 更新 __init__.py

```python
# collectors/__init__.py
from .base import BaseCollector
from .follow_base import FollowBaseCollector
from .factory import CollectorFactory

# 向后兼容
def HuggingFacePapersCollector():
    return CollectorFactory.create_collector(
        CollectorConfig("HuggingFace Papers", {"feed_id_env": "HGPAPERS_FEED_ID", ...})
    )

__all__ = [
    "BaseCollector",
    "FollowBaseCollector",
    "CollectorFactory",
]
```

**优点：**
- ✓ 删除 ~100 行样板代码
- ✓ 新增 collector 只需修改 YAML（无需写代码）
- ✓ 配置集中管理，易于维护
- ✓ 更容易做 A/B 测试

**缺点：**
- ✗ 需要更新所有测试
- ✗ 需要添加 YAML 配置
- ✗ 向后兼容需要额外工作

---

### 方案 C：模板引擎（可选）

如果 HTML 变得更复杂，考虑 Jinja2：

```python
# templates/collector_item.html
<strong>{{ item.title | escape }}</strong><br>
<small>来源: {{ item.source | escape }} | 发布日期: {{ item.published_date | format_date }}</small>
<div class="content-html">
    {{ item.details.content_html | safe }}
</div>
<a href="{{ item.url | escape }}" target="_blank">{{ read_more_text }}</a>
```

**优点：**
- ✓ 设计师可以直接修改 HTML
- ✓ 支持条件渲染、循环等复杂逻辑

**缺点：**
- ✗ 增加依赖（Jinja2）
- ✗ 对于当前简单模板可能过度设计

---

## 推荐方案

**阶段 1：立即执行（方案 A）**
- 低风险，快速见效
- 减少环境变量和重复代码
- 20-30 分钟完成

**阶段 2：考虑执行（方案 B）**
- 如果计划添加 5+ 个 collectors
- 或需要频繁调整配置
- 1-2 小时完成

**不建议：方案 C**
- 当前 HTML 足够简单
- 除非需要复杂的条件渲染

---

## 对比表

| 指标 | 当前 | 方案 A | 方案 B |
|------|------|--------|--------|
| 环境变量数 | ~12 | ~6 | ~6 |
| Collector 类数 | 5 | 5 | 1 |
| 代码行数 | ~350 | ~320 | ~280 |
| 新增 collector | 写类 | 写类 | 改 YAML |
| 测试修改 | - | 最小 | 中等 |
| 时间成本 | - | 20min | 1-2h |

---

## 实施建议

1. **先做方案 A**
   - 今天就可以完成
   - 立即减少冗余

2. **评估方案 B**
   - 如果未来要加很多 collectors → 做
   - 如果只有这 4 个 → 不做

3. **记录决策**
   - 无论选哪个，更新 PLAN.md
   - 说明为什么这样设计
