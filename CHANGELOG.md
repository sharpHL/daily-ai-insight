# Changelog

## [2.0.1] - 2024-11-25

### Fixed
- **Critical date filtering bug** - Fixed timezone comparison issue in `is_date_within_last_days`
  - Issue: Comparing timezone-aware API dates with naive local datetime caused TypeError
  - Impact: All Follow.is collectors (Twitter, Reddit, etc.) returned 0 items despite API returning data
  - Solution: Use `datetime.now(timezone.utc)` for timezone-aware comparison
  - Result: Follow.is collectors now successfully fetch data (verified with 60 items from Twitter/Reddit/News)

## [2.0.0] - 2024-11-24

### Major Architecture Refactoring
- **Unified collector architecture** - All Follow.is collectors now use single `FollowCollector` base class
- **Code reduction** - 41% less code (1,705 → 1,000 lines)
- **Simplified collectors** - Each collector now only 19-28 lines (was 100+ lines)
- **Removed duplicate base classes** - Consolidated `follow_base.py` and `folo_base.py`

### Added
- Hybrid storage system (Git + JSON)
- Async storage API
- Auto Git commits for data persistence
- 9 new data collectors with full coverage

### Improved
- Test coverage to 100%
- Performance optimization (0.004ms init speed)
- Chinese encoding fixes
- Documentation cleanup

## [1.0.0] - 2024-11-20

### Initial Release
- Multi-source data collection (Follow.is RSS)
- AI analysis with Gemini/OpenAI
- Multi-channel delivery (Feishu, Telegram)
- GitHub Actions automation
- Data deduplication and cleaning