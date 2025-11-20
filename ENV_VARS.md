# Environment Variables - Complete Reference

## FOLO Configuration (Required for most collectors)

```env
# FOLO Cookie (get from browser DevTools)
FOLO_COOKIE=your_cookie_here

# FOLO API URL (usually don't need to change)
FOLO_DATA_API=https://api.follow.is/wallets/transactions

# Days to filter (default: 3)
FOLO_FILTER_DAYS=3
```

## Data Source IDs

### FOLO List IDs (listId-based sources)

```env
# Reddit
REDDIT_LIST_ID=your_list_id

# Twitter/X
TWITTER_LIST_ID=your_list_id

# Generic Papers (ArXiv, etc.)
PAPERS_LIST_ID=your_list_id

# Xiaohu AI
XIAOHU_LIST_ID=your_list_id

# HuggingFace Papers
HGPAPERS_LIST_ID=your_list_id
```

### FOLO Feed IDs (feedId-based sources)

```env
# AI Base
AIBASE_FEED_ID=your_feed_id

# Jiqizhixin (机器之心)
JIQIZHIXIN_FEED_ID=your_feed_id

# QBit (量子位)
QBIT_FEED_ID=your_feed_id

# XinZhiYuan (新智元)
XINZHIYUAN_FEED_ID=your_feed_id
```

### Fetch Pages Configuration

```env
# Number of pages to fetch for each source (default: 3)
REDDIT_FETCH_PAGES=3
TWITTER_FETCH_PAGES=3
PAPERS_FETCH_PAGES=3
XIAOHU_FETCH_PAGES=3
HGPAPERS_FETCH_PAGES=3
AIBASE_FETCH_PAGES=3
JIQIZHIXIN_FETCH_PAGES=3
QBIT_FETCH_PAGES=3
XINZHIYUAN_FETCH_PAGES=3
```

## Direct API Sources

### GitHub Trending

```env
# GitHub Trending API (default: https://gh-trending-api.com/repositories)
GITHUB_TRENDING_API=https://gh-trending-api.com/repositories

# Optional: filter by language
GITHUB_TRENDING_LANGUAGE=python

# Enable translation of descriptions to Chinese
TRANSLATE_ENABLED=false
```

### News Aggregator

```env
# Comma-separated list of RSS feed URLs
NEWS_AGGREGATOR_FEEDS=https://example.com/feed1.xml,https://example.com/feed2.xml
```

## LLM Providers

### Gemini (Google)

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-pro
```

### OpenAI

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4
```

### Provider Selection

```env
# Which LLM provider to use: 'gemini' or 'openai'
LLM_PROVIDER=gemini
```

## Output Channels

### Feishu (Lark)

```env
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/...
```

### Telegram

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=your_chat_id
```

## Optional Features

### GitHub Integration (for archiving reports)

```env
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=username/repo-name
GITHUB_BRANCH=main
```

---

## Quick Setup

### 1. Minimal Configuration (Core Features)

```env
# FOLO
FOLO_COOKIE=your_cookie

# At least one LLM provider
GEMINI_API_KEY=your_key

# At least one output channel
FEISHU_WEBHOOK=your_webhook
```

### 2. Full Configuration (All Features)

See sections above for complete list of all available variables.

---

## How to Get FOLO Cookie

1. Login to [app.follow.is](https://app.follow.is)
2. Open browser DevTools (F12)
3. Go to Network tab
4. Refresh the page
5. Find any request to `api.follow.is`
6. Copy the entire `Cookie` header value

## How to Get FOLO List/Feed IDs

1. Go to [app.follow.is](https://app.follow.is)
2. Navigate to your List or Feed
3. Check the URL: `https://app.follow.is/list/[LIST_ID]` or `https://app.follow.is/feed/[FEED_ID]`
4. Copy the ID from the URL

---

## Collector Mapping

| Collector | Environment Variable | Type |
|-----------|---------------------|------|
| GitHubTrendingCollector | GITHUB_TRENDING_API | Direct API |
| PapersCollector | PAPERS_LIST_ID | FOLO List |
| TwitterCollector | TWITTER_LIST_ID | FOLO List |
| RedditCollector | REDDIT_LIST_ID | FOLO List |
| XiaohuCollector | XIAOHU_LIST_ID | FOLO List |
| HuggingFacePapersCollector | HGPAPERS_LIST_ID | FOLO List |
| AIBaseCollector | AIBASE_FEED_ID | FOLO Feed |
| JiqizhixinCollector | JIQIZHIXIN_FEED_ID | FOLO Feed |
| QBitCollector | QBIT_FEED_ID | FOLO Feed |
| XinZhiYuanCollector | XINZHIYUAN_FEED_ID | FOLO Feed |
| NewsAggregatorCollector | NEWS_AGGREGATOR_FEEDS | Direct RSS |

