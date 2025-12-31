"""
Google Gemini API Parser for Tax Table Extraction

Uses Google Generative AI API (Gemini) for fast tax table parsing.
Much faster than GLM (~10-20s per province vs ~100s).
"""

import os
import logging
from pathlib import Path

from .base_parser import BaseLLMParser

logger = logging.getLogger(__name__)


def _load_env() -> None:
    """Load environment variables from .env file if present."""
    current = Path(__file__).parent
    for _ in range(5):
        env_file = current / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                return
            except ImportError:
                _load_env_manual(env_file)
                return
        current = current.parent


def _load_env_manual(env_file: Path) -> None:
    """Manually parse .env file without python-dotenv."""
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        logger.warning(f"Failed to load .env: {e}")


class GeminiParser(BaseLLMParser):
    """
    Google Gemini API client for parsing tax tables.

    Uses the google-generativeai SDK to call Gemini models.
    Requires GEMINI_API_KEY environment variable.
    Optionally reads GEMINI_MODEL from environment.

    Usage:
        parser = GeminiParser()
        result = parser.parse_json(prompt)
    """

    # Default model if not specified in env or args
    DEFAULT_MODEL = "gemini-2.5-flashgua"

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 16384
    ):
        """
        Initialize Gemini Parser.

        Args:
            model: Gemini model to use (reads from GEMINI_MODEL env if not specified)
            temperature: Lower = more deterministic (default: 0.1)
            max_tokens: Maximum output tokens
        """
        # Load env first to get GEMINI_MODEL if needed
        if not os.environ.get("GEMINI_API_KEY"):
            _load_env()

        # Priority: arg > env > default
        self.model_name = model or os.environ.get("GEMINI_MODEL") or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model = None

    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            if not os.environ.get("GEMINI_API_KEY"):
                _load_env()

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY environment variable is required. "
                    "Get your API key from https://aistudio.google.com/apikey"
                )

            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(
                    self.model_name,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens,
                    }
                )
                logger.info(f"Gemini model initialized: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required. Install with: "
                    "uv add --optional tools google-generativeai"
                )

        return self._model

    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return False

        try:
            import google.generativeai  # noqa: F401
            return True
        except ImportError:
            return False

    def parse(self, prompt: str) -> str:
        """
        Send prompt to Gemini API and get response.

        Args:
            prompt: The extraction prompt with table text and instructions

        Returns:
            Raw response content from Gemini

        Raises:
            ValueError: If API call fails or returns invalid response
        """
        if len(prompt) < 100:
            raise ValueError(f"Prompt too short: {len(prompt)} chars")

        model = self._get_model()

        logger.info(
            f"Gemini API request: model={self.model_name}, "
            f"prompt_length={len(prompt)} chars"
        )

        try:
            response = model.generate_content(prompt)

            if not response.text:
                raise ValueError("Gemini API returned empty content")

            content = response.text.strip()

            logger.info(f"Gemini API response: {len(content)} chars")

            return content

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise ValueError(f"Gemini API call failed: {e}")
