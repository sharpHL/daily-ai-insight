# Environment Variables

Copy `.env.example` and configure your API keys:

## Follow.is Data Sources

```env
# Authentication (Required)
FOLO_COOKIE=your_cookie           # From browser DevTools (F12 → Network)
FOLO_DATA_API=https://api.follow.is/entries
FOLO_FILTER_DAYS=3                # Days to filter

# List IDs (get from Follow.is URLs)
PAPERS_LIST_ID=your_list_id       # Academic papers
TWITTER_LIST_ID=your_list_id      # Twitter posts
REDDIT_LIST_ID=your_list_id       # Reddit posts
NEWS_AGGREGATOR_LIST_ID=your_id   # News aggregator

# Feed IDs
AIBASE_FEED_ID=your_feed_id       # AI Base news
JIQIZHIXIN_FEED_ID=your_feed_id   # 机器之心
QBIT_FEED_ID=your_feed_id         # 量子位
XINZHIYUAN_FEED_ID=your_feed_id   # 新智元
XIAOHU_FEED_ID=your_feed_id       # Xiaohu AI
```

## Other Data Sources

```env
# GitHub Trending
GITHUB_TRENDING_API=https://gh-trending-api.com/repositories
GITHUB_TRENDING_LANGUAGE=python   # Optional filter
```

## LLM Providers

```env
# Gemini (default)
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-pro

# OpenAI (optional)
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4

LLM_PROVIDER=gemini               # gemini or openai
```

## Output Channels

```env
# Feishu
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=your_chat_id
```

## Quick Setup Guide

### Get Follow.is Cookie
1. Login to [app.follow.is](https://app.follow.is)
2. Open DevTools (F12) → Network tab
3. Refresh page, find any `api.follow.is` request
4. Copy the `Cookie` header value

### Get List/Feed IDs
1. Navigate to your list/feed on Follow.is
2. Check URL: `app.follow.is/list/[ID]` or `app.follow.is/feed/[ID]`
3. Copy the ID from URL