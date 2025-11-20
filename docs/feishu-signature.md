# Feishu Webhook Signature Verification

This document explains how to configure and use signature verification for Feishu (Lark) webhooks to enhance security.

## Overview

Feishu webhook signature verification adds an extra layer of security by ensuring that webhook requests are authentic. When enabled, each request includes:
- **timestamp**: Current Unix timestamp (in seconds)
- **sign**: HMAC-SHA256 signature of `{timestamp}\n{secret}`

## How It Works

### Signature Generation Algorithm

1. Get current Unix timestamp (seconds): `timestamp = int(time.time())`
2. Construct signing string: `string_to_sign = f"{timestamp}\n{secret}"`
3. Generate HMAC-SHA256 hash: `hmac.new(string_to_sign.encode(), digestmod=hashlib.sha256)`
4. Encode to Base64: `base64.b64encode(hmac_code).decode()`

### Example

```python
import time
import hmac
import hashlib
import base64

# Configuration
timestamp = 1234567890
secret = "your_secret_key"

# Generate signature
string_to_sign = f"{timestamp}\n{secret}"
hmac_code = hmac.new(
    string_to_sign.encode("utf-8"),
    digestmod=hashlib.sha256
).digest()
sign = base64.b64encode(hmac_code).decode("utf-8")

# Result
print(f"Timestamp: {timestamp}")
print(f"Signature: {sign}")
```

## Configuration

### Step 1: Enable Signature Verification in Feishu

1. Go to your Feishu group/channel
2. Click on **Settings** → **Bots & Webhooks**
3. Create or edit a custom bot
4. In security settings, enable **Signature Verification** (签名校验)
5. Copy the generated **Secret Key**

### Step 2: Configure Environment Variables

Add the secret key to your `.env` file:

```bash
# Feishu Configuration
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id
FEISHU_SECRET=your_secret_key_here
```

### Step 3: Update Code (if needed)

The `FeishuRenderer` class automatically detects and uses the secret if configured:

```python
from daily_ai_insight.renderers import FeishuRenderer

# Option 1: Use environment variables (recommended)
renderer = FeishuRenderer()

# Option 2: Pass explicitly
renderer = FeishuRenderer(
    webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/...",
    secret="your_secret_key"
)
```

## Request Payload Structure

### Without Signature

```json
{
  "msg_type": "text",
  "content": {
    "text": "Hello, Feishu!"
  }
}
```

### With Signature

```json
{
  "msg_type": "text",
  "content": {
    "text": "Hello, Feishu!"
  },
  "timestamp": "1234567890",
  "sign": "WcyIyZehVouph5pqXmfqnjQQqlE/RFnm707DFOXhOC4="
}
```

## Testing

### Manual Test

Run the test script to verify signature generation:

```bash
python3 scripts/test_signature.py
```

Expected output:
```
🔐 Testing Feishu Signature Generation

Test 1: Basic signature generation
  ✅ Generated successfully

Test 2: Current timestamp
  ✅ Generated successfully

...

✅ All tests passed!
```

### Unit Tests

Run the unit tests:

```bash
make test
# or
pytest tests/unit/test_feishu_signature.py -v
```

## Troubleshooting

### Issue: "signature verification failed" error from Feishu

**Possible causes:**
1. **Incorrect secret**: Verify the secret matches what's configured in Feishu
2. **Time sync issue**: Ensure your server time is synchronized (NTP)
3. **Timestamp format**: Should be Unix timestamp in seconds (10 digits), not milliseconds

**Solution:**
```bash
# Check system time
date +%s

# Verify secret in .env
echo $FEISHU_SECRET

# Enable debug logging
export DEBUG=true
python -m daily_ai_insight
```

### Issue: Signature works locally but fails in CI/CD

**Possible cause:** Time synchronization issue in containerized environments

**Solution:**
```yaml
# In GitHub Actions
- name: Sync time
  run: sudo ntpdate -s time.nist.gov || true
```

## Security Best Practices

1. **Never commit secrets**: Keep `.env` in `.gitignore`
2. **Rotate secrets regularly**: Update secret key periodically
3. **Use environment variables**: Don't hardcode secrets in code
4. **Validate timestamps**: Feishu may reject signatures with timestamps too far in the past/future (typically ±5 minutes)
5. **Use HTTPS**: Always use HTTPS webhook URLs

## References

- [Feishu Custom Bot Documentation](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
- [HMAC-SHA256 Algorithm](https://en.wikipedia.org/wiki/HMAC)
- [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104)

## Example Integration

Complete example using signature verification:

```python
import asyncio
from daily_ai_insight.renderers import FeishuRenderer

async def send_daily_report():
    """Send daily report with signature verification."""
    renderer = FeishuRenderer()  # Reads from env vars

    report_data = {
        "executive_summary": "Today's AI insights...",
        "key_points": [
            {
                "title": "GPT-5 Announced",
                "description": "OpenAI announces next generation model",
                "importance": "high"
            }
        ]
    }

    success = await renderer.send(report_data)
    print(f"Report sent: {success}")

# Run
asyncio.run(send_daily_report())
```

## Changelog

- **2025-01-20**: Added signature verification support
  - Added `FEISHU_SECRET` environment variable
  - Implemented HMAC-SHA256 signature generation
  - Updated both `send()` and `send_simple_message()` methods
  - Added unit tests and documentation
