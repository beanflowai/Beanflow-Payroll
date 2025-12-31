"""
Allow running as: python -m tools.tax_config_converter
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
