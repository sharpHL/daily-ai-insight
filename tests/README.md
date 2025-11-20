# Testing Guide

This project has two types of tests:

## 📦 Unit Tests (Mock)

Located in `tests/unit/`, these tests use mocks and don't require real API credentials.

**Run unit tests only:**
```bash
pytest tests/unit/ -v
```

**Features:**
- Fast execution (no network calls)
- No credentials required
- Test internal logic and transformations
- Use `pytest` fixtures with `monkeypatch`

## 🌐 Integration Tests (Real API)

Located in `tests/integration/`, these tests make real API calls to Follow.is and other services.

**Setup:**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual credentials in `.env`:
   ```bash
   # Required for all collectors
   FOLO_COOKIE=your_actual_cookie

   # Feed/List IDs
   HGPAPERS_FEED_ID=your_feed_id
   REDDIT_LIST_ID=your_list_id
   XIAOHU_FEED_ID=your_feed_id
   NEWS_AGGREGATOR_LIST_ID=your_list_id
   ```

3. Get your Follow.is cookie:
   - Log in to [Follow.is](https://follow.is)
   - Open DevTools (F12) → Application → Cookies
   - Copy the entire cookie value

**Run integration tests:**
```bash
# All integration tests
pytest tests/integration/ -v

# Specific collector
pytest tests/integration/test_collectors_real.py::TestHuggingFacePapersReal -v

# With detailed output
pytest tests/integration/ -v -s
```

**Features:**
- Real API calls to Follow.is
- Validates actual data structure
- Tests concurrent fetching
- Environment loaded via `python-dotenv`
- Auto-skip if credentials missing

## 🎯 Run All Tests

```bash
# Run everything (unit + integration)
pytest -v

# With coverage report
pytest --cov=src/daily_ai_insight --cov-report=html

# Only unit tests (no API calls)
pytest tests/unit/
```

## 📊 Coverage

```bash
# Generate coverage report
pytest --cov=src/daily_ai_insight --cov-report=html

# View report
open htmlcov/index.html
```

## 🚀 Quick Commands

```bash
# Fast: Unit tests only
make test-unit    # or: pytest tests/unit/

# Slow: Integration tests (requires .env)
make test-integration    # or: pytest tests/integration/

# Complete: All tests
make test    # or: pytest
```

## ⚠️ Important Notes

1. **Environment Variables:**
   - Unit tests: Use `monkeypatch` to mock env vars
   - Integration tests: Use `dotenv` to load from `.env`

2. **Test Isolation:**
   - Integration tests are auto-skipped if credentials missing
   - Each test class has its own collector instance
   - No test should modify global state

3. **Rate Limiting:**
   - Integration tests include delays between requests
   - Use `FOLO_FETCH_PAGES=1` in `.env` for faster tests

4. **Security:**
   - Never commit `.env` file (already in `.gitignore`)
   - Use `.env.example` as template only
   - Rotate credentials if accidentally exposed

## 📝 Example: Adding New Collector Test

**Unit test (mock):**
```python
# tests/unit/test_collectors.py
@pytest.mark.asyncio
async def test_new_collector(mock_env):
    collector = NewCollector()
    # Mock the API response
    with patch.object(collector, 'fetch', return_value=mock_data):
        result = await collector.fetch()
    assert result is not None
```

**Integration test (real):**
```python
# tests/integration/test_collectors_real.py
class TestNewCollectorReal:
    @pytest.fixture
    def collector(self, check_env_vars):
        check_env_vars("FOLO_COOKIE", "NEW_FEED_ID")
        return NewCollector()

    @pytest.mark.asyncio
    async def test_fetch_real(self, collector, is_real_test):
        raw_data = await collector.fetch()
        assert raw_data is not None
        assert "items" in raw_data
```
