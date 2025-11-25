#!/usr/bin/env python3
"""Check which List/Feed IDs are configured in .env"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Check all collector IDs
configs = {
    "Papers": {
        "PAPERS_LIST_ID": os.getenv("PAPERS_LIST_ID"),
    },
    "Twitter": {
        "TWITTER_LIST_ID": os.getenv("TWITTER_LIST_ID"),
    },
    "AI Base": {
        "AIBASE_FEED_ID": os.getenv("AIBASE_FEED_ID"),
    },
    "机器之心": {
        "JIQIZHIXIN_FEED_ID": os.getenv("JIQIZHIXIN_FEED_ID"),
    },
    "量子位": {
        "QBIT_FEED_ID": os.getenv("QBIT_FEED_ID"),
    },
    "新智元": {
        "XINZHIYUAN_FEED_ID": os.getenv("XINZHIYUAN_FEED_ID"),
    },
    "Reddit": {
        "REDDIT_LIST_ID": os.getenv("REDDIT_LIST_ID"),
    },
    "Xiaohu AI": {
        "XIAOHU_FEED_ID": os.getenv("XIAOHU_FEED_ID"),
        "XIAOHU_LIST_ID": os.getenv("XIAOHU_LIST_ID"),
    },
    "News Aggregator": {
        "NEWS_AGGREGATOR_LIST_ID": os.getenv("NEWS_AGGREGATOR_LIST_ID"),
    },
}

print("=" * 70)
print("📋 Environment Configuration Check")
print("=" * 70)
print()

configured = []
placeholder = []
missing = []

for collector, env_vars in configs.items():
    print(f"🔍 {collector}")
    for var_name, var_value in env_vars.items():
        if var_value:
            # Check if it's a placeholder
            if var_value.startswith("your_"):
                status = "⚠️  Placeholder"
                placeholder.append((collector, var_name, var_value))
            else:
                # Show first 20 chars + ...
                display_value = var_value[:20] + "..." if len(var_value) > 20 else var_value
                status = f"✅ Configured: {display_value}"
                configured.append((collector, var_name))
        else:
            status = "❌ Not set"
            missing.append((collector, var_name))

        print(f"   {var_name}: {status}")
    print()

# Summary
print("=" * 70)
print("📊 Summary")
print("=" * 70)
print(f"✅ Properly configured: {len(configured)}")
print(f"⚠️  Placeholder values: {len(placeholder)}")
print(f"❌ Not set: {len(missing)}")
print()

if configured:
    print("✅ Properly configured collectors:")
    for collector, var in configured:
        print(f"   - {collector} ({var})")
    print()

if placeholder:
    print("⚠️  Collectors with placeholder values (need real IDs):")
    for collector, var, value in placeholder:
        print(f"   - {collector} ({var} = '{value}')")
    print()

if missing:
    print("❌ Missing configuration:")
    for collector, var in missing:
        print(f"   - {collector} ({var})")
    print()

print("=" * 70)
print("💡 Tip: Real IDs should be numeric strings (e.g., '153028784690326528')")
print("=" * 70)
