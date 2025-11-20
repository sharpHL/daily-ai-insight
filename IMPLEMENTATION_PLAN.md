# Implementation Plan - Daily AI Insight

## Executive Summary

Complete the Python refactor of CloudFlare-AI-Insight-Daily with **missing 7 data sources** and **enhanced AI features** to achieve feature parity while maintaining simplicity.

**Current Progress**: 40% feature complete
**Target**: 85% feature complete (skip web UI components)
**Timeline**: 4 weeks

---

## Phase 1: Critical Data Sources (Week 1)

### 🎯 Goal
Add the 3 most valuable missing data sources

### Tasks

#### 1.1 GitHub Trending Collector ⭐ HIGH PRIORITY

**File**: `src/daily_ai_insight/collectors/github_trending.py`

```python
class GitHubTrendingCollector(BaseCollector):
    """Fetch trending GitHub repositories"""

    def __init__(self):
        self.api_url = os.getenv(
            'GITHUB_TRENDING_API',
            'https://gh-trending-api.com/repositories'
        )
        self.translate_enabled = os.getenv('TRANSLATE_ENABLED', 'true').lower() == 'true'

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetch from GitHub Trending API
        # Handle translation if enabled
        pass

    def transform(self, raw_data: List[dict]) -> List[dict]:
        # Transform to unified format
        pass
```

**Environment Variables**:
```env
GITHUB_TRENDING_API=https://gh-trending-api.com/repositories
GITHUB_TRENDING_LANGUAGE=python  # Optional filter
TRANSLATE_ENABLED=true
```

**Testing**:
```bash
# Test GitHub trending collector
python -m daily_ai_insight.collectors.github_trending
```

**Estimated Time**: 2 days

---

#### 1.2 Generic Papers Collector (FOLO)

**File**: `src/daily_ai_insight/collectors/papers.py`

Extends `FOLOBaseCollector` for generic ArXiv/research papers.

```python
from .follow_base import FOLOBaseCollector

class PapersCollector(FOLOBaseCollector):
    """Generic papers from ArXiv via FOLO"""

    def __init__(self):
        super().__init__(
            list_id=os.getenv('PAPERS_LIST_ID'),
            name='papers',
            source_name='ArXiv Papers'
        )
```

**Environment Variables**:
```env
PAPERS_LIST_ID=your_folo_list_id
PAPERS_FETCH_PAGES=3
```

**Testing**:
```bash
python -m daily_ai_insight.collectors.papers
```

**Estimated Time**: 1 day

---

#### 1.3 Twitter Collector (FOLO)

**File**: `src/daily_ai_insight/collectors/twitter.py`

Similar to existing Reddit collector but for Twitter/X feeds.

```python
from .follow_base import FOLOBaseCollector

class TwitterCollector(FOLOBaseCollector):
    """Twitter/X feeds via FOLO"""

    def __init__(self):
        super().__init__(
            list_id=os.getenv('TWITTER_LIST_ID'),
            name='twitter',
            source_name='Twitter/X'
        )

    def transform(self, raw_data: dict) -> List[dict]:
        # Handle Twitter-specific formatting
        # Extract author names properly
        pass
```

**Environment Variables**:
```env
TWITTER_LIST_ID=your_folo_list_id
TWITTER_FETCH_PAGES=3
```

**Estimated Time**: 1 day

---

#### 1.4 Update CLI and Integration

Update `cli.py` to include new collectors:

```python
from daily_ai_insight.collectors import (
    NewsAggregatorCollector,
    HuggingFacePapersCollector,
    RedditCollector,
    XiaohuCollector,
    GitHubTrendingCollector,  # New
    PapersCollector,           # New
    TwitterCollector,          # New
)

COLLECTORS = [
    NewsAggregatorCollector(),
    HuggingFacePapersCollector(),
    RedditCollector(),
    XiaohuCollector(),
    GitHubTrendingCollector(),
    PapersCollector(),
    TwitterCollector(),
]
```

**Estimated Time**: 0.5 days

---

### Week 1 Deliverables

- ✅ GitHub Trending collector
- ✅ Papers collector
- ✅ Twitter collector
- ✅ Updated CLI integration
- ✅ Environment variable documentation
- ✅ Basic tests for all collectors

**Total Time**: ~5 days

---

## Phase 2: Enhanced AI Pipeline (Week 2)

### 🎯 Goal
Implement multi-step AI analysis for better quality output

### Tasks

#### 2.1 Multi-Step Prompt System

**File**: `src/daily_ai_insight/llm/prompts/multi_step.py`

```python
class MultiStepPrompts:
    """Multi-step analysis prompts from original implementation"""

    @staticmethod
    def get_step_one_prompt() -> str:
        """Step 1: Chunk and summarize each item"""
        return """
You are an AI assistant helping to summarize AI/tech news items.

For each item below, provide:
1. One-sentence summary (Chinese)
2. Key technical details
3. Potential impact (1-2 sentences)

Output format: JSON array of summaries
        """

    @staticmethod
    def get_step_two_prompt() -> str:
        """Step 2: Format and structure summaries"""
        return """
Take the summarized items and organize them into a structured daily report.

Format:
## 今日要闻
[Top 3-5 items with details]

## 技术进展
[Technical updates]

## 项目推荐
[GitHub projects]

## 论文速递
[Academic papers]
        """

    @staticmethod
    def get_step_three_prompt() -> str:
        """Step 3: Generate executive summary"""
        return """
Generate a 100-word executive summary covering:
- Main trends observed today
- Most significant developments
- Key takeaways for readers
        """

    @staticmethod
    def get_podcast_prompt() -> str:
        """Generate podcast script"""
        return """
Convert the daily report into a conversational podcast script.

Format:
[开场白]
大家好，欢迎收听今天的AI日报播客...

[正文]
今天我们关注到几个重要进展...

[结尾]
以上就是今天的内容，感谢收听...
        """
```

**Estimated Time**: 1 day

---

#### 2.2 Multi-Step Analyzer

**File**: `src/daily_ai_insight/llm/multi_step_analyzer.py`

```python
from typing import List, Dict, Any
from .prompts.multi_step import MultiStepPrompts
from .providers.base import BaseLLMProvider

class MultiStepAnalyzer:
    """Multi-step content analysis pipeline"""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.prompts = MultiStepPrompts()

    async def analyze_full(
        self,
        items: List[Dict[str, Any]],
        enable_chunking: bool = True
    ) -> Dict[str, str]:
        """Full multi-step analysis"""

        # Step 1: Chunk and summarize (optional for large datasets)
        if enable_chunking and len(items) > 10:
            summaries = await self._chunk_summarize(items)
        else:
            summaries = self._format_items(items)

        # Step 2: Format into structured report
        formatted_report = await self._format_report(summaries)

        # Step 3: Generate executive summary
        executive_summary = await self._generate_summary(formatted_report)

        return {
            'full_report': formatted_report,
            'executive_summary': executive_summary,
            'raw_summaries': summaries
        }

    async def _chunk_summarize(
        self,
        items: List[dict],
        chunk_size: int = 3
    ) -> str:
        """Summarize items in chunks to handle large datasets"""
        chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]

        tasks = []
        for chunk in chunks:
            chunk_text = self._format_items(chunk)
            task = self.llm.generate(
                prompt=chunk_text,
                system_prompt=self.prompts.get_step_one_prompt()
            )
            tasks.append(task)

        summaries = await asyncio.gather(*tasks)
        return '\n\n'.join(summaries)

    async def _format_report(self, summaries: str) -> str:
        """Format summaries into structured report"""
        return await self.llm.generate(
            prompt=summaries,
            system_prompt=self.prompts.get_step_two_prompt()
        )

    async def _generate_summary(self, report: str) -> str:
        """Generate executive summary"""
        return await self.llm.generate(
            prompt=report,
            system_prompt=self.prompts.get_step_three_prompt()
        )

    async def generate_podcast(self, report: str) -> str:
        """Generate podcast script from report"""
        return await self.llm.generate(
            prompt=report,
            system_prompt=self.prompts.get_podcast_prompt()
        )

    def _format_items(self, items: List[dict]) -> str:
        """Format items for LLM input"""
        formatted = []
        for item in items:
            text = f"""
Title: {item['title']}
Source: {item['source']}
Date: {item['published_date']}
URL: {item['url']}
Content: {item['content'][:500]}...
            """
            formatted.append(text)
        return '\n\n------\n\n'.join(formatted)
```

**Estimated Time**: 2 days

---

#### 2.3 Update CLI for Multi-Step Analysis

Add options to CLI:

```python
@click.option('--analysis-mode', type=click.Choice(['simple', 'multi-step', 'podcast']),
              default='simple', help='Analysis mode')
async def run(skip_collection, skip_analysis, cleanup, analysis_mode):
    # ...

    if not skip_analysis:
        if analysis_mode == 'multi-step':
            analyzer = MultiStepAnalyzer(llm_provider)
            result = await analyzer.analyze_full(all_items)
            print(f"\n📝 Executive Summary:\n{result['executive_summary']}\n")
        elif analysis_mode == 'podcast':
            analyzer = MultiStepAnalyzer(llm_provider)
            result = await analyzer.analyze_full(all_items)
            podcast = await analyzer.generate_podcast(result['full_report'])
            print(f"\n🎙️ Podcast Script:\n{podcast}\n")
        else:
            # Simple analysis (current implementation)
            pass
```

**Estimated Time**: 1 day

---

#### 2.4 Update Renderers for Multi-Format Output

Update Markdown renderer to support different formats:

```python
class MarkdownRenderer:
    def render(self, data: dict, format_type: str = 'standard') -> str:
        if format_type == 'podcast':
            return self._render_podcast(data)
        elif format_type == 'multi-step':
            return self._render_multi_step(data)
        else:
            return self._render_standard(data)

    def _render_podcast(self, data: dict) -> str:
        """Render podcast script format"""
        pass

    def _render_multi_step(self, data: dict) -> str:
        """Render multi-step analysis format"""
        pass
```

**Estimated Time**: 1 day

---

### Week 2 Deliverables

- ✅ Multi-step prompt system
- ✅ Multi-step analyzer implementation
- ✅ Podcast script generation
- ✅ CLI support for different analysis modes
- ✅ Updated renderers for multi-format output
- ✅ Documentation and examples

**Total Time**: ~5 days

---

## Phase 3: GitHub Integration (Week 3)

### 🎯 Goal
Auto-archive daily reports to GitHub repository

### Tasks

#### 3.1 GitHub Archiver

**File**: `src/daily_ai_insight/storage/github_archiver.py`

```python
import os
from pathlib import Path
from typing import Optional
import httpx
from datetime import datetime

class GitHubArchiver:
    """Archive daily reports to GitHub repository"""

    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo = os.getenv('GITHUB_REPO')  # Format: owner/repo
        self.branch = os.getenv('GITHUB_BRANCH', 'main')
        self.base_url = 'https://api.github.com'

        if not self.token or not self.repo:
            raise ValueError('GITHUB_TOKEN and GITHUB_REPO must be set')

    async def commit_report(
        self,
        date: str,
        content: str,
        folder: str = 'daily',
        message: Optional[str] = None
    ) -> dict:
        """
        Commit markdown report to GitHub

        Args:
            date: Date string (YYYY-MM-DD)
            content: Markdown content
            folder: Target folder in repo
            message: Optional custom commit message

        Returns:
            GitHub API response
        """
        file_path = f"{folder}/{date}.md"
        commit_message = message or f"Daily AI Insight - {date}"

        # Get file SHA if exists (for update)
        file_sha = await self._get_file_sha(file_path)

        # Prepare request
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Encode content to base64
        import base64
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')

        payload = {
            'message': commit_message,
            'content': content_b64,
            'branch': self.branch
        }

        if file_sha:
            payload['sha'] = file_sha

        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _get_file_sha(self, file_path: str) -> Optional[str]:
        """Get file SHA if exists"""
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()['sha']
            except:
                pass
        return None

    async def read_report(self, date: str, folder: str = 'daily') -> Optional[str]:
        """Read historical report from GitHub"""
        file_path = f"{folder}/{date}.md"
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    import base64
                    content_b64 = response.json()['content']
                    content = base64.b64decode(content_b64).decode('utf-8')
                    return content
            except:
                pass
        return None

    async def list_reports(
        self,
        folder: str = 'daily',
        limit: int = 10
    ) -> List[dict]:
        """List recent reports in GitHub repo"""
        url = f"{self.base_url}/repos/{self.repo}/contents/{folder}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                files = response.json()
                # Filter .md files and sort by name (date)
                md_files = [
                    f for f in files
                    if f['name'].endswith('.md')
                ]
                md_files.sort(key=lambda x: x['name'], reverse=True)
                return md_files[:limit]
        return []
```

**Estimated Time**: 2 days

---

#### 3.2 Update CLI for GitHub Integration

```python
@click.option('--push-github', is_flag=True, help='Push report to GitHub')
@click.option('--github-folder', default='daily', help='GitHub folder for reports')
async def run(
    skip_collection,
    skip_analysis,
    cleanup,
    analysis_mode,
    push_github,
    github_folder
):
    # ... existing logic ...

    # After rendering markdown
    if push_github:
        try:
            archiver = GitHubArchiver()
            result = await archiver.commit_report(
                date=today,
                content=markdown_content,
                folder=github_folder
            )
            print(f"✅ Pushed to GitHub: {result['content']['html_url']}")
        except Exception as e:
            print(f"❌ Failed to push to GitHub: {e}")
```

**Estimated Time**: 1 day

---

#### 3.3 Update Documentation

Update `.env.example` and README:

```env
# GitHub Integration (Optional)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=username/repo-name
GITHUB_BRANCH=main
```

**Estimated Time**: 0.5 days

---

### Week 3 Deliverables

- ✅ GitHub archiver implementation
- ✅ CLI support for GitHub push
- ✅ Read historical reports from GitHub
- ✅ List recent reports
- ✅ Documentation and examples
- ✅ Error handling and retry logic

**Total Time**: ~4 days

---

## Phase 4: Remaining Sources & Polish (Week 4)

### 🎯 Goal
Add remaining FOLO sources and polish the codebase

### Tasks

#### 4.1 Remaining FOLO Collectors (Optional)

All follow the same pattern using `FOLOBaseCollector`:

**Files**:
- `src/daily_ai_insight/collectors/aibase.py`
- `src/daily_ai_insight/collectors/jiqizhixin.py`
- `src/daily_ai_insight/collectors/qbit.py`
- `src/daily_ai_insight/collectors/xinzhiyuan.py`

**Template**:
```python
from .follow_base import FOLOBaseCollector

class AiBaseCollector(FOLOBaseCollector):
    def __init__(self):
        super().__init__(
            feed_id=os.getenv('AIBASE_FEED_ID'),
            name='aibase',
            source_name='AI Base'
        )
```

**Environment Variables**:
```env
AIBASE_FEED_ID=
JIQIZHIXIN_FEED_ID=
QBIT_FEED_ID=
XINZHIYUAN_FEED_ID=
```

**Estimated Time**: 2 days (0.5 day each)

---

#### 4.2 Testing & Bug Fixes

- Write comprehensive tests for all collectors
- Test multi-step analyzer
- Test GitHub integration
- Fix any discovered bugs
- Performance optimization

**Estimated Time**: 2 days

---

#### 4.3 Documentation Updates

- Update README with all features
- Add usage examples for new modes
- Document all environment variables
- Create troubleshooting guide
- Add architecture diagrams

**Estimated Time**: 1 day

---

### Week 4 Deliverables

- ✅ All 11 data sources implemented
- ✅ Comprehensive test coverage
- ✅ Complete documentation
- ✅ Bug fixes and optimizations
- ✅ Ready for production use

**Total Time**: ~5 days

---

## Environment Variables - Complete Reference

### Data Sources
```env
# FOLO Configuration
FOLO_COOKIE=your_cookie
FOLO_DATA_API=https://api.follow.is/wallets/transactions
FOLO_FILTER_DAYS=3

# FOLO List/Feed IDs
XIAOHU_LIST_ID=
REDDIT_LIST_ID=
TWITTER_LIST_ID=
PAPERS_LIST_ID=
AIBASE_FEED_ID=
JIQIZHIXIN_FEED_ID=
QBIT_FEED_ID=
XINZHIYUAN_FEED_ID=
HGPAPERS_LIST_ID=

# Direct APIs
GITHUB_TRENDING_API=https://gh-trending-api.com/repositories
NEWS_AGGREGATOR_FEEDS=feed1.xml,feed2.xml
```

### LLM Configuration
```env
# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-pro

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4

# Feature Flags
TRANSLATE_ENABLED=true
LLM_PROVIDER=gemini
```

### Output Channels
```env
# Feishu
FEISHU_WEBHOOK=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# GitHub
GITHUB_TOKEN=
GITHUB_REPO=username/daily-ai-insight-reports
GITHUB_BRANCH=main
```

---

## Testing Strategy

### Unit Tests
```bash
# Test individual collectors
pytest tests/collectors/test_github_trending.py
pytest tests/collectors/test_papers.py
pytest tests/collectors/test_twitter.py

# Test multi-step analyzer
pytest tests/llm/test_multi_step_analyzer.py

# Test GitHub integration
pytest tests/storage/test_github_archiver.py
```

### Integration Tests
```bash
# Full pipeline test
python -m daily_ai_insight --analysis-mode multi-step --push-github
```

### Manual Testing Checklist

- [ ] Each collector fetches data successfully
- [ ] Data cleaning and deduplication works
- [ ] Simple analysis generates output
- [ ] Multi-step analysis produces quality results
- [ ] Podcast script is conversational
- [ ] Markdown rendering is correct
- [ ] Feishu push works
- [ ] Telegram push works
- [ ] GitHub archiver commits successfully
- [ ] Historical reports can be read from GitHub
- [ ] All environment variables are documented
- [ ] Error messages are clear
- [ ] Performance is acceptable

---

## Success Metrics

### Feature Completeness
- ✅ All 11 data sources: 100%
- ✅ Multi-step AI pipeline: 100%
- ✅ GitHub integration: 100%
- ✅ Multi-format output: 100%
- ❌ Web UI: 0% (not needed)
- ❌ RSS feeds: 0% (not needed)

**Target**: 85% (skip web UI and RSS)

### Quality Metrics
- Code coverage: >80%
- Type hint coverage: 100%
- Documentation: Complete
- Error handling: Comprehensive
- Performance: <5 min for full pipeline

---

## Risk Mitigation

### High Risk Items

1. **FOLO API Rate Limiting**
   - Mitigation: Random delays, exponential backoff
   - Fallback: Reduce fetch pages

2. **LLM API Costs**
   - Mitigation: Use cheaper models for initial steps
   - Monitoring: Track token usage

3. **GitHub API Rate Limits**
   - Mitigation: Use authenticated requests (higher limits)
   - Fallback: Local storage only

4. **Data Source Changes**
   - Mitigation: Graceful error handling
   - Logging: Detailed error messages

---

## Post-Implementation

### Monitoring
- Set up error alerting (email/Telegram)
- Track daily run success rate
- Monitor LLM costs
- Track data source availability

### Maintenance
- Weekly: Check for API changes
- Monthly: Review and update prompts
- Quarterly: Add new data sources as needed

### Future Enhancements (Beyond Scope)
- Vector database for semantic search
- Web dashboard for browsing history
- Personalized topic filtering
- Multi-language support
- Custom data source plugins

---

## Conclusion

This 4-week plan will bring the Python implementation to 85% feature parity with the original CloudFlare Worker, focusing on:

1. **Week 1**: Critical data sources (GitHub, Papers, Twitter)
2. **Week 2**: Advanced AI features (multi-step, podcast)
3. **Week 3**: GitHub archiving integration
4. **Week 4**: Remaining sources + polish

The result will be a production-ready, CLI-based daily AI intelligence pipeline suitable for personal use with optional GitHub archiving and multiple output formats.
