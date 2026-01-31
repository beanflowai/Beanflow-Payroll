"""Holiday Pay Calculation Module.

This module provides holiday pay calculation for Canadian payroll,
split into logical components for maintainability:

- HolidayPayCalculator: Main calculator (orchestrator)
- EligibilityChecker: Eligibility rule checking
- WorkDayTracker: Work day tracking and counting
- FormulaCalculators: Provincial formula implementations
- EarningsFetcher: Historical earnings queries
"""

from app.services.payroll_run.holiday_pay.calculator import (
    HolidayPayCalculator,
    HolidayPayResult,
)

__all__ = [
    "HolidayPayCalculator",
    "HolidayPayResult",
]
