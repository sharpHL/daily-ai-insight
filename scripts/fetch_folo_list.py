#!/usr/bin/env python3
"""
Fetch and filter Folo list content based on user profile interests.

Usage:
    python scripts/fetch_folo_list.py

Requires FOLO_COOKIE and GEMINI_API_KEY in .env
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LIST_ID = "216345814850997248"
FOLO_API = "https://api.follow.is/entries"
FILTER_DAYS = 15  # Look back 15 days (half month)

# User profile for filtering
USER_PROFILE = {
    "roles": ["算法工程师", "AI爱好者"],
    "interests": ["AI前沿追踪", "效率提升", "机器学习", "深度学习", "LLM", "开源工具"],
}

# Keywords for fast filtering (first pass)
RELEVANCE_KEYWORDS = {
    "high": [
        # AI/ML core
        "llm", "large language model", "gpt", "claude", "gemini", "transformer",
        "neural network", "deep learning", "machine learning", "ai model",
        "embedding", "fine-tuning", "rag", "agent", "多模态", "大模型",
        # Efficiency
        "productivity", "workflow", "automation", "效率", "工具",
        # Research
        "paper", "arxiv", "研究", "论文", "benchmark",
        # Engineering
        "algorithm", "算法", "优化", "inference", "训练",
    ],
    "medium": [
        # General tech
        "api", "sdk", "framework", "library", "开源",
        "python", "rust", "typescript",
        # Platforms
        "openai", "anthropic", "google ai", "huggingface",
        # Topics
        "nlp", "cv", "computer vision", "speech",
    ],
}

# Categories for grouping
CATEGORIES = {
    "AI Research & Papers": ["paper", "arxiv", "研究", "论文", "benchmark", "sota"],
    "LLM & Agents": ["llm", "gpt", "claude", "gemini", "agent", "大模型", "prompt"],
    "Tools & Libraries": ["tool", "library", "framework", "sdk", "开源", "github"],
    "Efficiency & Productivity": ["productivity", "workflow", "效率", "automation", "工具"],
    "Industry News": ["funding", "launch", "release", "发布", "融资", "收购"],
}


def get_headers() -> dict[str, str]:
    """Get API headers with cookie."""
    cookie = os.getenv("FOLO_COOKIE", "")
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "accept": "application/json",
        "origin": "https://app.folo.is",
        "Cookie": cookie,
    }


def strip_html(html_content: str) -> str:
    """Strip HTML tags from content."""
    if not html_content:
        return ""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator="\n", strip=True)


def keyword_relevance_score(title: str, content: str) -> tuple[int, str]:
    """
    Calculate relevance score based on keywords.

    Returns:
        (score, matched_keyword) - score 0-10, highest matched keyword
    """
    text = (title + " " + content).lower()

    # Check high relevance keywords
    for keyword in RELEVANCE_KEYWORDS["high"]:
        if keyword.lower() in text:
            return (8, keyword)

    # Check medium relevance keywords
    for keyword in RELEVANCE_KEYWORDS["medium"]:
        if keyword.lower() in text:
            return (5, keyword)

    return (0, "")


def categorize_item(title: str, content: str) -> str:
    """Categorize item based on keywords."""
    text = (title + " " + content).lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category

    return "Other"


async def fetch_list_content() -> list[dict[str, Any]]:
    """Fetch content from Folo list."""
    all_items = []
    published_after = None

    print(f"Fetching content from list {LIST_ID}...")

    async with aiohttp.ClientSession() as session:
        for page in range(15):  # Fetch up to 15 pages for half month data
            body = {
                "view": 1,
                "withContent": True,
                "listId": LIST_ID,
            }
            if published_after:
                body["publishedAfter"] = published_after

            try:
                async with session.post(
                    FOLO_API,
                    headers=get_headers(),
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        print(f"  Page {page + 1}: HTTP {resp.status}")
                        break

                    data = await resp.json()

                    if not data or not data.get("data"):
                        print(f"  Page {page + 1}: No more data")
                        break

                    page_items = []
                    for entry in data["data"]:
                        if not entry.get("entries"):
                            continue

                        entries = entry["entries"]
                        feeds = entry.get("feeds", {})

                        item = {
                            "id": entries.get("id", ""),
                            "title": entries.get("title", ""),
                            "url": entries.get("url", ""),
                            "content_html": entries.get("content", ""),
                            "content_text": strip_html(entries.get("content", "")),
                            "published_at": entries.get("publishedAt", ""),
                            "author": entries.get("author", ""),
                            "source": feeds.get("title", "Unknown"),
                        }
                        page_items.append(item)

                    all_items.extend(page_items)
                    print(f"  Page {page + 1}: {len(page_items)} items")

                    # Update cursor
                    if data["data"]:
                        published_after = data["data"][-1]["entries"]["publishedAt"]

                    # Small delay between pages
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"  Page {page + 1}: Error - {e}")
                break

    print(f"Total fetched: {len(all_items)} items")
    return all_items


async def llm_filter_item(item: dict[str, Any], gemini_key: str) -> dict[str, Any] | None:
    """Use LLM to evaluate borderline items."""
    import google.generativeai as genai

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""You are filtering content for an AI engineer interested in:
- AI/ML research and papers
- LLM and agent development
- Productivity tools and efficiency
- Algorithm engineering

Evaluate this content:
Title: {item['title']}
Content: {item['content_text'][:500]}

Return JSON only:
{{"include": true/false, "reason": "brief reason", "category": "AI Research|LLM & Agents|Tools|Efficiency|Industry|Skip", "summary": "1-2 sentence summary if include=true"}}
"""

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        # Handle case where LLM returns a list instead of dict
        if isinstance(result, list):
            result = result[0] if result else {}
        return result
    except Exception as e:
        print(f"    LLM error for '{item['title'][:30]}...': {e}")
        return None


async def filter_and_categorize(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Filter items and group by category."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    categorized: dict[str, list[dict[str, Any]]] = {cat: [] for cat in CATEGORIES}
    categorized["Other"] = []

    borderline_items = []

    print("\nFiltering content...")

    # First pass: keyword filtering
    for item in items:
        score, keyword = keyword_relevance_score(item["title"], item["content_text"])

        if score >= 8:
            # High relevance - include directly
            category = categorize_item(item["title"], item["content_text"])
            item["relevance"] = "high"
            item["matched_keyword"] = keyword
            categorized[category].append(item)
        elif score >= 5:
            # Medium relevance - queue for LLM evaluation
            item["keyword_score"] = score
            item["matched_keyword"] = keyword
            borderline_items.append(item)
        # score < 5: skip

    print(f"  Keyword filter: {sum(len(v) for v in categorized.values())} high relevance")
    print(f"  Borderline items for LLM: {len(borderline_items)}")

    # Second pass: LLM filtering for borderline items
    if borderline_items and gemini_key:
        print("  Running LLM evaluation...")
        for i, item in enumerate(borderline_items[:20]):  # Limit to 20 for cost
            result = await llm_filter_item(item, gemini_key)
            if result and result.get("include"):
                category = result.get("category", "Other")
                # Map LLM category to our categories
                if category in categorized:
                    pass
                elif "Research" in category or "Paper" in category:
                    category = "AI Research & Papers"
                elif "LLM" in category or "Agent" in category:
                    category = "LLM & Agents"
                elif "Tool" in category:
                    category = "Tools & Libraries"
                elif "Efficiency" in category or "Productivity" in category:
                    category = "Efficiency & Productivity"
                elif "Industry" in category or "News" in category:
                    category = "Industry News"
                else:
                    category = "Other"

                item["relevance"] = "medium"
                item["llm_summary"] = result.get("summary", "")
                item["llm_reason"] = result.get("reason", "")
                categorized[category].append(item)

            if (i + 1) % 5 == 0:
                print(f"    Processed {i + 1}/{min(20, len(borderline_items))}")

            await asyncio.sleep(0.5)  # Rate limiting

    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}

    return categorized


def generate_markdown(categorized: dict[str, list[dict[str, Any]]]) -> str:
    """Generate markdown output."""
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Folo Digest - {date_str}",
        "",
        f"> Filtered for: {', '.join(USER_PROFILE['roles'])}",
        f"> Interests: {', '.join(USER_PROFILE['interests'])}",
        "",
        "---",
        "",
    ]

    # Summary stats
    total = sum(len(v) for v in categorized.values())
    lines.append(f"**Total relevant items: {total}**")
    lines.append("")

    # Table of contents
    lines.append("## Contents")
    for category, items in categorized.items():
        anchor = category.lower().replace(" ", "-").replace("&", "")
        lines.append(f"- [{category}](#{anchor}) ({len(items)})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Content by category
    for category, items in categorized.items():
        lines.append(f"## {category}")
        lines.append("")

        for item in items:
            # Title with link
            title = item["title"] or "Untitled"
            url = item.get("url", "#")
            lines.append(f"### [{title}]({url})")
            lines.append("")

            # Metadata
            meta = []
            if item.get("source"):
                meta.append(f"**Source**: {item['source']}")
            if item.get("author"):
                meta.append(f"**Author**: {item['author']}")
            if item.get("relevance"):
                meta.append(f"**Relevance**: {item['relevance']}")
            if meta:
                lines.append(" | ".join(meta))
                lines.append("")

            # Summary (prefer LLM summary, fallback to content preview)
            if item.get("llm_summary"):
                lines.append(f"> {item['llm_summary']}")
            elif item.get("content_text"):
                preview = item["content_text"][:300]
                if len(item["content_text"]) > 300:
                    preview += "..."
                lines.append(f"> {preview}")
            lines.append("")

            # Key details/quotes if available
            content = item.get("content_text", "")
            if len(content) > 300:
                # Extract a relevant quote (look for sentences with keywords)
                sentences = re.split(r'[.!?。！？]', content)
                for sent in sentences[:10]:
                    sent = sent.strip()
                    if len(sent) > 50 and any(kw in sent.lower() for kw in ["ai", "model", "效率", "tool"]):
                        lines.append(f"**Key point**: {sent}")
                        lines.append("")
                        break

            lines.append("---")
            lines.append("")

    # Footer
    lines.append(f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


async def main():
    """Main entry point."""
    # Check required env vars
    if not os.getenv("FOLO_COOKIE"):
        print("Error: FOLO_COOKIE not set in .env")
        return

    # Fetch content
    items = await fetch_list_content()

    if not items:
        print("No items fetched. Check your FOLO_COOKIE.")
        return

    # Filter and categorize
    categorized = await filter_and_categorize(items)

    # Generate output
    markdown = generate_markdown(categorized)

    # Save to file
    output_path = Path("folo_digest.md")
    output_path.write_text(markdown, encoding="utf-8")

    print(f"\nOutput saved to: {output_path.absolute()}")
    print(f"Total relevant items: {sum(len(v) for v in categorized.values())}")
    for cat, items in categorized.items():
        print(f"  - {cat}: {len(items)}")


if __name__ == "__main__":
    asyncio.run(main())
