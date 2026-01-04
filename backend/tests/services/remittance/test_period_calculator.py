"""Tests for remittance period calculator."""

from datetime import date

import pytest

from app.services.remittance.period_calculator import (
    calculate_monthly_due_date,
    calculate_monthly_period_bounds,
    calculate_quarterly_due_date,
    calculate_quarterly_period_bounds,
    calculate_threshold1_due_date,
    calculate_threshold1_period_bounds,
    get_period_bounds_and_due_date,
)


class TestCalculateMonthlyPeriodBounds:
    """Tests for monthly period boundary calculation."""

    def test_january_bounds(self):
        """Test January period bounds."""
        start, end = calculate_monthly_period_bounds(date(2025, 1, 15))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_february_bounds_non_leap_year(self):
        """Test February bounds in non-leap year."""
        start, end = calculate_monthly_period_bounds(date(2025, 2, 10))
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_february_bounds_leap_year(self):
        """Test February bounds in leap year."""
        start, end = calculate_monthly_period_bounds(date(2024, 2, 10))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_december_bounds(self):
        """Test December period bounds."""
        start, end = calculate_monthly_period_bounds(date(2025, 12, 25))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_first_day_of_month(self):
        """Test with first day of month as reference."""
        start, end = calculate_monthly_period_bounds(date(2025, 6, 1))
        assert start == date(2025, 6, 1)
        assert end == date(2025, 6, 30)

    def test_last_day_of_month(self):
        """Test with last day of month as reference."""
        start, end = calculate_monthly_period_bounds(date(2025, 3, 31))
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)


class TestCalculateMonthlyDueDate:
    """Tests for monthly due date calculation."""

    def test_january_period_due_date(self):
        """Test January period due date is Feb 15."""
        due = calculate_monthly_due_date(date(2025, 1, 31))
        assert due == date(2025, 2, 15)

    def test_december_period_due_date(self):
        """Test December period due date is Jan 15 next year."""
        due = calculate_monthly_due_date(date(2025, 12, 31))
        assert due == date(2026, 1, 15)

    def test_november_period_due_date(self):
        """Test November period due date is Dec 15."""
        due = calculate_monthly_due_date(date(2025, 11, 30))
        assert due == date(2025, 12, 15)


class TestCalculateQuarterlyPeriodBounds:
    """Tests for quarterly period boundary calculation."""

    def test_q1_bounds(self):
        """Test Q1 (Jan-Mar) bounds."""
        # January
        start, end = calculate_quarterly_period_bounds(date(2025, 1, 15))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)

        # February
        start, end = calculate_quarterly_period_bounds(date(2025, 2, 20))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)

        # March
        start, end = calculate_quarterly_period_bounds(date(2025, 3, 31))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)

    def test_q2_bounds(self):
        """Test Q2 (Apr-Jun) bounds."""
        start, end = calculate_quarterly_period_bounds(date(2025, 5, 15))
        assert start == date(2025, 4, 1)
        assert end == date(2025, 6, 30)

    def test_q3_bounds(self):
        """Test Q3 (Jul-Sep) bounds."""
        start, end = calculate_quarterly_period_bounds(date(2025, 8, 15))
        assert start == date(2025, 7, 1)
        assert end == date(2025, 9, 30)

    def test_q4_bounds(self):
        """Test Q4 (Oct-Dec) bounds."""
        start, end = calculate_quarterly_period_bounds(date(2025, 11, 15))
        assert start == date(2025, 10, 1)
        assert end == date(2025, 12, 31)


class TestCalculateQuarterlyDueDate:
    """Tests for quarterly due date calculation."""

    def test_q1_due_date(self):
        """Test Q1 due date is Apr 15."""
        due = calculate_quarterly_due_date(date(2025, 3, 31))
        assert due == date(2025, 4, 15)

    def test_q2_due_date(self):
        """Test Q2 due date is Jul 15."""
        due = calculate_quarterly_due_date(date(2025, 6, 30))
        assert due == date(2025, 7, 15)

    def test_q4_due_date(self):
        """Test Q4 due date is Jan 15 next year."""
        due = calculate_quarterly_due_date(date(2025, 12, 31))
        assert due == date(2026, 1, 15)


class TestCalculateThreshold1PeriodBounds:
    """Tests for threshold 1 (twice monthly) period bounds."""

    def test_first_half_of_month(self):
        """Test 1st-15th period bounds."""
        # Day 1
        start, end = calculate_threshold1_period_bounds(date(2025, 1, 1))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 15)

        # Day 15
        start, end = calculate_threshold1_period_bounds(date(2025, 1, 15))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 15)

        # Day 10
        start, end = calculate_threshold1_period_bounds(date(2025, 1, 10))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 15)

    def test_second_half_of_month(self):
        """Test 16th-end period bounds."""
        # Day 16
        start, end = calculate_threshold1_period_bounds(date(2025, 1, 16))
        assert start == date(2025, 1, 16)
        assert end == date(2025, 1, 31)

        # Day 31
        start, end = calculate_threshold1_period_bounds(date(2025, 1, 31))
        assert start == date(2025, 1, 16)
        assert end == date(2025, 1, 31)

    def test_february_second_half(self):
        """Test second half of February (28 days)."""
        start, end = calculate_threshold1_period_bounds(date(2025, 2, 20))
        assert start == date(2025, 2, 16)
        assert end == date(2025, 2, 28)

    def test_february_leap_year_second_half(self):
        """Test second half of February (29 days in leap year)."""
        start, end = calculate_threshold1_period_bounds(date(2024, 2, 20))
        assert start == date(2024, 2, 16)
        assert end == date(2024, 2, 29)


class TestCalculateThreshold1DueDate:
    """Tests for threshold 1 due date calculation."""

    def test_first_half_due_date(self):
        """Test 1st-15th period due date is 25th of same month."""
        due = calculate_threshold1_due_date(date(2025, 1, 15))
        assert due == date(2025, 1, 25)

    def test_second_half_due_date(self):
        """Test 16th-end period due date is 10th of next month."""
        due = calculate_threshold1_due_date(date(2025, 1, 31))
        assert due == date(2025, 2, 10)

    def test_december_second_half_due_date(self):
        """Test December 16th-31st due date is Jan 10 next year."""
        due = calculate_threshold1_due_date(date(2025, 12, 31))
        assert due == date(2026, 1, 10)


class TestGetPeriodBoundsAndDueDate:
    """Tests for the combined period bounds and due date function."""

    def test_regular_remitter(self):
        """Test regular (monthly) remitter period calculation."""
        start, end, due = get_period_bounds_and_due_date(date(2025, 3, 15), "regular")
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)
        assert due == date(2025, 4, 15)

    def test_quarterly_remitter(self):
        """Test quarterly remitter period calculation."""
        start, end, due = get_period_bounds_and_due_date(date(2025, 5, 15), "quarterly")
        assert start == date(2025, 4, 1)
        assert end == date(2025, 6, 30)
        assert due == date(2025, 7, 15)

    def test_threshold_1_remitter_first_half(self):
        """Test threshold 1 remitter first half of month."""
        start, end, due = get_period_bounds_and_due_date(
            date(2025, 3, 10), "threshold_1"
        )
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 15)
        assert due == date(2025, 3, 25)

    def test_threshold_1_remitter_second_half(self):
        """Test threshold 1 remitter second half of month."""
        start, end, due = get_period_bounds_and_due_date(
            date(2025, 3, 20), "threshold_1"
        )
        assert start == date(2025, 3, 16)
        assert end == date(2025, 3, 31)
        assert due == date(2025, 4, 10)

    def test_threshold_2_remitter_fallback(self):
        """Test threshold 2 falls back to threshold 1 with warning."""
        start, end, due = get_period_bounds_and_due_date(
            date(2025, 3, 10), "threshold_2"
        )
        # Should use threshold_1 logic
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 15)
        assert due == date(2025, 3, 25)

    def test_invalid_remitter_type(self):
        """Test invalid remitter type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown remitter_type"):
            get_period_bounds_and_due_date(date(2025, 3, 15), "invalid_type")
