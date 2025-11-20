# Collectors 重构总结

## 📋 重构概述

根据 CloudFlare-AI-Insight-Daily 项目的 JS 实现,完全重构了 Python 版本的数据收集器 (collectors) 模块。

## 🎯 主要改进

### 1. **统一的三方法架构**
参考 JS 实现,所有 collector 现在实现三个核心方法:
- `fetch()` - 从数据源获取原始数据
- `transform()` - 将原始数据转换为统一格式
- `generate_html()` - 生成 HTML 展示内容

### 2. **正确的 Follow.is API 集成**
- ❌ 旧实现:使用错误的 API 端点 (`api.folo.app`) 和 RSS 解析方式
- ✅ 新实现:使用正确的 API (`api.follow.is/entries`) 和 POST 请求

### 3. **新的 collectors 模块结构**
```
collectors/
├── base.py                  # 基础抽象类 (重写)
├── follow_base.py           # Follow.is API 基类 (新增)
├── utils.py                 # 辅助函数 (新增)
├── huggingface_papers.py    # HuggingFace Papers (新增)
├── reddit.py                # Reddit (新增)
├── xiaohu.py                # Xiaohu.AI (新增)
├── news_aggregator.py       # News Aggregator (新增)
└── folo.py                  # 旧实现 (保留但未使用)
```

## 🔧 技术实现细节

### Follow.is API 调用模式
```python
# 请求格式
POST https://api.follow.is/entries
Headers:
  - Cookie: {FOLO_COOKIE}
  - Content-Type: application/json
  - User-Agent: {随机 UA}
  - 其他浏览器模拟头...

Body:
{
  "feedId": "...",      # 或 "listId"
  "view": 1,
  "withContent": true,
  "publishedAfter": "..." # 分页游标
}

# 响应格式
{
  "data": [
    {
      "entries": {
        "id": "...",
        "url": "...",
        "title": "...",
        "content": "...",
        "publishedAt": "...",
        "author": "..."
      },
      "feeds": {
        "title": "..."
      }
    }
  ]
}
```

### 统一数据格式
```python
{
  "id": str,
  "type": str,
  "url": str,
  "title": str,
  "description": str,
  "published_date": str,
  "authors": str,
  "source": str,
  "details": {
    "content_html": str
  }
}
```

### 辅助函数 (utils.py)
- `get_random_user_agent()` - 随机 UA
- `sleep_random()` - 随机延迟避免限流
- `is_date_within_last_days()` - 日期过滤
- `strip_html()` - HTML 标签清理
- `escape_html()` - HTML 转义
- `format_date_to_chinese()` - 日期中文格式化
- `get_follow_headers()` - 统一请求头

## 🏗️ 架构设计

### FollowBaseCollector (基类)
所有 Follow.is 数据源继承此类,获得:
- ✅ 统一的 API 调用逻辑
- ✅ 自动分页支持
- ✅ 日期过滤
- ✅ 错误处理
- ✅ 随机延迟防限流

### 具体 Collector (子类)
只需实现:
- 构造函数中指定环境变量
- (可选) 覆盖 `_get_home_url()`
- (可选) 覆盖 `generate_html()` 自定义 HTML

## ✅ 测试覆盖

创建了全面的单元测试 `tests/unit/test_collectors.py`:

- **Utils 测试** (5个)
  - 随机 UA 生成
  - 日期过滤
  - HTML 处理
  - 转义函数

- **Collector 测试** (6个)
  - API fetch 测试
  - 数据转换测试
  - HTML 生成测试
  - 集成测试

**测试结果:** 11/11 通过 ✅

## 📦 环境变量配置

需要在 `.env` 中配置:

```bash
# Follow.is 基础配置
FOLO_COOKIE=your_cookie_here
FOLO_DATA_API=https://api.follow.is/entries
FOLO_FETCH_PAGES=3
FOLO_FILTER_DAYS=3

# 各数据源的 Feed/List ID
HGPAPERS_FEED_ID=xxx
REDDIT_LIST_ID=xxx
XIAOHU_FEED_ID=xxx
NEWS_AGGREGATOR_LIST_ID=xxx
```

## 🔄 CLI 集成

更新了 `cli.py` 以使用新的 collectors:

```python
# 初始化所有 collectors
collectors = [
    HuggingFacePapersCollector(),
    RedditCollector(),
    XiaohuCollector(),
    NewsAggregatorCollector()
]

# 循环收集数据
for collector in collectors:
    raw_data = await collector.fetch()
    items = collector.transform(raw_data, collector.name)
    all_items.extend(items)
```

## 📈 代码质量提升

- ✅ 完全类型注解
- ✅ 详细文档字符串
- ✅ 错误处理和日志
- ✅ 单元测试覆盖
- ✅ 遵循 Python 最佳实践
- ✅ 与 JS 实现对齐

## 🎓 关键学习点

1. **API 调用方式**:Follow.is 使用 POST + JSON,不是 GET + RSS
2. **分页机制**:使用 `publishedAfter` 游标而非页码
3. **请求头模拟**:需要完整的浏览器请求头才能成功
4. **数据结构**:嵌套的 `entries` 和 `feeds` 结构
5. **日期过滤**:在客户端而非服务端过滤

## 🚀 下一步

- [ ] 添加更多数据源 (GitHub Trending, Twitter 等)
- [ ] 实现缓存机制减少 API 调用
- [ ] 添加 rate limiting 保护
- [ ] 实现翻译功能 (如 JS 版本)
- [ ] 添加更多集成测试

## 📝 注意事项

1. 需要有效的 `FOLO_COOKIE` 才能调用 API
2. 请求频率不要过高,建议每次请求后随机延迟 0-5 秒
3. `publishedAfter` 游标来自上一页最后一条的 `publishedAt`
4. 所有日期格式使用 ISO 8601

---

重构完成时间: 2025-11-20
