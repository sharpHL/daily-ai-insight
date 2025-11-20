"""OpenAI API provider (backup)."""

import os
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI API provider for content analysis (backup)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"  # Using 3.5-turbo for cost efficiency

    async def analyze(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Analyze content using OpenAI.

        Args:
            prompt: The prompt to send to OpenAI
            max_retries: Maximum number of retry attempts

        Returns:
            Analysis result dictionary
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional AI analyst. Always respond in JSON format when requested."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2048,
                    response_format={"type": "json_object"}  # Force JSON response
                )

                text = response.choices[0].message.content

                # Parse JSON response
                try:
                    result = json.loads(text)
                    logger.debug(f"Successfully parsed OpenAI response")
                    return result
                except json.JSONDecodeError:
                    logger.debug(f"Response is not JSON, returning as text")
                    return {"text": text}

            except Exception as e:
                logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All OpenAI API attempts failed")
                    raise

        return {}

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generate text using OpenAI.

        Args:
            prompt: The prompt to send to OpenAI
            max_tokens: Maximum output tokens

        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (rough estimate).

        Args:
            text: Text to count tokens for

        Returns:
            Token count estimate
        """
        # Rough estimate for GPT-3.5
        return len(text) // 4