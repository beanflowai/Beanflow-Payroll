"""
Unit tests for Overtime Calculator Service.

Tests various scenarios:
- Weekly threshold provinces (ON, QC)
- Daily threshold provinces (AB, BC)
- BC double-time
- Holiday exclusion
- Multi-week periods
"""

from decimal import Decimal

import pytest

from app.services.overtime_calculator import (
    DailyHoursEntry,
    OvertimeResult,
    calculate_overtime_split,
)
from app.services.payroll.province_standards import InvalidProvinceCodeError


class TestWeeklyThresholdProvinces:
    """Tests for provinces with weekly threshold only (ON, QC, etc.)."""

    def test_ontario_under_threshold(self):
        """ON: 40 hours in a week → all regular, no overtime."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("8"), is_holiday=False),  # Mon
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("8"), is_holiday=False),  # Tue
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("8"), is_holiday=False),  # Wed
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("8"), is_holiday=False),  # Thu
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("8"), is_holiday=False),  # Fri
        ]

        result = calculate_overtime_split(entries, "ON")

        assert result.regular_hours == Decimal("40.00")
        assert result.overtime_hours == Decimal("0.00")
        assert result.double_time_hours == Decimal("0.00")

    def test_ontario_over_threshold(self):
        """ON: 50 hours in a week → 44 regular, 6 overtime (threshold is 44h)."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("10"), is_holiday=False),  # Mon
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("10"), is_holiday=False),  # Tue
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("10"), is_holiday=False),  # Wed
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("10"), is_holiday=False),  # Thu
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("10"), is_holiday=False),  # Fri
        ]

        result = calculate_overtime_split(entries, "ON")

        assert result.regular_hours == Decimal("44.00")
        assert result.overtime_hours == Decimal("6.00")
        assert result.double_time_hours == Decimal("0.00")

    def test_quebec_threshold(self):
        """QC: 45 hours in a week → 40 regular, 5 overtime (threshold is 40h)."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("9"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "QC")

        assert result.regular_hours == Decimal("40.00")
        assert result.overtime_hours == Decimal("5.00")


class TestDailyThresholdProvinces:
    """Tests for provinces with daily threshold (AB, BC, etc.)."""

    def test_alberta_daily_overtime(self):
        """AB: 9h/day × 5 days → 40h regular, 5h overtime (8h/day threshold)."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("9"), is_holiday=False),
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("9"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "AB")

        assert result.regular_hours == Decimal("40.00")
        assert result.overtime_hours == Decimal("5.00")
        assert result.double_time_hours == Decimal("0.00")

    def test_bc_daily_overtime(self):
        """BC: 10h/day → 8h regular, 2h overtime per day."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("10"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "BC")

        assert result.regular_hours == Decimal("8.00")
        assert result.overtime_hours == Decimal("2.00")
        assert result.double_time_hours == Decimal("0.00")

    def test_bc_double_time(self):
        """BC: 14h/day → 8h regular, 4h OT (8-12h), 2h double-time (>12h)."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("14"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "BC")

        assert result.regular_hours == Decimal("8.00")
        assert result.overtime_hours == Decimal("4.00")
        assert result.double_time_hours == Decimal("2.00")

    def test_bc_weekly_overflow(self):
        """BC: 8h × 6 days = 48h → triggers weekly threshold (40h)."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("8"), is_holiday=False),  # Mon
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("8"), is_holiday=False),  # Tue
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("8"), is_holiday=False),  # Wed
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("8"), is_holiday=False),  # Thu
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("8"), is_holiday=False),  # Fri
            DailyHoursEntry(date="2025-01-11", total_hours=Decimal("8"), is_holiday=False),  # Sat
        ]

        result = calculate_overtime_split(entries, "BC")

        # 6 × 8h = 48h, daily threshold is 8h (no daily OT)
        # Weekly threshold is 40h, so 8h becomes overtime
        assert result.regular_hours == Decimal("40.00")
        assert result.overtime_hours == Decimal("8.00")
        assert result.double_time_hours == Decimal("0.00")


class TestHolidayExclusion:
    """Tests for holiday exclusion."""

    def test_holiday_hours_excluded(self):
        """Hours on holidays should be excluded from overtime calculation."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("8"), is_holiday=False),
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("8"), is_holiday=True),  # Holiday
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("8"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "ON")

        # Holiday hours (8h) should be excluded, only 16h counted
        assert result.regular_hours == Decimal("16.00")
        assert result.overtime_hours == Decimal("0.00")


class TestMultiWeekPeriods:
    """Tests for pay periods spanning multiple weeks."""

    def test_two_week_period(self):
        """Two-week period with overtime in second week."""
        entries = [
            # Week 1: 40 hours (under Ontario's 44h threshold)
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("8"), is_holiday=False),
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("8"), is_holiday=False),
            DailyHoursEntry(date="2025-01-08", total_hours=Decimal("8"), is_holiday=False),
            DailyHoursEntry(date="2025-01-09", total_hours=Decimal("8"), is_holiday=False),
            DailyHoursEntry(date="2025-01-10", total_hours=Decimal("8"), is_holiday=False),
            # Week 2: 50 hours (6h over threshold)
            DailyHoursEntry(date="2025-01-13", total_hours=Decimal("10"), is_holiday=False),
            DailyHoursEntry(date="2025-01-14", total_hours=Decimal("10"), is_holiday=False),
            DailyHoursEntry(date="2025-01-15", total_hours=Decimal("10"), is_holiday=False),
            DailyHoursEntry(date="2025-01-16", total_hours=Decimal("10"), is_holiday=False),
            DailyHoursEntry(date="2025-01-17", total_hours=Decimal("10"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "ON")

        # Week 1: 40h regular, 0h OT
        # Week 2: 44h regular, 6h OT
        assert result.regular_hours == Decimal("84.00")
        assert result.overtime_hours == Decimal("6.00")


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_entries(self):
        """Empty entries should return zeros."""
        result = calculate_overtime_split([], "ON")

        assert result.regular_hours == Decimal("0.00")
        assert result.overtime_hours == Decimal("0.00")
        assert result.double_time_hours == Decimal("0.00")

    def test_zero_hours(self):
        """Zero hour entries should be skipped."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("0"), is_holiday=False),
            DailyHoursEntry(date="2025-01-07", total_hours=Decimal("8"), is_holiday=False),
        ]

        result = calculate_overtime_split(entries, "ON")

        assert result.regular_hours == Decimal("8.00")
        assert result.overtime_hours == Decimal("0.00")

    def test_invalid_province(self):
        """Invalid province code should raise error."""
        with pytest.raises(InvalidProvinceCodeError) as exc_info:
            calculate_overtime_split([], "XX")

        assert "Invalid province code" in str(exc_info.value)

    def test_federal_fallback(self):
        """Federal jurisdiction should work."""
        entries = [
            DailyHoursEntry(date="2025-01-06", total_hours=Decimal("50"), is_holiday=False),
        ]

        # This will use all 50h since no daily threshold, but weekly threshold is 40h
        # However, this is a single day in week, so 50h total, 40h regular, 10h OT
        result = calculate_overtime_split(entries, "Federal")

        assert result.regular_hours == Decimal("40.00")
        assert result.overtime_hours == Decimal("10.00")
