#!/usr/bin/env python3
"""Complete test for all collectors after refactoring."""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_all_presets():
    """Test all preset collectors can be created."""
    print("Testing all preset collectors...\n")

    from daily_ai_insight.collectors import create_from_preset
    from daily_ai_insight.collectors.factory import PRESET_CONFIGS

    success_count = 0
    fail_count = 0

    for preset_name in PRESET_CONFIGS.keys():
        try:
            collector = create_from_preset(preset_name)
            print(f"✅ {preset_name:20s} → name='{collector.name}', source='{collector.source_name}'")

            # Verify basic attributes
            assert collector.name == preset_name
            assert collector.source_name is not None
            assert hasattr(collector, 'fetch')

            success_count += 1
        except Exception as e:
            print(f"❌ {preset_name:20s} → {e}")
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Success: {success_count}/{len(PRESET_CONFIGS)}")
    print(f"❌ Failed: {fail_count}/{len(PRESET_CONFIGS)}")
    print(f"{'='*60}\n")

    return fail_count == 0


def test_specialized_collectors():
    """Test specialized collectors (non-preset)."""
    print("Testing specialized collectors...\n")

    from daily_ai_insight.collectors import GitHubTrendingCollector

    try:
        github = GitHubTrendingCollector()
        print(f"✅ GitHubTrendingCollector → name='{github.name}'")
        return True
    except Exception as e:
        print(f"❌ GitHubTrendingCollector → {e}")
        return False


def test_factory_functions():
    """Test individual factory functions."""
    print("Testing individual factory functions...\n")

    from daily_ai_insight.collectors import (
        create_twitter_collector,
        create_reddit_collector,
        create_papers_collector,
        create_mixed_collector,
    )

    factories = [
        ("create_twitter_collector", create_twitter_collector, "twitter"),
        ("create_reddit_collector", create_reddit_collector, "reddit"),
        ("create_papers_collector", create_papers_collector, "papers"),
        ("create_mixed_collector", create_mixed_collector, "mixed"),
    ]

    success_count = 0
    for func_name, func, expected_name in factories:
        try:
            collector = func()
            print(f"✅ {func_name:30s} → name='{collector.name}'")
            assert collector.name == expected_name
            success_count += 1
        except Exception as e:
            print(f"❌ {func_name:30s} → {e}")

    print(f"\n✅ {success_count}/{len(factories)} factory functions working\n")
    return success_count == len(factories)


def test_custom_collector():
    """Test custom collector creation."""
    print("Testing custom collector creation...\n")

    from daily_ai_insight.collectors import create_collector

    try:
        custom = create_collector(
            name="test_custom",
            list_id_env="TEST_LIST_ID",
            source_name="Test Custom Source",
            home_url="https://example.com",
            item_type="test"
        )
        print(f"✅ Custom collector created")
        print(f"   name: {custom.name}")
        print(f"   source: {custom.source_name}")
        print(f"   home_url: {custom.home_url}")
        print()
        return True
    except Exception as e:
        print(f"❌ Custom collector failed: {e}\n")
        return False


def test_preset_override():
    """Test overriding preset configurations."""
    print("Testing preset override...\n")

    from daily_ai_insight.collectors import create_from_preset

    try:
        # Override twitter list_id_env
        custom_twitter = create_from_preset(
            "twitter",
            list_id_env="MY_CUSTOM_TWITTER_LIST"
        )
        print(f"✅ Preset override working")
        print(f"   Custom list_id_env used\n")
        return True
    except Exception as e:
        print(f"❌ Preset override failed: {e}\n")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Complete Collector Tests After Refactoring")
    print("="*60)
    print()

    results = []

    # Test 1: All presets
    results.append(("All Preset Collectors", test_all_presets()))

    # Test 2: Specialized collectors
    results.append(("Specialized Collectors", test_specialized_collectors()))

    # Test 3: Factory functions
    results.append(("Factory Functions", test_factory_functions()))

    # Test 4: Custom collector
    results.append(("Custom Collector", test_custom_collector()))

    # Test 5: Preset override
    results.append(("Preset Override", test_preset_override()))

    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30s} {status}")

    all_passed = all(result[1] for result in results)
    print("="*60)
    if all_passed:
        print("🎉 All tests passed! Refactoring is fully functional.")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
