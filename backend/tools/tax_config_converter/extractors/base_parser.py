"""
Base LLM Parser Interface

Abstract base class for LLM-based tax table parsing.
Supports multiple providers: GLM, Gemini, etc.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseLLMParser(ABC):
    """
    Abstract base class for LLM parsers.

    Implementations must provide:
    - parse(): Send prompt and get raw text response
    - is_available(): Check if the API is available
    """

    @abstractmethod
    def parse(self, prompt: str) -> str:
        """
        Send prompt to LLM API and get response.

        Args:
            prompt: The extraction prompt with table text and instructions

        Returns:
            Raw response content from LLM

        Raises:
            ValueError: If API call fails or returns invalid response
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM API is available (API key set, package installed)."""
        pass

    def parse_json(self, prompt: str) -> dict[str, Any]:
        """
        Parse prompt and extract JSON from response.

        Args:
            prompt: The extraction prompt

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If response doesn't contain valid JSON
        """
        response = self.parse(prompt)

        # Try to extract JSON from response
        json_str = self._extract_json(response)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            raise ValueError(f"Invalid JSON in response: {e}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from response text.

        Handles various formats:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON with surrounding text
        """
        # Try markdown code block first
        json_block = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if json_block:
            return json_block.group(1).strip()

        # Try to find JSON object directly
        first_brace = text.find("{")
        last_brace = text.rfind("}")

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]

        # Maybe it's a JSON array
        first_bracket = text.find("[")
        last_bracket = text.rfind("]")

        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            return text[first_bracket:last_bracket + 1]

        # Return as-is and let JSON parser handle it
        return text.strip()
