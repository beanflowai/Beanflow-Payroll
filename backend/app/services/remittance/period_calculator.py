"""Remittance Period Calculator.

Utility functions for calculating remittance period boundaries and due dates
based on CRA remitter type classification.

Remitter Types:
- quarterly: AMWA < $3,000 (4 periods/year)
- regular: AMWA $3,000 - $24,999 (12 periods/year, monthly)
- threshold_1: AMWA $25,000 - $99,999 (24 periods/year, twice monthly)
- threshold_2: AMWA >= $100,000 (up to 48 periods/year)
"""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date

logger = logging.getLogger(__name__)


def calculate_monthly_period_bounds(reference_date: date) -> tuple[date, date]:
    """Calculate monthly remittance period boundaries.

    For "regular" remitters, periods are full calendar months.

    Args:
        reference_date: Any date within the target month

    Returns:
        Tuple of (period_start, period_end) where:
        - period_start is 1st day of month
        - period_end is last day of month
    """
    year = reference_date.year
    month = reference_date.month
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return (first_day, last_day)


def calculate_monthly_due_date(period_end: date) -> date:
    """Calculate due date for monthly (regular) remitter.

    Due date is the 15th of the month following the remittance period.

    Args:
        period_end: Last day of the remittance period

    Returns:
        Due date (15th of following month)
    """
    if period_end.month == 12:
        return date(period_end.year + 1, 1, 15)
    return date(period_end.year, period_end.month + 1, 15)


def calculate_quarterly_period_bounds(reference_date: date) -> tuple[date, date]:
    """Calculate quarterly remittance period boundaries.

    Quarters:
    - Q1: January - March
    - Q2: April - June
    - Q3: July - September
    - Q4: October - December

    Args:
        reference_date: Any date within the target quarter

    Returns:
        Tuple of (period_start, period_end)
    """
    year = reference_date.year
    month = reference_date.month
    quarter = (month - 1) // 3
    quarter_start_month = quarter * 3 + 1
    quarter_end_month = quarter_start_month + 2

    first_day = date(year, quarter_start_month, 1)
    last_day = date(year, quarter_end_month, monthrange(year, quarter_end_month)[1])
    return (first_day, last_day)


def calculate_quarterly_due_date(period_end: date) -> date:
    """Calculate due date for quarterly remitter.

    Due date is the 15th of the month following quarter end.

    Args:
        period_end: Last day of the quarter

    Returns:
        Due date (15th of following month)
    """
    if period_end.month == 12:
        return date(period_end.year + 1, 1, 15)
    return date(period_end.year, period_end.month + 1, 15)


def calculate_threshold1_period_bounds(reference_date: date) -> tuple[date, date]:
    """Calculate threshold 1 (twice monthly) period boundaries.

    Periods:
    - 1st to 15th of month
    - 16th to last day of month

    Args:
        reference_date: Any date within the target period

    Returns:
        Tuple of (period_start, period_end)
    """
    year = reference_date.year
    month = reference_date.month
    day = reference_date.day

    if day <= 15:
        first_day = date(year, month, 1)
        last_day = date(year, month, 15)
    else:
        first_day = date(year, month, 16)
        last_day = date(year, month, monthrange(year, month)[1])

    return (first_day, last_day)


def calculate_threshold1_due_date(period_end: date) -> date:
    """Calculate due date for threshold 1 remitter.

    Due dates:
    - 1st-15th period: Due 25th of same month
    - 16th-end period: Due 10th of next month

    Args:
        period_end: Last day of the period

    Returns:
        Due date
    """
    if period_end.day == 15:
        return date(period_end.year, period_end.month, 25)
    else:
        if period_end.month == 12:
            return date(period_end.year + 1, 1, 10)
        return date(period_end.year, period_end.month + 1, 10)


def get_period_bounds_and_due_date(
    reference_date: date, remitter_type: str
) -> tuple[date, date, date]:
    """Get period boundaries and due date based on remitter type.

    Args:
        reference_date: The payroll run's period_end date
        remitter_type: One of 'quarterly', 'regular', 'threshold_1', 'threshold_2'

    Returns:
        Tuple of (period_start, period_end, due_date)

    Raises:
        ValueError: If remitter_type is not recognized
    """
    if remitter_type == "regular":
        start, end = calculate_monthly_period_bounds(reference_date)
        due = calculate_monthly_due_date(end)
    elif remitter_type == "quarterly":
        start, end = calculate_quarterly_period_bounds(reference_date)
        due = calculate_quarterly_due_date(end)
    elif remitter_type == "threshold_1":
        start, end = calculate_threshold1_period_bounds(reference_date)
        due = calculate_threshold1_due_date(end)
    elif remitter_type == "threshold_2":
        # Threshold 2 has complex rules (up to 4 times monthly)
        # TODO: Implement full threshold_2 logic with weekly periods
        # For now, treat same as threshold_1 with warning
        logger.warning(
            "threshold_2 remitter type is not fully implemented. "
            "Using threshold_1 rules (twice monthly) as fallback. "
            "Actual threshold_2 may require up to 4 remittances per month."
        )
        start, end = calculate_threshold1_period_bounds(reference_date)
        due = calculate_threshold1_due_date(end)
    else:
        raise ValueError(f"Unknown remitter_type: {remitter_type}")

    return (start, end, due)
