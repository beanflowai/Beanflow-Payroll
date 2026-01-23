"""Holiday Pay Calculator - Backwards Compatibility Module.

This module has been refactored into the holiday_pay/ subpackage.
This file re-exports the main classes for backwards compatibility.

New imports should use:
    from app.services.payroll_run.holiday_pay import HolidayPayCalculator, HolidayPayResult
"""

from app.services.payroll_run.holiday_pay import (
    HolidayPayCalculator,
    HolidayPayResult,
)
from app.services.payroll_run.holiday_pay.formula_calculators import (
    WORK_DAYS_PER_PERIOD,
)

# Re-export for backwards compatibility
__all__ = [
    "HolidayPayCalculator",
    "HolidayPayResult",
    "WORK_DAYS_PER_PERIOD",
]
