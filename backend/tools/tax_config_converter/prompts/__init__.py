"""Extraction prompts for different tax configuration types."""

from .cpp_ei_prompt import create_cpp_ei_prompt
from .federal_prompt import create_federal_prompt
from .provinces_prompt import create_provinces_prompt

__all__ = ["create_cpp_ei_prompt", "create_federal_prompt", "create_provinces_prompt"]
