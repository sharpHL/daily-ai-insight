#!/usr/bin/env python3
"""Test script to send a message to Feishu webhook."""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from daily_ai_insight.renderers.feishu import FeishuRenderer


async def test_simple_message():
    """Test sending a simple text message."""
    print("🧪 Testing Feishu Simple Message\n")

    # Load environment variables
    load_dotenv()

    webhook = os.getenv("FEISHU_WEBHOOK")
    secret = os.getenv("FEISHU_SECRET")

    if not webhook:
        print("❌ Error: FEISHU_WEBHOOK not set in .env file")
        return False

    print(f"📍 Webhook: {webhook[:50]}...")
    print(f"🔐 Secret: {'✅ Configured' if secret else '❌ Not configured'}\n")

    # Initialize renderer
    try:
        renderer = FeishuRenderer(webhook_url=webhook, secret=secret)
        print("✅ FeishuRenderer initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize renderer: {e}")
        return False

    # Send test message
    print("📤 Sending test message...\n")

    message = """🤖 Feishu Webhook Test

✅ This is a test message from daily-ai-insight
🕐 Timestamp: {timestamp}
🔐 Signature: {signature}

If you see this message, the webhook is working correctly!
""".format(
        timestamp="enabled" if secret else "disabled",
        signature="enabled" if secret else "disabled"
    )

    try:
        success = await renderer.send_simple_message(message)

        if success:
            print("✅ Message sent successfully!")
            return True
        else:
            print("❌ Failed to send message (check webhook URL and permissions)")
            return False

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_card_message():
    """Test sending a rich card message."""
    print("\n" + "="*60)
    print("🧪 Testing Feishu Card Message\n")

    # Load environment variables
    load_dotenv()

    webhook = os.getenv("FEISHU_WEBHOOK")
    secret = os.getenv("FEISHU_SECRET")

    if not webhook:
        print("❌ Error: FEISHU_WEBHOOK not set in .env file")
        return False

    # Initialize renderer
    renderer = FeishuRenderer(webhook_url=webhook, secret=secret)

    # Create test report data
    report_data = {
        "executive_summary": "This is a test report from daily-ai-insight to verify card messages are working correctly.",
        "key_points": [
            {
                "title": "Test Point 1: High Priority",
                "description": "This is a high priority test item to verify card rendering.",
                "importance": "high"
            },
            {
                "title": "Test Point 2: Medium Priority",
                "description": "This is a medium priority test item.",
                "importance": "medium"
            },
            {
                "title": "Test Point 3: Low Priority",
                "description": "This is a low priority test item.",
                "importance": "low"
            }
        ],
        "trend_analysis": {
            "current_trends": [
                "Webhook integration working",
                "Signature verification active" if secret else "Signature verification not configured"
            ],
            "emerging_topics": [
                "Daily AI insights automation"
            ]
        },
        "recommendations": [
            {
                "action": "Verify all messages are received correctly",
                "reason": "Testing phase",
                "priority": "high"
            },
            {
                "action": "Check signature verification if enabled",
                "reason": "Security testing",
                "priority": "medium"
            }
        ],
        "notable_sources": [
            {
                "title": "Daily AI Insight Project",
                "url": "https://github.com/yourusername/daily-ai-insight",
                "reason": "Main project repository"
            }
        ]
    }

    print("📤 Sending card message...\n")

    try:
        success = await renderer.send(report_data)

        if success:
            print("✅ Card message sent successfully!")
            return True
        else:
            print("❌ Failed to send card message")
            return False

    except Exception as e:
        print(f"❌ Error sending card message: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("🚀 Feishu Webhook Test Suite")
    print("="*60 + "\n")

    # Test 1: Simple message
    result1 = await test_simple_message()

    # Test 2: Card message
    result2 = await test_card_message()

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Simple Message: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Card Message:   {'✅ PASS' if result2 else '❌ FAIL'}")
    print()

    if result1 and result2:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
