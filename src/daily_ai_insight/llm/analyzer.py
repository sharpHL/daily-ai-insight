"""Content analyzer using LLM providers."""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .providers.gemini import GeminiProvider
from .providers.openai import OpenAIProvider
from .prompts.templates import (
    ANALYSIS_PROMPT,
    REPORT_GENERATION_PROMPT,
    SUMMARY_PROMPT,
    CATEGORIZATION_PROMPT,
    FILTER_PROMPT
)

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyze content using LLM providers."""

    def __init__(self, provider: str = "gemini"):
        """Initialize content analyzer.

        Args:
            provider: LLM provider to use ("gemini" or "openai")
        """
        self.provider_name = provider

        try:
            if provider == "gemini":
                self.provider = GeminiProvider()
            elif provider == "openai":
                self.provider = OpenAIProvider()
            else:
                # Default to Gemini
                self.provider = GeminiProvider()
                self.provider_name = "gemini"
        except Exception as e:
            logger.warning(f"Failed to initialize {provider}: {e}")
            # Try fallback
            if provider == "gemini":
                logger.info("Trying OpenAI as fallback")
                self.provider = OpenAIProvider()
                self.provider_name = "openai"
            else:
                logger.info("Trying Gemini as fallback")
                self.provider = GeminiProvider()
                self.provider_name = "gemini"

    async def analyze_content(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collected content items.

        Args:
            items: List of content items

        Returns:
            Analysis results
        """
        if not items:
            logger.warning("No items to analyze")
            return {}

        # Prepare content for analysis
        content_data = self._prepare_content_for_analysis(items)

        # Generate prompt
        prompt = ANALYSIS_PROMPT.format(content=json.dumps(content_data, ensure_ascii=False, indent=2))

        # Check token count and truncate if needed
        token_count = self.provider.count_tokens(prompt)
        if token_count > 10000:
            logger.warning(f"Content too long ({token_count} tokens), truncating...")
            content_data = content_data[:30]  # Limit to 30 items
            prompt = ANALYSIS_PROMPT.format(content=json.dumps(content_data, ensure_ascii=False, indent=2))

        # Analyze with LLM
        try:
            analysis = await self.provider.analyze(prompt)
            logger.info(f"Successfully analyzed {len(items)} items using {self.provider_name}")
            return analysis
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return basic analysis on failure
            return self._fallback_analysis(items)

    async def generate_report(self, analysis: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Generate a formatted report from analysis.

        Args:
            analysis: Analysis results from LLM
            items: Original content items

        Returns:
            Markdown formatted report
        """
        # Prepare insights data
        insights = {
            "analysis": analysis,
            "total_items": len(items),
            "sources": list(set(item.get("source", "unknown") for item in items)),
            "categories": self._categorize_items(items)
        }

        # Generate report prompt
        prompt = REPORT_GENERATION_PROMPT.format(
            insights=json.dumps(insights, ensure_ascii=False, indent=2),
            date=datetime.now().strftime("%Y-%m-%d"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        try:
            report = await self.provider.generate_text(prompt, max_tokens=3000)
            logger.info(f"Successfully generated report using {self.provider_name}")

            # Add metadata
            report = self._add_report_metadata(report, analysis, items)

            return report
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            # Generate basic report on failure
            return self._generate_basic_report(analysis, items)

    async def summarize_item(self, item: Dict[str, Any]) -> str:
        """Generate summary for a single item.

        Args:
            item: Content item

        Returns:
            Summary text
        """
        content = f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}"
        prompt = SUMMARY_PROMPT.format(content=content)

        try:
            summary = await self.provider.generate_text(prompt, max_tokens=200)
            return summary.strip()
        except:
            # Fallback to truncation
            return item.get("content", "")[:100] + "..."

    async def filter_relevant_content(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter content for relevance.

        Args:
            items: List of content items

        Returns:
            Filtered list of relevant items
        """
        relevant_items = []

        for item in items:
            # Quick keyword check first
            if self._quick_relevance_check(item):
                relevant_items.append(item)
                continue

            # Use LLM for uncertain cases
            content = f"Title: {item.get('title', '')}\nContent: {item.get('content', '')[:500]}"
            prompt = FILTER_PROMPT.format(content=content)

            try:
                result = await self.provider.analyze(prompt)
                if result.get("include", False) or result.get("relevance_score", 0) >= 6:
                    relevant_items.append(item)
            except:
                # Keep item on error
                relevant_items.append(item)

        logger.info(f"Filtered {len(items)} items to {len(relevant_items)} relevant items")
        return relevant_items

    def _prepare_content_for_analysis(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare content for LLM analysis.

        Args:
            items: Raw content items

        Returns:
            Prepared content list
        """
        prepared = []

        for item in items[:50]:  # Limit to 50 items
            prepared.append({
                "title": item.get("title", ""),
                "content": item.get("content", "")[:500],  # Truncate content
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "published_at": str(item.get("published_at", "")),
                "tags": item.get("tags", [])
            })

        return prepared

    def _categorize_items(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize items by tags/source.

        Args:
            items: Content items

        Returns:
            Category counts
        """
        categories = {}

        for item in items:
            tags = item.get("tags", [])
            if not tags:
                tags = [item.get("source", "other")]

            for tag in tags:
                categories[tag] = categories.get(tag, 0) + 1

        return categories

    def _quick_relevance_check(self, item: Dict[str, Any]) -> bool:
        """Quick keyword-based relevance check.

        Args:
            item: Content item

        Returns:
            True if likely relevant
        """
        ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "deep learning",
            "neural", "gpt", "llm", "transformer", "neural network", "large language model",
            "generative ai", "foundation model"
        ]

        content = (item.get("title", "") + " " + item.get("content", "")).lower()

        return any(keyword in content for keyword in ai_keywords)

    def _fallback_analysis(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic analysis without LLM.

        Args:
            items: Content items

        Returns:
            Basic analysis dictionary
        """
        return {
            "executive_summary": f"Collected {len(items)} AI-related items today",
            "key_points": [
                {
                    "title": item.get("title", ""),
                    "description": item.get("content", "")[:100],
                    "importance": "medium"
                }
                for item in items[:5]
            ],
            "trend_analysis": {
                "current_trends": ["AI technology continues to evolve"],
                "emerging_topics": ["To be analyzed"],
                "declining_topics": []
            },
            "impact_assessment": "Requires further analysis",
            "professional_insights": "LLM analysis temporarily unavailable",
            "recommendations": [
                {
                    "action": "Review raw data",
                    "reason": "Automated analysis failed",
                    "priority": "high"
                }
            ],
            "notable_sources": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "reason": "Today's popular content"
                }
                for item in items[:3]
            ]
        }

    def _generate_basic_report(self, analysis: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Generate basic report without LLM.

        Args:
            analysis: Analysis results
            items: Content items

        Returns:
            Basic markdown report
        """
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M")

        report = f"""# AI Daily Insight Report

## 📅 Date: {date}

## 📋 Executive Summary

{analysis.get('executive_summary', 'AI industry information summary for today')}

## 🔥 Today's Highlights

"""

        # Add key points
        for point in analysis.get("key_points", [])[:5]:
            report += f"- **{point.get('title', '')}**: {point.get('description', '')}\n"

        report += "\n## 📊 Content Statistics\n\n"
        report += f"- Total collected: {len(items)} items\n"
        report += f"- Data sources: {len(set(item.get('source', '') for item in items))} sources\n"

        report += "\n## 📚 Recommended Reading\n\n"

        # Add notable sources
        for idx, source in enumerate(analysis.get("notable_sources", [])[:5], 1):
            report += f"{idx}. **{source.get('title', '')}**\n"
            report += f"   - Link: {source.get('url', '')}\n"
            report += f"   - Reason: {source.get('reason', '')}\n\n"

        report += f"\n---\n*Report generated at: {date} {time}*"

        return report

    def _add_report_metadata(self, report: str, analysis: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Add metadata to report.

        Args:
            report: Generated report
            analysis: Analysis results
            items: Content items

        Returns:
            Report with metadata
        """
        metadata = f"""

---

## 📈 Data Statistics

- **Data Sources**: {len(set(item.get('source', '') for item in items))} sources
- **Content Count**: {len(items)} items
- **Analysis Model**: {self.provider_name.upper()}
- **Generated At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*Powered by Daily AI Insight - Your Personal Intelligence Pipeline*
"""

        return report + metadata