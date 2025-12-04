#!/usr/bin/env python3
"""
Sync feedback from Cloudflare KV to local feedback.yaml.

This script is run by GitHub Actions before generating the daily report.
It fetches user feedback from the Cloudflare Worker API and updates
the local feedback.yaml file, which is then used to personalize the report.

Usage:
    python scripts/sync_feedback.py

Environment variables:
    FEEDBACK_API_URL: URL of the Cloudflare Worker (required)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
import aiohttp
import asyncio

FEEDBACK_PATH = Path("configs/feedback.yaml")


def load_feedback() -> dict[str, Any]:
    """Load existing feedback file."""
    if not FEEDBACK_PATH.exists():
        return {
            "feedback_log": [],
            "learned_preferences": {
                "additional_interests": [],
                "additional_filters": [],
                "keyword_adjustments": {},
                "source_adjustments": {},
            },
            "statistics": {
                "total_feedback_count": 0,
                "liked_count": 0,
                "disliked_count": 0,
            },
        }

    with open(FEEDBACK_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_feedback(data: dict[str, Any]) -> None:
    """Save feedback to file."""
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def learn_from_feedback(feedback_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze feedback and update learned preferences.

    This function:
    1. Counts liked/disliked items
    2. Extracts patterns from feedback
    3. Updates keyword adjustments
    """
    learned = feedback_data.get("learned_preferences", {})
    feedback_log = feedback_data.get("feedback_log", [])

    # Initialize counters
    keyword_counts: dict[str, int] = {}
    total_liked = 0
    total_disliked = 0

    # Analyze recent feedback (last 30 days)
    for entry in feedback_log[-30:]:
        items = entry.get("items", [])
        for item in items:
            action = item.get("action", "")
            title = item.get("title", "").lower()

            # Count actions
            if action == "want_more":
                total_liked += 1
                # Extract keywords from liked items
                for word in title.split():
                    if len(word) > 2:
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1
            elif action == "not_interested":
                total_disliked += 1
                # Negative weight for disliked keywords
                for word in title.split():
                    if len(word) > 2:
                        keyword_counts[word] = keyword_counts.get(word, 0) - 1

    # Update keyword adjustments (only significant patterns)
    keyword_adjustments = {}
    for keyword, count in keyword_counts.items():
        if abs(count) >= 2:  # Only if appears multiple times
            keyword_adjustments[keyword] = count

    # Update learned preferences
    learned["keyword_adjustments"] = keyword_adjustments

    # Update statistics
    feedback_data["statistics"] = {
        "total_feedback_count": sum(len(e.get("items", [])) for e in feedback_log),
        "liked_count": total_liked,
        "disliked_count": total_disliked,
        "last_updated": datetime.now().isoformat(),
    }

    feedback_data["learned_preferences"] = learned

    return feedback_data


async def fetch_feedback_from_api(api_url: str) -> list[dict[str, Any]]:
    """Fetch all feedback from Cloudflare Worker API."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{api_url}/feedback/all", timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"  API returned status {resp.status}")
                    return []

                data = await resp.json()
                return data.get("feedback", [])
        except Exception as e:
            print(f"  Error fetching feedback: {e}")
            return []


async def main():
    """Main entry point."""
    api_url = os.getenv("FEEDBACK_API_URL", "")

    if not api_url:
        print("FEEDBACK_API_URL not set, skipping feedback sync")
        return

    print(f"Fetching feedback from {api_url}...")

    # Fetch from API
    api_feedback = await fetch_feedback_from_api(api_url)
    print(f"  Fetched {len(api_feedback)} days of feedback")

    # Load existing feedback
    feedback_data = load_feedback()
    existing_dates = {e.get("date") for e in feedback_data.get("feedback_log", [])}

    # Merge new feedback
    new_count = 0
    for entry in api_feedback:
        date = entry.get("date")
        if date and date not in existing_dates:
            feedback_data.setdefault("feedback_log", []).append({
                "date": date,
                "items": entry.get("items", []),
            })
            new_count += 1

    print(f"  Added {new_count} new days of feedback")

    # Learn from feedback
    feedback_data = learn_from_feedback(feedback_data)

    # Save updated feedback
    save_feedback(feedback_data)
    print(f"  Saved to {FEEDBACK_PATH}")

    # Print summary
    stats = feedback_data.get("statistics", {})
    print(f"\nFeedback statistics:")
    print(f"  Total feedback: {stats.get('total_feedback_count', 0)}")
    print(f"  Liked: {stats.get('liked_count', 0)}")
    print(f"  Disliked: {stats.get('disliked_count', 0)}")

    learned = feedback_data.get("learned_preferences", {})
    adjustments = learned.get("keyword_adjustments", {})
    if adjustments:
        print(f"\nLearned keyword adjustments:")
        for kw, adj in sorted(adjustments.items(), key=lambda x: -abs(x[1]))[:10]:
            sign = "+" if adj > 0 else ""
            print(f"  {kw}: {sign}{adj}")


if __name__ == "__main__":
    asyncio.run(main())
