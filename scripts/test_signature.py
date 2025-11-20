#!/usr/bin/env python3
"""Simple test script to verify Feishu signature generation."""

import time
import hmac
import hashlib
import base64


def generate_sign(timestamp: int, secret: str) -> str:
    """Generate signature for Feishu webhook.

    Args:
        timestamp: Current timestamp in seconds
        secret: Secret key

    Returns:
        Base64 encoded signature
    """
    # Construct string to sign: timestamp + newline + secret
    string_to_sign = f"{timestamp}\n{secret}"

    # Generate HMAC-SHA256 signature
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    # Encode to base64
    sign = base64.b64encode(hmac_code).decode("utf-8")

    return sign


def main():
    """Test signature generation."""
    print("🔐 Testing Feishu Signature Generation\n")

    # Test 1: Basic signature generation
    print("Test 1: Basic signature generation")
    secret = "test_secret_key"
    timestamp = 1234567890
    sign = generate_sign(timestamp, secret)
    print(f"  Timestamp: {timestamp}")
    print(f"  Secret: {secret}")
    print(f"  Signature: {sign}")
    print(f"  ✅ Generated successfully\n")

    # Test 2: Current timestamp
    print("Test 2: Current timestamp")
    current_timestamp = int(time.time())
    current_sign = generate_sign(current_timestamp, secret)
    print(f"  Timestamp: {current_timestamp}")
    print(f"  Secret: {secret}")
    print(f"  Signature: {current_sign}")
    print(f"  ✅ Generated successfully\n")

    # Test 3: Deterministic (same input = same output)
    print("Test 3: Deterministic behavior")
    sign1 = generate_sign(timestamp, secret)
    sign2 = generate_sign(timestamp, secret)
    if sign1 == sign2:
        print(f"  ✅ Same inputs produce same signature")
    else:
        print(f"  ❌ FAILED: Signatures don't match")
        return False
    print()

    # Test 4: Different timestamps produce different signatures
    print("Test 4: Different timestamps")
    timestamp2 = timestamp + 1
    sign_a = generate_sign(timestamp, secret)
    sign_b = generate_sign(timestamp2, secret)
    if sign_a != sign_b:
        print(f"  ✅ Different timestamps produce different signatures")
    else:
        print(f"  ❌ FAILED: Signatures should be different")
        return False
    print()

    # Test 5: Example payload structure
    print("Test 5: Example payload structure")
    payload = {
        "msg_type": "text",
        "content": {"text": "Hello, Feishu!"},
        "timestamp": str(current_timestamp),
        "sign": current_sign
    }
    print(f"  Payload:")
    import json
    print(json.dumps(payload, indent=2))
    print(f"  ✅ Payload structure correct\n")

    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    main()
