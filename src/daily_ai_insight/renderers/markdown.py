"""Markdown renderer for reports."""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Render reports in Markdown format."""

    def render(self, report_data: Dict[str, Any]) -> str:
        """Render report data as Markdown.

        Args:
            report_data: Report data dictionary

        Returns:
            Markdown formatted report
        """
        try:
            # If report_data is already a formatted markdown string, return it
            if isinstance(report_data, str):
                return report_data

            # Otherwise, format the data
            return self._format_report(report_data)

        except Exception as e:
            logger.error(f"Error rendering Markdown: {e}")
            return self._error_report(str(e))

    def _format_report(self, data: Dict[str, Any]) -> str:
        """Format report data as Markdown.

        Args:
            data: Report data dictionary

        Returns:
            Formatted Markdown
        """
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M")

        md = f"""# 🤖 AI Daily Insight Report

## 📅 Date: {date}

## 📋 Executive Summary

{data.get('executive_summary', 'No summary available')}

## 🔥 Key Points

"""

        # Add key points
        key_points = data.get('key_points', [])
        for point in key_points:
            if isinstance(point, dict):
                importance_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(point.get('importance', 'medium'), '⚪')

                md += f"### {importance_emoji} {point.get('title', 'Untitled')}\n\n"
                md += f"{point.get('description', '')}\n\n"
            else:
                md += f"- {point}\n"

        # Trend Analysis
        md += "\n## 📊 Trend Analysis\n\n"

        trend_analysis = data.get('trend_analysis', {})
        if isinstance(trend_analysis, dict):
            current_trends = trend_analysis.get('current_trends', [])
            if current_trends:
                md += "### Current Trends\n"
                for trend in current_trends:
                    md += f"- {trend}\n"
                md += "\n"

            emerging_topics = trend_analysis.get('emerging_topics', [])
            if emerging_topics:
                md += "### Emerging Topics\n"
                for topic in emerging_topics:
                    md += f"- {topic}\n"
                md += "\n"

            declining_topics = trend_analysis.get('declining_topics', [])
            if declining_topics:
                md += "### Declining Topics\n"
                for topic in declining_topics:
                    md += f"- {topic}\n"
                md += "\n"
        else:
            md += f"{trend_analysis}\n\n"

        # Impact Assessment
        md += "## 💡 Impact Assessment\n\n"
        md += f"{data.get('impact_assessment', 'No assessment available')}\n\n"

        # Professional Insights
        md += "## 🎯 Professional Insights\n\n"
        md += f"{data.get('professional_insights', 'No insights available')}\n\n"

        # Recommendations
        md += "## 📝 Recommendations\n\n"
        recommendations = data.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    priority_emoji = {
                        'high': '🔥',
                        'medium': '⚡',
                        'low': '💡'
                    }.get(rec.get('priority', 'medium'), '📌')

                    md += f"- {priority_emoji} **{rec.get('action', '')}**\n"
                    if rec.get('reason'):
                        md += f"  - *Reason: {rec.get('reason')}*\n"
                else:
                    md += f"- {rec}\n"
            md += "\n"

        # Notable Sources
        md += "## 📚 Recommended Reading\n\n"
        notable_sources = data.get('notable_sources', [])
        if notable_sources:
            for idx, source in enumerate(notable_sources, 1):
                if isinstance(source, dict):
                    md += f"{idx}. **[{source.get('title', 'Untitled')}]({source.get('url', '#')})**\n"
                    if source.get('reason'):
                        md += f"   - {source.get('reason')}\n"
                    md += "\n"
                else:
                    md += f"{idx}. {source}\n"

        # Statistics
        if 'statistics' in data:
            md += "## 📈 Statistics\n\n"
            stats = data['statistics']
            if isinstance(stats, dict):
                for key, value in stats.items():
                    md += f"- **{key}**: {value}\n"
            md += "\n"

        # Footer
        md += f"""
---

*Report generated at {date} {time}*
*Powered by Daily AI Insight*
🤖 *Your Personal AI Intelligence Pipeline*
"""

        return md

    def _error_report(self, error_msg: str) -> str:
        """Generate error report.

        Args:
            error_msg: Error message

        Returns:
            Error report in Markdown
        """
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""# ⚠️ Report Generation Error

## Date: {date}

## Error Details

```
{error_msg}
```

## What to do?

1. Check the logs for more details
2. Verify API keys and configuration
3. Ensure data collection was successful
4. Try regenerating the report

---
*Daily AI Insight - Error Report*
"""

    def render_simple_list(self, items: List[Dict[str, Any]]) -> str:
        """Render items as a simple Markdown list.

        Args:
            items: List of content items

        Returns:
            Markdown formatted list
        """
        md = "# Content List\n\n"

        for item in items:
            md += f"## {item.get('title', 'Untitled')}\n\n"
            md += f"**Source**: {item.get('source', 'Unknown')}\n"
            md += f"**Published**: {item.get('published_at', 'Unknown')}\n"
            md += f"**URL**: {item.get('url', '#')}\n\n"
            md += f"{item.get('content', '')[:200]}...\n\n"
            md += "---\n\n"

        return md