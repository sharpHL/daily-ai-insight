#!/usr/bin/env python3
"""Examples of using FollowCollector with callbacks instead of subclasses.

This demonstrates the new callback-based design which is more flexible
and eliminates the need to create subclasses for each data source.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from daily_ai_insight.collectors import FollowCollector
from daily_ai_insight.collectors.transformers import (
    twitter_transform,
    weibo_transform,
    reddit_transform,
    auto_detect_transform,
    get_transformer,
)


# ============================================================================
# Example 1: Basic Usage with Pre-built Transformers
# ============================================================================

async def example_1_prebuilt_transformers():
    """Use pre-built transformers from the transformers module."""
    print("=" * 70)
    print("Example 1: Pre-built Transformers")
    print("=" * 70)
    print()

    # Twitter collector with twitter_transform callback
    twitter = FollowCollector(
        name="twitter",
        list_id_env="TWITTER_LIST_ID",
        source_name="Twitter",
        item_type="tweet",
        transform_callback=twitter_transform  # ← Callback instead of subclass!
    )

    print("✅ Created Twitter collector with callback")
    print(f"   No subclass needed!")
    print()

    data = await twitter.fetch()
    items = data.get("items", [])
    print(f"📊 Fetched {len(items)} items")

    if items:
        sample = items[0]
        metadata = sample.get("_metadata", {})
        print(f"\n📄 Sample item metadata:")
        print(f"   platform: {metadata.get('platform')}")
        print(f"   is_retweet: {metadata.get('is_retweet')}")
        print(f"   hashtags: {metadata.get('hashtags', [])}")
        print(f"   mentions: {metadata.get('mentions', [])}")


# ============================================================================
# Example 2: Auto-Detection for Mixed Sources
# ============================================================================

async def example_2_auto_detection():
    """Use auto_detect_transform for mixed-source lists."""
    print("\n" + "=" * 70)
    print("Example 2: Auto-Detection (Mixed Sources)")
    print("=" * 70)
    print()

    # One collector handles all sources automatically!
    mixed = FollowCollector(
        name="ai_mixed",
        list_id_env="AI_MIXED_LIST_ID",
        source_name="AI Mixed",
        transform_callback=auto_detect_transform  # ← Auto-detects platform!
    )

    print("✅ Created mixed collector with auto-detection")
    print(f"   Automatically handles: Twitter, Weibo, Reddit, GitHub")
    print()

    data = await mixed.fetch()
    items = data.get("items", [])
    print(f"📊 Fetched {len(items)} items")

    # Count platforms
    platforms = {}
    for item in items:
        platform = item.get("_metadata", {}).get("platform", "other")
        platforms[platform] = platforms.get(platform, 0) + 1

    print(f"\n📈 Platform distribution:")
    for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform:15s} {count:3d} items")


# ============================================================================
# Example 3: Custom Transform Function
# ============================================================================

def my_custom_transform(entries, feeds, source_name, item_type, custom_source_format):
    """Custom transformer with specific business logic."""
    from daily_ai_insight.collectors.transformers import extract_common_fields

    # Start with common fields
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)

    # Add custom processing
    content = item["content_text"]
    metadata = item["_metadata"]

    # Custom: Extract AI model mentions
    ai_models = []
    for model in ["GPT", "Claude", "Gemini", "Llama", "Mistral"]:
        if model.lower() in content.lower():
            ai_models.append(model)

    if ai_models:
        metadata["mentioned_ai_models"] = ai_models

    # Custom: Detect news vs opinion
    if any(word in content.lower() for word in ["breaking", "announced", "released"]):
        metadata["content_type"] = "news"
    elif any(word in content.lower() for word in ["think", "believe", "opinion"]):
        metadata["content_type"] = "opinion"
    else:
        metadata["content_type"] = "general"

    return item


async def example_3_custom_transform():
    """Use a custom transform function."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Transform Function")
    print("=" * 70)
    print()

    collector = FollowCollector(
        name="ai_news",
        list_id_env="TWITTER_LIST_ID",
        source_name="AI News",
        transform_callback=my_custom_transform  # ← Your custom logic!
    )

    print("✅ Created collector with custom transform")
    print(f"   Extracts: AI model mentions, content type")
    print()

    data = await collector.fetch()
    items = data.get("items", [])[:3]  # First 3

    for i, item in enumerate(items, 1):
        metadata = item["_metadata"]
        print(f"\n📄 Item {i}:")
        print(f"   Title: {item['title'][:60]}...")
        if metadata.get("mentioned_ai_models"):
            print(f"   AI Models: {', '.join(metadata['mentioned_ai_models'])}")
        print(f"   Type: {metadata.get('content_type', 'N/A')}")


# ============================================================================
# Example 4: Get Transformer by Name
# ============================================================================

async def example_4_transformer_registry():
    """Use the transformer registry for dynamic selection."""
    print("\n" + "=" * 70)
    print("Example 4: Transformer Registry")
    print("=" * 70)
    print()

    # User selects platform at runtime
    platform = "twitter"  # Could be from config, user input, etc.

    transformer = get_transformer(platform)

    collector = FollowCollector(
        name=f"{platform}_dynamic",
        list_id_env="TWITTER_LIST_ID",
        transform_callback=transformer  # ← Dynamically selected!
    )

    print(f"✅ Dynamically selected '{platform}' transformer")
    print()

    data = await collector.fetch()
    print(f"📊 Fetched {len(data.get('items', []))} items")


# ============================================================================
# Example 5: Lambda for Quick Customization
# ============================================================================

async def example_5_lambda_transform():
    """Use lambda for simple inline transforms."""
    print("\n" + "=" * 70)
    print("Example 5: Lambda/Inline Transform")
    print("=" * 70)
    print()

    from daily_ai_insight.collectors.transformers import extract_common_fields

    # Quick inline transform using lambda
    collector = FollowCollector(
        name="simple",
        list_id_env="TWITTER_LIST_ID",
        transform_callback=lambda entries, feeds, **kwargs: {
            **extract_common_fields(entries, feeds, **kwargs),
            "_metadata": {
                **extract_common_fields(entries, feeds, **kwargs)["_metadata"],
                "processed_by": "lambda_transform",
                "custom_flag": True
            }
        }
    )

    print("✅ Created collector with lambda transform")
    print(f"   Perfect for quick customizations!")
    print()

    data = await collector.fetch()
    if data.get("items"):
        sample = data["items"][0]
        print(f"📄 Sample metadata:")
        print(f"   processed_by: {sample['_metadata'].get('processed_by')}")
        print(f"   custom_flag: {sample['_metadata'].get('custom_flag')}")


# ============================================================================
# Example 6: Comparison - Subclass vs Callback
# ============================================================================

async def example_6_comparison():
    """Compare the old subclass way vs new callback way."""
    print("\n" + "=" * 70)
    print("Example 6: Subclass vs Callback Comparison")
    print("=" * 70)
    print()

    print("OLD WAY (Subclass):")
    print("-" * 70)
    print("""
    class TwitterCollector(FollowCollector):
        def __init__(self):
            def format_twitter_source(author, feeds):
                # Custom logic
                ...

            super().__init__(
                name="twitter",
                list_id_env="TWITTER_LIST_ID",
                custom_source_format=format_twitter_source
            )

        def _transform_entry(self, entries, feeds):
            # Override method
            # Custom transform logic
            ...
    """)

    print("\nNEW WAY (Callback):")
    print("-" * 70)
    print("""
    from daily_ai_insight.collectors.transformers import twitter_transform

    collector = FollowCollector(
        name="twitter",
        list_id_env="TWITTER_LIST_ID",
        transform_callback=twitter_transform  # Done!
    )

    # Or with custom transform:
    def my_transform(entries, feeds, **kwargs):
        # Custom logic here
        ...

    collector = FollowCollector(
        name="custom",
        list_id_env="MY_LIST_ID",
        transform_callback=my_transform
    )
    """)

    print("\nBenefits of Callback Approach:")
    print("  ✅ No subclass needed")
    print("  ✅ More flexible (swap transforms at runtime)")
    print("  ✅ Easier to test (pure functions)")
    print("  ✅ Better composition")
    print("  ✅ Less boilerplate code")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("🎯 FollowCollector Callback Pattern Examples")
    print("=" * 70)
    print()
    print("Demonstrating the new callback-based design that eliminates")
    print("the need for creating subclasses for each data source.")
    print()

    # Check configuration
    if not os.getenv("TWITTER_LIST_ID") or os.getenv("TWITTER_LIST_ID").startswith("your_"):
        print("⚠️  Please configure TWITTER_LIST_ID in .env to run examples")
        return

    try:
        # Run examples
        await example_1_prebuilt_transformers()
        await example_2_auto_detection()
        await example_3_custom_transform()
        await example_4_transformer_registry()
        await example_5_lambda_transform()
        await example_6_comparison()

        print("\n" + "=" * 70)
        print("✅ All examples completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
