"""Tests for Feishu signature generation."""

import os
import time
import hmac
import hashlib
import base64
import pytest
from unittest.mock import patch
from daily_ai_insight.renderers.feishu import FeishuRenderer


class TestFeishuSignature:
    """Test Feishu webhook signature generation."""

    @patch.dict(os.environ, {}, clear=True)
    def test_generate_sign(self):
        """Test signature generation."""
        # Setup
        secret = "test_secret_key"
        renderer = FeishuRenderer(
            webhook_url="https://example.com/webhook",
            secret=secret
        )

        # Generate signature
        timestamp = 1234567890
        sign = renderer._generate_sign(timestamp)

        # Verify signature is base64 encoded
        assert sign is not None
        assert len(sign) > 0

        # Verify we can decode it
        try:
            base64.b64decode(sign)
        except Exception:
            pytest.fail("Signature is not valid base64")

    @patch.dict(os.environ, {}, clear=True)
    def test_signature_deterministic(self):
        """Test that same timestamp and secret produce same signature."""
        secret = "test_secret_key"
        renderer = FeishuRenderer(
            webhook_url="https://example.com/webhook",
            secret=secret
        )

        timestamp = 1234567890
        sign1 = renderer._generate_sign(timestamp)
        sign2 = renderer._generate_sign(timestamp)

        assert sign1 == sign2

    @patch.dict(os.environ, {}, clear=True)
    def test_signature_different_for_different_timestamps(self):
        """Test that different timestamps produce different signatures."""
        secret = "test_secret_key"
        renderer = FeishuRenderer(
            webhook_url="https://example.com/webhook",
            secret=secret
        )

        timestamp1 = 1234567890
        timestamp2 = 1234567891

        sign1 = renderer._generate_sign(timestamp1)
        sign2 = renderer._generate_sign(timestamp2)

        assert sign1 != sign2

    @patch.dict(os.environ, {}, clear=True)
    def test_signature_matches_expected_algorithm(self):
        """Test that signature matches HMAC-SHA256 algorithm."""
        secret = "test_secret"
        timestamp = 1234567890

        renderer = FeishuRenderer(
            webhook_url="https://example.com/webhook",
            secret=secret
        )

        # Generate using our method
        our_sign = renderer._generate_sign(timestamp)

        # Generate using direct HMAC-SHA256
        string_to_sign = f"{timestamp}\n{secret}"
        expected_sign = base64.b64encode(
            hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
        ).decode("utf-8")

        assert our_sign == expected_sign

    @patch.dict(os.environ, {}, clear=True)
    def test_no_signature_without_secret(self):
        """Test that signature is not generated without secret."""
        # Explicitly clear environment variables
        with patch.dict(os.environ, {"FEISHU_WEBHOOK": "https://example.com/webhook"}, clear=True):
            renderer = FeishuRenderer(webhook_url="https://example.com/webhook")
            assert renderer.secret is None

    def test_signature_enabled_log(self, caplog):
        """Test that signature enabled message is logged."""
        import logging

        # Set log level to INFO to capture the message
        caplog.set_level(logging.INFO)

        # Clear environment to avoid interference
        with patch.dict(os.environ, {}, clear=True):
            renderer = FeishuRenderer(
                webhook_url="https://example.com/webhook",
                secret="test_secret"
            )

            assert renderer.secret == "test_secret"
            assert "Feishu signature verification enabled" in caplog.text
