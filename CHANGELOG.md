# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Feishu Webhook Signature Verification** (2025-01-20)
  - Added signature verification support for enhanced security
  - New `FEISHU_SECRET` environment variable
  - HMAC-SHA256 signature generation and validation
  - Automatic timestamp and signature inclusion in webhook requests
  - Comprehensive documentation in `docs/feishu-signature.md`
  - Unit tests for signature generation
  - Test script `scripts/test_signature.py` for manual verification

### Changed
- **FeishuRenderer** class updated:
  - Added `secret` parameter to `__init__()` method
  - Added `_generate_sign()` method for signature generation
  - Updated `send()` method to include signature when secret is configured
  - Updated `send_simple_message()` method to include signature when secret is configured
  - Added logging for signature verification status

## [0.1.0] - 2025-01-XX

### Added
- Initial project structure with src-layout
- FOLO RSS collector with Cookie authentication
- Data cleaning and deduplication processors
- LLM integration (Gemini and OpenAI)
- Multi-channel output (Feishu, Telegram, Markdown)
- GitHub Actions workflow for daily execution
- Comprehensive test framework
- Makefile for common operations
- Full documentation

### Features
- Collect data from FOLO RSS aggregator
- Clean and deduplicate content
- Analyze with AI (Gemini/OpenAI)
- Generate structured daily reports
- Push to Feishu and Telegram
- Automated daily execution via GitHub Actions

[Unreleased]: https://github.com/yourusername/daily-ai-insight/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/daily-ai-insight/releases/tag/v0.1.0
