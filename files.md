# Project File Map

> Project file structure tree. Can be rewritten (NOT append-only). See CLAUDE.md for policy.

---

CLAUDE.md                    – Claude instructions and project context
progress.md                  – Project history (append-only)
files.md                     – This file (file structure tree)
README.md                    – Project overview and quick start
ENV_VARS.md                  – Environment variables reference
CHANGELOG.md                 – Version history
pyproject.toml               – Project config, deps, tool settings
Makefile                     – Common dev commands

/src/daily_ai_insight        – Main package
  __init__.py                – Package init
  __main__.py                – Module entry point
  cli.py                     – CLI entry, DailyInsightPipeline class

  /collectors                – Data source collectors
    __init__.py              – Exports factory functions
    base.py                  – BaseCollector, FollowCollector classes
    factory.py               – Factory functions, PRESET_CONFIGS
    transformers.py          – Platform transforms (twitter, reddit, etc)
    github_trending.py       – GitHub Trending collector
    utils.py                 – Shared utilities (headers, date filter)

  /processors                – Data cleaning and dedup
    __init__.py              – Exports DataCleaner, Deduplicator
    cleaner.py               – DataCleaner class
    deduper.py               – Deduplicator class

  /storage                   – Persistence layer
    __init__.py              – Exports create_storage
    manager.py               – StorageManager class
    backend.py               – Storage backend base
    /backends                – Backend implementations
      file.py                – File-based storage
      kv.py                  – Key-value storage

  /llm                       – LLM analysis
    __init__.py              – Exports ContentAnalyzer
    analyzer.py              – ContentAnalyzer class
    /providers               – LLM provider implementations
      gemini.py              – Google Gemini provider
      openai.py              – OpenAI provider
    /prompts                 – Prompt templates
      templates.py           – Analysis/report prompts

  /renderers                 – Output formatters
    __init__.py              – Exports renderers
    markdown.py              – Markdown output
    feishu.py                – Feishu webhook sender
    telegram.py              – Telegram bot sender

/tests                       – Test suite
  conftest.py                – Shared fixtures
  /unit                      – Unit tests (mocked)
    test_collectors.py       – Collector tests
    test_storage.py          – Storage tests
  /integration               – Integration tests (real APIs)
    test_collectors_real.py  – Real API collector tests

/scripts                     – Utility scripts
  test_collectors_complete.py – Validate all collectors

/storage                     – Runtime data directory
  /data                      – Raw collected data (JSON)
  /processed                 – Analyzed data
  /archives                  – Generated reports

/configs                     – Configuration files
/docs                        – Documentation
  /guides                    – User guides
  /refactoring               – Architecture docs
