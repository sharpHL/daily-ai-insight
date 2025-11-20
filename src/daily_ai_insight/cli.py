#!/usr/bin/env python3
"""Daily AI Insight - CLI entry point."""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

# Import modules
from daily_ai_insight.collectors import (
    # Original collectors
    RedditCollector,
    XiaohuCollector,
    NewsAggregatorCollector,
    # New collectors
    GitHubTrendingCollector,
    PapersCollector,
    TwitterCollector,
    AIBaseCollector,
    JiqizhixinCollector,
    QBitCollector,
    XinZhiYuanCollector,
)
from daily_ai_insight.processors import DataCleaner, Deduplicator
from daily_ai_insight.storage import create_storage
from daily_ai_insight.llm import ContentAnalyzer
from daily_ai_insight.renderers import MarkdownRenderer, FeishuRenderer, TelegramRenderer

# Load environment variables
load_dotenv()

# Setup rich console
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "false").lower() != "true" else logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


class DailyInsightPipeline:
    """Main pipeline for Daily AI Insight."""

    def __init__(self):
        self.storage = create_storage()  # Auto-configured from .env
        self.cleaner = DataCleaner()
        self.deduper = Deduplicator()
        self.analyzer = ContentAnalyzer(provider="gemini")
        self.markdown_renderer = MarkdownRenderer()

        # Initialize renderers based on available credentials
        self.feishu_renderer = None
        self.telegram_renderer = None

        if os.getenv("FEISHU_WEBHOOK"):
            try:
                self.feishu_renderer = FeishuRenderer()
                logger.info("✅ Feishu renderer initialized")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Feishu: {e}")

        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            try:
                self.telegram_renderer = TelegramRenderer()
                logger.info("✅ Telegram renderer initialized")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Telegram: {e}")

    async def run(self, skip_collection: bool = False, skip_analysis: bool = False):
        """Run the complete pipeline.

        Args:
            skip_collection: Skip data collection phase
            skip_analysis: Skip LLM analysis phase
        """
        console.print("\n[bold cyan]🚀 Starting Daily AI Insight Pipeline[/bold cyan]\n")

        try:
            # Step 1: Collect data
            if not skip_collection:
                items = await self._collect_data()
            else:
                console.print("[yellow]⏭️  Skipping data collection, using existing data[/yellow]")
                items = await self.storage.load_recent(hours=24)

            if not items:
                console.print("[red]❌ No data collected or available[/red]")
                return

            console.print(f"[green]✅ Collected {len(items)} items[/green]")

            # Step 2: Clean and deduplicate
            items = await self._process_data(items)
            console.print(f"[green]✅ Processed to {len(items)} unique items[/green]")

            # Save processed data
            await self.storage.save_raw(items, source="processed")

            # Step 3: Analyze with LLM
            if not skip_analysis:
                analysis = await self._analyze_content(items)
            else:
                console.print("[yellow]⏭️  Skipping LLM analysis[/yellow]")
                analysis = self._create_basic_analysis(items)

            # Step 4: Generate report
            report = await self._generate_report(analysis, items)

            # Step 5: Save and send report
            await self._distribute_report(report, analysis)

            console.print("\n[bold green]✅ Pipeline completed successfully![/bold green]")

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise

    async def _collect_data(self) -> List[Dict[str, Any]]:
        """Collect data from sources."""
        all_items = []

        # Initialize collectors
        collectors = [
            # Original collectors
            RedditCollector(),
            XiaohuCollector(),
            NewsAggregatorCollector(),
            # New collectors
            GitHubTrendingCollector(),
            PapersCollector(),
            TwitterCollector(),
            AIBaseCollector(),
            JiqizhixinCollector(),
            QBitCollector(),
            XinZhiYuanCollector(),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            for collector in collectors:
                task = progress.add_task(
                    f"[cyan]Collecting data from {collector.name}...",
                    total=None
                )

                try:
                    # Fetch raw data
                    raw_data = await collector.fetch()

                    # Transform to unified format
                    items = collector.transform(raw_data, collector.name.lower().replace(" ", "-"))

                    all_items.extend(items)
                    progress.update(
                        task,
                        description=f"[green]✓ Collected {len(items)} items from {collector.name}",
                        completed=True
                    )

                except Exception as e:
                    logger.error(f"Failed to collect from {collector.name}: {e}")
                    progress.update(
                        task,
                        description=f"[red]✗ Failed to collect from {collector.name}"
                    )

        return all_items

    async def _process_data(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and deduplicate data."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Clean data
            task = progress.add_task("[cyan]Cleaning data...", total=None)
            items = self.cleaner.clean(items)
            progress.update(task, completed=True)

            # Deduplicate
            task = progress.add_task("[cyan]Removing duplicates...", total=None)
            items = self.deduper.deduplicate(items)
            progress.update(task, completed=True)

        return items

    async def _analyze_content(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content with LLM."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing with AI...", total=None)

            try:
                # Filter relevant content first
                relevant_items = await self.analyzer.filter_relevant_content(items)
                console.print(f"[yellow]Filtered to {len(relevant_items)} relevant items[/yellow]")

                # Analyze
                analysis = await self.analyzer.analyze_content(relevant_items)
                progress.update(task, completed=True)

                # Save analysis
                await self.storage.save_processed(analysis, report_type="analysis")

                return analysis

            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                progress.update(task, description="[red]Analysis failed")
                return self._create_basic_analysis(items)

    def _create_basic_analysis(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create basic analysis without LLM."""
        return {
            "executive_summary": f"Collected {len(items)} items from data sources",
            "key_points": [
                {
                    "title": item.get("title", ""),
                    "description": item.get("content", "")[:100],
                    "importance": "medium"
                }
                for item in items[:5]
            ],
            "trend_analysis": {
                "current_trends": ["Data collection successful"],
                "emerging_topics": [],
                "declining_topics": []
            },
            "impact_assessment": "Manual review required",
            "professional_insights": "LLM analysis not available",
            "recommendations": [
                {
                    "action": "Review collected data manually",
                    "reason": "Automated analysis unavailable",
                    "priority": "high"
                }
            ],
            "notable_sources": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "reason": "Recent content"
                }
                for item in items[:3]
            ]
        }

    async def _generate_report(self, analysis: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Generate report from analysis."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Generating report...", total=None)

            try:
                # Try to generate with LLM
                report = await self.analyzer.generate_report(analysis, items)
            except Exception as e:
                logger.warning(f"LLM report generation failed: {e}")
                # Fallback to template-based generation
                report = self.markdown_renderer.render(analysis)

            progress.update(task, completed=True)

        return report

    async def _distribute_report(self, report: str, analysis: Dict[str, Any]):
        """Save and distribute report."""
        # Save to file
        report_path = await self.storage.save_report(report, format="markdown")
        console.print(f"[green]✅ Report saved to: {report_path}[/green]")

        # Send to channels
        tasks = []

        if self.feishu_renderer:
            tasks.append(self._send_to_feishu(analysis))

        if self.telegram_renderer:
            tasks.append(self._send_to_telegram(analysis))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to send to channel {i}: {result}")

    async def _send_to_feishu(self, analysis: Dict[str, Any]):
        """Send report to Feishu."""
        try:
            success = await self.feishu_renderer.send(analysis)
            if success:
                console.print("[green]✅ Report sent to Feishu[/green]")
            else:
                console.print("[red]❌ Failed to send to Feishu[/red]")
        except Exception as e:
            logger.error(f"Feishu error: {e}")

    async def _send_to_telegram(self, analysis: Dict[str, Any]):
        """Send report to Telegram."""
        try:
            success = await self.telegram_renderer.send(analysis)
            if success:
                console.print("[green]✅ Report sent to Telegram[/green]")
            else:
                console.print("[red]❌ Failed to send to Telegram[/red]")
        except Exception as e:
            logger.error(f"Telegram error: {e}")


async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Daily AI Insight Pipeline")
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip data collection and use existing data"
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip LLM analysis"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup old files"
    )

    args = parser.parse_args()

    # Cleanup if requested
    if args.cleanup:
        storage = create_storage()
        await storage.cleanup(days=7)
        console.print("[green]✅ Cleaned up old files[/green]")
        return

    # Run pipeline
    pipeline = DailyInsightPipeline()
    await pipeline.run(
        skip_collection=args.skip_collection,
        skip_analysis=args.skip_analysis
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Pipeline interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Pipeline failed: {e}[/red]")
        sys.exit(1)