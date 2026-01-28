"""ROE (Record of Employment) services.

This module provides utilities for generating ROE data, including:
- Insurable hours calculation for salaried and hourly employees
- ROE data aggregation
"""

from app.services.roe.insurable_hours_calculator import (
    InsurableHoursCalculator,
    calculate_insurable_hours,
)

__all__ = [
    "InsurableHoursCalculator",
    "calculate_insurable_hours",
]
