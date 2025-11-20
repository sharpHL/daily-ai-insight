"""Telegram renderer for reports."""

import os
import aiohttp
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TelegramRenderer:
    """Render and send reports to Telegram."""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot token and chat ID are required")

        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def send(self, report_data: Dict[str, Any]) -> bool:
        """Send report to Telegram.

        Args:
            report_data: Report data dictionary

        Returns:
            True if successful
        """
        try:
            # Convert report to Telegram format
            messages = self._format_for_telegram(report_data)

            # Send messages (split if too long)
            for message in messages:
                success = await self._send_message(message)
                if not success:
                    return False

            logger.info("Successfully sent report to Telegram")
            return True

        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False

    async def _send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a single message to Telegram.

        Args:
            text: Message text
            parse_mode: Parse mode (Markdown or HTML)

        Returns:
            True if successful
        """
        try:
            # Escape special characters for Telegram MarkdownV2
            if parse_mode == "MarkdownV2":
                text = self._escape_markdown_v2(text)

            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendMessage",
                    json=payload
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get("ok"):
                        return True
                    else:
                        logger.error(f"Telegram API error: {result}")
                        # Try with plain text if markdown fails
                        if parse_mode != "":
                            return await self._send_message(text, parse_mode="")
                        return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def _format_for_telegram(self, data: Dict[str, Any]) -> List[str]:
        """Format report data for Telegram.

        Args:
            data: Report data

        Returns:
            List of formatted messages
        """
        messages = []
        date = datetime.now().strftime("%Y-%m-%d")

        # Header message
        header = f"""🤖 *AI Daily Insight Report*
📅 *Date:* {date}

"""

        # Executive Summary
        if 'executive_summary' in data:
            header += f"📋 *Executive Summary*\n{data['executive_summary']}\n\n"

        messages.append(header)

        # Key Points
        key_points = data.get('key_points', [])
        if key_points:
            points_msg = "*🔥 Key Points*\n\n"
            for point in key_points[:5]:
                if isinstance(point, dict):
                    importance = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(point.get('importance', 'medium'), '⚪')
                    points_msg += f"{importance} *{point.get('title', '')}*\n"
                    desc = point.get('description', '')[:100]
                    points_msg += f"{desc}\n\n"
                else:
                    points_msg += f"• {point}\n"

            messages.append(points_msg)

        # Trend Analysis
        trend_analysis = data.get('trend_analysis', {})
        if isinstance(trend_analysis, dict) and trend_analysis:
            trends_msg = "*📊 Trend Analysis*\n\n"

            current = trend_analysis.get('current_trends', [])
            if current:
                trends_msg += "*Current Trends:*\n"
                for trend in current[:3]:
                    trends_msg += f"• {trend}\n"
                trends_msg += "\n"

            emerging = trend_analysis.get('emerging_topics', [])
            if emerging:
                trends_msg += "*Emerging Topics:*\n"
                for topic in emerging[:3]:
                    trends_msg += f"• {topic}\n"

            messages.append(trends_msg)

        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            rec_msg = "*📝 Recommendations*\n\n"
            for rec in recommendations[:3]:
                if isinstance(rec, dict):
                    priority = {
                        'high': '🔥',
                        'medium': '⚡',
                        'low': '💡'
                    }.get(rec.get('priority', 'medium'), '📌')
                    rec_msg += f"{priority} {rec.get('action', '')}\n"
                    if rec.get('reason'):
                        rec_msg += f"   _Reason: {rec.get('reason')}_\n"
                    rec_msg += "\n"
                else:
                    rec_msg += f"• {rec}\n"

            messages.append(rec_msg)

        # Notable Sources
        sources = data.get('notable_sources', [])
        if sources:
            sources_msg = "*📚 Recommended Reading*\n\n"
            for idx, source in enumerate(sources[:5], 1):
                if isinstance(source, dict):
                    title = source.get('title', 'Link')[:50]
                    url = source.get('url', '#')
                    sources_msg += f"{idx}. [{title}]({url})\n"
                    if source.get('reason'):
                        sources_msg += f"   _{source.get('reason')}_\n"
                    sources_msg += "\n"

            messages.append(sources_msg)

        # Footer
        footer = f"\n_Generated at {datetime.now().strftime('%H:%M:%S')}_\n"
        footer += "_Powered by Daily AI Insight_ 🤖"
        messages.append(footer)

        # Split messages if they're too long
        return self._split_long_messages(messages)

    def _split_long_messages(self, messages: List[str], max_length: int = 4000) -> List[str]:
        """Split messages that are too long for Telegram.

        Args:
            messages: List of messages
            max_length: Maximum message length

        Returns:
            List of split messages
        """
        result = []

        for message in messages:
            if len(message) <= max_length:
                result.append(message)
            else:
                # Split by paragraphs first
                parts = message.split('\n\n')
                current = ""

                for part in parts:
                    if len(current) + len(part) + 2 <= max_length:
                        if current:
                            current += "\n\n"
                        current += part
                    else:
                        if current:
                            result.append(current)
                        current = part

                if current:
                    result.append(current)

        return result

    def _escape_markdown_v2(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        # Characters that need escaping in MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

        for char in special_chars:
            text = text.replace(char, f'\\{char}')

        return text

    async def send_simple_message(self, message: str) -> bool:
        """Send a simple text message to Telegram.

        Args:
            message: Message text

        Returns:
            True if successful
        """
        return await self._send_message(message, parse_mode="")