#!/usr/bin/env python3
"""Test script to validate the refactoring."""

import sys


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from daily_ai_insight.collectors import (
            BaseCollector,
            FollowCollector,
            GitHubTrendingCollector,
            factory,
            create_twitter_collector,
            create_reddit_collector,
            create_papers_collector,
            create_mixed_collector,
            create_collector,
            create_from_preset,
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_factory_functions():
    """Test that factory functions create collectors correctly."""
    print("\nTesting factory functions...")

    try:
        from daily_ai_insight.collectors import (
            create_twitter_collector,
            create_reddit_collector,
            create_papers_collector,
            create_mixed_collector,
        )

        # Create collectors
        twitter = create_twitter_collector()
        reddit = create_reddit_collector()
        papers = create_papers_collector()
        mixed = create_mixed_collector()

        print(f"✅ Twitter collector: {twitter.name}")
        print(f"✅ Reddit collector: {reddit.name}")
        print(f"✅ Papers collector: {papers.name}")
        print(f"✅ Mixed collector: {mixed.name}")

        return True
    except Exception as e:
        print(f"❌ Factory function error: {e}")
        return False


def test_presets():
    """Test that preset configurations work."""
    print("\nTesting preset configurations...")

    try:
        from daily_ai_insight.collectors import create_from_preset
        from daily_ai_insight.collectors.factory import PRESET_CONFIGS

        print(f"Available presets: {list(PRESET_CONFIGS.keys())}")

        # Test a few presets
        twitter = create_from_preset("twitter")
        aibase = create_from_preset("aibase")
        xiaohu = create_from_preset("xiaohu")

        print(f"✅ Twitter preset: {twitter.name}")
        print(f"✅ AIBase preset: {aibase.name}")
        print(f"✅ Xiaohu preset: {xiaohu.name}")

        return True
    except Exception as e:
        print(f"❌ Preset error: {e}")
        return False


def test_deleted_classes():
    """Test that deleted classes are no longer importable."""
    print("\nTesting deleted classes...")

    deleted_classes = [
        "TwitterCollector",
        "RedditCollector",
        "PapersCollector",
        "AIBaseCollector",
        "JiqizhixinCollector",
        "QBitCollector",
        "XinZhiYuanCollector",
        "XiaohuCollector",
        "NewsAggregatorCollector",
    ]

    all_deleted = True
    for class_name in deleted_classes:
        try:
            exec(f"from daily_ai_insight.collectors import {class_name}")
            print(f"❌ {class_name} still importable (should be deleted)")
            all_deleted = False
        except ImportError:
            print(f"✅ {class_name} successfully deleted")

    return all_deleted


def test_custom_collector():
    """Test creating custom collector with create_collector."""
    print("\nTesting custom collector creation...")

    try:
        from daily_ai_insight.collectors import create_collector

        custom = create_collector(
            name="my_custom",
            list_id_env="CUSTOM_LIST_ID",
            source_name="Custom Source",
            item_type="custom"
        )

        print(f"✅ Custom collector: {custom.name}")
        return True
    except Exception as e:
        print(f"❌ Custom collector error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Refactoring Validation Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_factory_functions,
        test_presets,
        test_deleted_classes,
        test_custom_collector,
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All tests passed! Refactoring successful.")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
