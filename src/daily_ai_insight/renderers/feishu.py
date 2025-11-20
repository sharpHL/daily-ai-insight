"""Feishu (Lark) renderer for reports."""

import os
import json
import time
import hmac
import hashlib
import base64
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeishuRenderer:
    """Render and send reports to Feishu."""

    def __init__(self, webhook_url: str = None, secret: str = None):
        """Initialize Feishu renderer.

        Args:
            webhook_url: Feishu webhook URL
            secret: Optional secret key for signature verification
        """
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK")
        self.secret = secret or os.getenv("FEISHU_SECRET")

        if not self.webhook_url:
            raise ValueError("Feishu webhook URL is required")

        if self.secret:
            logger.info("Feishu signature verification enabled")

    def _generate_sign(self, timestamp: int) -> str:
        """Generate signature for Feishu webhook.

        Args:
            timestamp: Current timestamp in seconds

        Returns:
            Base64 encoded signature
        """
        # Construct string to sign: timestamp + newline + secret
        string_to_sign = f"{timestamp}\n{self.secret}"

        # Generate HMAC-SHA256 signature
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        # Encode to base64
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return sign

    async def send(self, report_data: Dict[str, Any]) -> bool:
        """Send report to Feishu.

        Args:
            report_data: Report data dictionary

        Returns:
            True if successful
        """
        try:
            card = self._create_card(report_data)

            # Add signature if secret is configured
            if self.secret:
                timestamp = int(time.time())
                sign = self._generate_sign(timestamp)
                card["timestamp"] = str(timestamp)
                card["sign"] = sign
                logger.debug(f"Added signature: timestamp={timestamp}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get("StatusCode") == 0:
                        logger.info("Successfully sent report to Feishu")
                        return True
                    else:
                        logger.error(f"Failed to send to Feishu: {result}")
                        return False

        except Exception as e:
            logger.error(f"Error sending to Feishu: {e}")
            return False

    def _create_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Feishu interactive card.

        Args:
            data: Report data

        Returns:
            Card JSON structure
        """
        date = datetime.now().strftime("%Y-%m-%d")

        # Build card elements
        elements = []

        # Executive Summary
        if 'executive_summary' in data:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📋 Executive Summary**\n{data['executive_summary']}"
                }
            })
            elements.append({"tag": "hr"})

        # Key Points
        key_points = data.get('key_points', [])
        if key_points:
            points_text = "**🔥 Today's Highlights**\n\n"
            for point in key_points[:5]:
                if isinstance(point, dict):
                    importance = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(point.get('importance', 'medium'), '⚪')
                    points_text += f"{importance} **{point.get('title', '')}**\n"
                    points_text += f"{point.get('description', '')}\n\n"
                else:
                    points_text += f"• {point}\n"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": points_text
                }
            })
            elements.append({"tag": "hr"})

        # Trend Analysis
        trend_analysis = data.get('trend_analysis', {})
        if isinstance(trend_analysis, dict) and trend_analysis:
            trends_text = "**📊 Trend Analysis**\n\n"

            current = trend_analysis.get('current_trends', [])
            if current:
                trends_text += "Current Trends:\n"
                for trend in current[:3]:
                    trends_text += f"• {trend}\n"
                trends_text += "\n"

            emerging = trend_analysis.get('emerging_topics', [])
            if emerging:
                trends_text += "Emerging Topics:\n"
                for topic in emerging[:3]:
                    trends_text += f"• {topic}\n"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": trends_text
                }
            })
            elements.append({"tag": "hr"})

        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            rec_text = "**📝 Recommendations**\n\n"
            for rec in recommendations[:3]:
                if isinstance(rec, dict):
                    priority = {
                        'high': '🔥',
                        'medium': '⚡',
                        'low': '💡'
                    }.get(rec.get('priority', 'medium'), '📌')
                    rec_text += f"{priority} {rec.get('action', '')}\n"
                    if rec.get('reason'):
                        rec_text += f"   *Reason: {rec.get('reason')}*\n"
                else:
                    rec_text += f"• {rec}\n"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": rec_text
                }
            })
            elements.append({"tag": "hr"})

        # Notable Sources
        sources = data.get('notable_sources', [])
        if sources:
            sources_text = "**📚 Recommended Reading**\n\n"
            for idx, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    sources_text += f"{idx}. [{source.get('title', 'Link')}]({source.get('url', '#')})\n"
                    if source.get('reason'):
                        sources_text += f"   {source.get('reason')}\n"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": sources_text
                }
            })

        # Footer
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Powered by Daily AI Insight"
                }
            ]
        })

        # Build complete card
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🤖 AI Daily Insight - {date}"
                    },
                    "template": "blue"
                },
                "elements": elements
            }
        }

        return card

    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """Truncate text to fit Feishu limits.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    async def send_simple_message(self, message: str) -> bool:
        """Send a simple text message to Feishu.

        Args:
            message: Message text

        Returns:
            True if successful
        """
        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }

            # Add signature if secret is configured
            if self.secret:
                timestamp = int(time.time())
                sign = self._generate_sign(timestamp)
                payload["timestamp"] = str(timestamp)
                payload["sign"] = sign
                logger.debug(f"Added signature: timestamp={timestamp}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    return response.status == 200 and result.get("StatusCode") == 0

        except Exception as e:
            logger.error(f"Error sending simple message to Feishu: {e}")
            return False