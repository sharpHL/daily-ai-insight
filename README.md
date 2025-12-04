# Daily AI Insight

Automated AI intelligence pipeline that collects, analyzes, and delivers daily tech briefings.

## Features

- **Multi-source collection** - Follow.is RSS, GitHub Trending, and more
- **AI analysis** - Deep insights using Gemini/OpenAI
- **Auto delivery** - Push to Feishu, Telegram
- **Hybrid storage** - Git + JSON with auto-archiving

## Quick Start

```bash
# Install dependencies (using uv)
uv venv && uv pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python main.py                    # Full pipeline
python main.py --skip-collection  # Use cached data
python main.py --cleanup           # Clean old files
```

## Configuration

Required environment variables in `.env`:

```env
# Follow.is
FOLO_COOKIE="your_cookie"          # From browser DevTools
PAPERS_LIST_ID="your_list_id"      # Your Follow.is list IDs
TWITTER_LIST_ID="your_list_id"

# LLM
GEMINI_API_KEY="your_key"          # Google AI Studio

# Delivery (optional)
FEISHU_WEBHOOK="https://..."       # Feishu webhook
TELEGRAM_BOT_TOKEN="bot_token"     # Telegram bot
```

## Project Structure

```
src/daily_ai_insight/
├── collectors/     # Data collectors (unified architecture)
├── processors/     # Cleaning & deduplication
├── storage/        # Hybrid storage system
├── llm/            # AI analysis
└── renderers/      # Output formatting
```

## Collectors

All Follow.is collectors use unified `FollowCollector` base class:

- **Papers** - Academic papers from ArXiv
- **Twitter** - Tech Twitter posts
- **AIBase** - AI news (aibase.com)
- **机器之心** - Chinese AI news
- **量子位** - Chinese tech news
- **新智元** - Chinese AI insights
- **GitHub Trending** - Daily trending repos

## Documentation

- **[Migration Guide](docs/guides/MIGRATION_GUIDE.md)** - Migrating from old subclass pattern
- **[Environment Variables](ENV_VARS.md)** - Complete configuration reference
- **[Change Log](CHANGELOG.md)** - Version history
- **[Refactoring Docs](docs/refactoring/)** - Technical details and architecture

## Development

```bash
# Test collectors
python scripts/test_collectors_complete.py  # Validate all collectors

# Run tests
pytest tests/unit/ -v
```

## License

MIT