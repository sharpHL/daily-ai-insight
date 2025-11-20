"""Google Gemini API provider."""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Google Gemini API provider for content analysis."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")

        genai.configure(api_key=self.api_key)

        # Initialize model with optimal settings
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # Using Flash for cost efficiency
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            )
        )

    async def analyze(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Analyze content using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            max_retries: Maximum number of retry attempts

        Returns:
            Analysis result dictionary
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)

                # Extract JSON from response
                text = response.text

                # Try to extract JSON from markdown code blocks
                if "```json" in text:
                    json_start = text.find("```json") + 7
                    json_end = text.find("```", json_start)
                    text = text[json_start:json_end].strip()
                elif "```" in text:
                    json_start = text.find("```") + 3
                    json_end = text.find("```", json_start)
                    text = text[json_start:json_end].strip()

                # Parse JSON response
                try:
                    result = json.loads(text)
                    logger.debug(f"Successfully parsed Gemini response")
                    return result
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    logger.debug(f"Response is not JSON, returning as text")
                    return {"text": text}

            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All Gemini API attempts failed")
                    raise

        return {}

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generate text using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            max_tokens: Maximum output tokens

        Returns:
            Generated text
        """
        try:
            # Update generation config for this call
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=max_tokens,
                )
            )

            return response.text

        except Exception as e:
            logger.error(f"Gemini text generation failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        try:
            return self.model.count_tokens(text).total_tokens
        except:
            # Rough estimate if counting fails
            return len(text) // 4