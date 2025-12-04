# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily AI Insight is an automated AI intelligence pipeline that collects, analyzes, and delivers daily tech briefings. It fetches data from multiple sources (Follow.is RSS, GitHub Trending), analyzes content with LLMs (Gemini/OpenAI), and distributes reports to messaging platforms (Feishu, Telegram).

## Commands

```bash
# Install
uv venv && uv pip install -e ".[dev]"

# Run pipeline
python -m daily_ai_insight                    # Full pipeline
python -m daily_ai_insight --skip-collection  # Use cached data
python -m daily_ai_insight --skip-analysis    # Skip LLM analysis
python -m daily_ai_insight --cleanup          # Clean old files

# Testing
pytest tests/unit/ -v                         # Unit tests only
pytest tests/integration/ -v                  # Integration tests (need .env)
pytest tests/ -v --cov                        # All tests with coverage

# Code quality
ruff check src/ tests/                        # Lint
black src/ tests/                             # Format
mypy src/                                     # Type check
```

## Architecture

### Pipeline Flow
```
Collectors → Processors → Storage → LLM Analyzer → Renderers → Distribution
```

### Key Components

**Collectors** (`src/daily_ai_insight/collectors/`)
- `base.py`: `BaseCollector` (abstract) and `FollowCollector` (concrete for Follow.is API)
- `factory.py`: Factory functions (`create_twitter_collector()`, `create_from_preset()`) and `PRESET_CONFIGS` dict
- `transformers.py`: Platform-specific transforms (twitter, reddit, weibo, auto-detect)
- `github_trending.py`: Standalone GitHub Trending collector

**Creating a new collector**: Use factory pattern, not subclasses:
```python
from daily_ai_insight.collectors import create_from_preset, create_collector

# Use preset
collector = create_from_preset("twitter")

# Or custom
collector = create_collector(
    name="custom",
    list_id_env="CUSTOM_LIST_ID",
    transform_callback=my_transform
)
```

**LLM** (`src/daily_ai_insight/llm/`)
- `analyzer.py`: `ContentAnalyzer` with auto-fallback between Gemini/OpenAI
- `providers/`: Provider implementations (gemini.py, openai.py)
- `prompts/templates.py`: LLM prompt templates

**Storage** (`src/daily_ai_insight/storage/`)
- Hybrid system: JSON files organized by date in `storage/{data,processed,archives}/`
- `manager.py`: `StorageManager` for save/load operations

**Renderers** (`src/daily_ai_insight/renderers/`)
- `markdown.py`, `feishu.py`, `telegram.py`: Output format converters

### Data Flow
1. Collectors produce items in JSFeed format via `fetch()` → `transform()`
2. Processors clean and deduplicate
3. `ContentAnalyzer.analyze_content()` processes with LLM
4. Renderers format for each channel
5. Results saved to `storage/` and sent to configured channels

## Testing

- Unit tests: `tests/unit/` - Use mocks, no external dependencies
- Integration tests: `tests/integration/` - Require `.env` with real API keys
- pytest-asyncio configured with `asyncio_mode = "auto"`

## Configuration

All config via `.env` (see `ENV_VARS.md`):
- `FOLO_COOKIE`: Follow.is auth cookie (required for Follow.is sources)
- `*_LIST_ID` / `*_FEED_ID`: Follow.is list/feed identifiers
- `GEMINI_API_KEY` / `OPENAI_API_KEY`: LLM providers
- `FEISHU_WEBHOOK` / `TELEGRAM_*`: Output channels

---

## Project History Log Policy (`progress.md`)

You MUST maintain an append-only project log at `progress.md`. If the project does not yet have a `progress.md`, create one.

### Purpose
`progress.md` is the canonical history of what this AI+human team has done. It is used as long-term memory and for auditability.

### Hard Rules (NON-NEGOTIABLE)
1. Treat `progress.md` as **immutable history**:
   - You may ONLY **append new entries at the end of the file**.
   - Do NOT edit, rewrite, reorder, or delete any existing lines.
   - Do NOT "clean up", "refactor", or "compact" old entries.
2. If earlier information is wrong or outdated:
   - Do NOT modify the old entry.
   - Instead, add a new entry with a short "Correction" note.
3. If a user explicitly asks to "update" or "fix" `progress.md`:
   - Default behavior: append a new corrective entry.
   - Only restructure old content if the human user clearly says
     "it is OK to rewrite history in progress.md".

### When to Append
You MUST append a new entry when ANY of these happens:
- You complete a meaningful unit of work (feature, bugfix, refactor, analysis).
- You change important decisions, architecture, or constraints.
- You finish a long session of work in this repo.

If in doubt: append an entry.

### Entry Format (strict)
Each entry MUST follow this structure, appended at EOF:

#### `[YYYY-MM-DD HH:MM] <short summary>`
- **Context**: one sentence about what we were trying to do.
- **Changes**:
  - `file_or_area`: short description of what changed and why.
  - ...
- **Decisions**:
  - key decision or assumption (if any).
- **Next steps**:
  - concrete next actions for future sessions.
- **Actor**: `Claude Code` / `sharp` / both.

Constraints:
- Keep each entry ≤ 200 words.
- Prefer bullet points, avoid prose walls.
- Link to relevant files/PRs where helpful.

### Operational Habits
- At the start of a new major session:
  - Load `@CLAUDE.md` and (if needed) skim `@progress.md`.
- At the end of a major session:
  - Summarize and append a new log entry to `progress.md`
    following this policy.
- Never run transformations on `progress.md` that remove or rewrite history.

---

## File Structure Tree Policy (`files.md`)

### 1. Purpose
Maintain the **file structure tree (tree + one-line description)** as the single source of truth (SSOT) for project structure, used for navigation, collaboration, and refactoring.
`files.md` can be rewritten, reorganized, overwritten (NOT append-only).

### 2. Scope of Documentation
**Must document:**
- Key directories (entry points, core business logic, agents, config, scripts)
- Important files (entry points, core logic, key classes/components)

**Do NOT document:**
- `.git`, cache, build artifacts, third-party dependencies
- Temporary or auto-generated files

**Format:**
```
<path> – <one-line description (≤60 chars)>
```

### 3. Update Timing (once per session)
Claude MUST:
- **Before session ends, if significant files were added/deleted/modified, update `files.md`**

**Triggers for update before session ends:**
- Files or directories added/deleted/moved/renamed during session
- Module responsibilities changed
- Structure became complex or ambiguous

### 4. Rendering Format (strict)
Tree structure MUST use the following format:
```
/src                         – Main source code directory
  /services                  – External system integrations
    llm_client.py           – LLM wrapper (Claude/GPT etc.)
    storage.py              – Local/cloud storage I/O
  app.py                     – Application entry point
  config.py                  – Global config loader

/scripts                     – Ops/data processing scripts
  clean_temp.py             – Clean temporary files
```
Format requirements:
- Use **2-space indentation** to show hierarchy
- Each line: `path – one-line description`

### 5. Workflow Requirements
Claude MUST:
1. Read latest `files.md` before any refactor
