"""
GLM API Parser for Tax Table Extraction

Uses ZhipuAI GLM API to parse tax tables from PDF text.
Based on BeanFlow-CRA implementation pattern.
"""

import logging
import os
from pathlib import Path

from .base_parser import BaseLLMParser

logger = logging.getLogger(__name__)


def _load_env() -> None:
    """Load environment variables from .env file if present."""
    # Try to find .env in backend directory
    current = Path(__file__).parent
    for _ in range(5):  # Search up to 5 levels
        env_file = current / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.debug(f"Loaded .env from {env_file}")
                return
            except ImportError:
                # dotenv not installed, try manual parsing
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
        logger.debug(f"Manually loaded .env from {env_file}")
    except Exception as e:
        logger.warning(f"Failed to load .env: {e}")


class GLMParser(BaseLLMParser):
    """
    GLM API client for parsing tax tables from PDF text.

    Uses the ZhipuAI SDK to call GLM-4.6 for intelligent table parsing.
    Requires GLM_API_KEY environment variable.

    Usage:
        parser = GLMParser()
        result = parser.parse_json(prompt)
    """

    def __init__(
        self,
        model: str = "glm-4.7",
        enable_thinking: bool = True,
        temperature: float = 0.1,
        max_tokens: int = 16384
    ):
        """
        Initialize GLM Parser.

        Args:
            model: GLM model to use (default: glm-4.6)
            enable_thinking: Enable thinking mode for complex reasoning
            temperature: Lower = more deterministic (default: 0.1 for data extraction)
            max_tokens: Maximum output tokens
        """
        self.model = model
        self.enable_thinking = enable_thinking
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        """Lazy initialization of ZhipuAI client."""
        if self._client is None:
            # Try to load from .env if not already set
            if not os.environ.get("GLM_API_KEY"):
                _load_env()

            api_key = os.environ.get("GLM_API_KEY")
            if not api_key:
                raise ValueError(
                    "GLM_API_KEY environment variable is required. "
                    "Get your API key from https://open.bigmodel.cn/"
                )

            try:
                from zhipuai import ZhipuAI
                self._client = ZhipuAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/coding/paas/v4/"
                )
                logger.info("ZhipuAI client initialized successfully")
            except ImportError:
                raise ImportError(
                    "zhipuai package is required. Install with: "
                    "uv add --optional tools zhipuai"
                )

        return self._client

    def is_available(self) -> bool:
        """Check if GLM API is available."""
        api_key = os.environ.get("GLM_API_KEY")
        if not api_key:
            return False

        try:
            from zhipuai import ZhipuAI  # noqa: F401
            return True
        except ImportError:
            return False

    def parse(self, prompt: str) -> str:
        """
        Send prompt to GLM API and get response.

        Args:
            prompt: The extraction prompt with table text and instructions

        Returns:
            Raw response content from GLM

        Raises:
            ValueError: If API call fails or returns invalid response
        """
        if len(prompt) < 100:
            raise ValueError(f"Prompt too short: {len(prompt)} chars")

        client = self._get_client()

        request_params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": 0.95,
        }

        if self.enable_thinking:
            request_params["thinking"] = {"type": "enabled"}
            logger.debug("Thinking mode enabled")

        logger.info(
            f"GLM API request: model={self.model}, "
            f"prompt_length={len(prompt)} chars"
        )

        try:
            response = client.chat.completions.create(**request_params)

            if not response.choices or len(response.choices) == 0:
                raise ValueError("GLM API returned no choices")

            choice = response.choices[0]
            content = choice.message.content if choice.message else None

            if not content:
                raise ValueError("GLM API returned empty content")

            # Log response details
            finish_reason = getattr(choice, "finish_reason", "N/A")
            logger.info(
                f"GLM API response: {len(content)} chars, "
                f"finish_reason={finish_reason}"
            )

            # Check for truncation
            if finish_reason in ("length", "max_tokens"):
                logger.warning(
                    f"Response may be truncated (finish_reason={finish_reason})"
                )

            return content.strip()

        except Exception as e:
            logger.error(f"GLM API call failed: {e}")
            raise ValueError(f"GLM API call failed: {e}")
