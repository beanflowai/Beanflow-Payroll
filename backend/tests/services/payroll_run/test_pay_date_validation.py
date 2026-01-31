"""
Tests for pay date validation functions.

Following TDD: Write test first, watch it fail, then implement.
"""

import pytest
from datetime import date

from app.services.payroll_run.constants import (
    get_pay_date_range,
    is_pay_date_compliant,
    get_tax_year,
)


class TestPayDateValidation:
    """Test pay date validation helper functions."""

    def test_get_pay_date_range_saskatchewan(self):
        """Test SK province: 6 days delay."""
        period_end = date(2025, 12, 31)
        earliest, recommended, latest = get_pay_date_range(period_end, "SK")

        assert earliest == date(2025, 12, 31), "Earliest should be period_end"
        assert recommended == date(2026, 1, 6), "SK should have 6 days delay"
        assert latest == date(2026, 1, 6), "SK latest should match recommended"

    def test_get_pay_date_range_quebec(self):
        """Test QC province: 16 days delay."""
        period_end = date(2025, 12, 31)
        earliest, recommended, latest = get_pay_date_range(period_end, "QC")

        assert earliest == date(2025, 12, 31), "Earliest should be period_end"
        assert recommended == date(2026, 1, 16), "QC should have 16 days delay"
        assert latest == date(2026, 1, 16), "QC latest should match recommended"

    def test_get_pay_date_range_ontario(self):
        """Test ON province: 7 days delay."""
        period_end = date(2025, 1, 15)
        earliest, recommended, latest = get_pay_date_range(period_end, "ON")

        assert earliest == date(2025, 1, 15), "Earliest should be period_end"
        assert recommended == date(2025, 1, 22), "ON should have 7 days delay"
        assert latest == date(2025, 1, 22), "ON latest should match recommended"

    def test_is_pay_date_compliant_valid(self):
        """Test compliant pay date."""
        period_end = date(2025, 12, 31)
        pay_date = date(2025, 12, 31)  # Early payment on same day

        assert is_pay_date_compliant(pay_date, period_end, "SK") is True

    def test_is_pay_date_compliant_recommended(self):
        """Test pay date exactly at recommended date."""
        period_end = date(2025, 12, 31)
        pay_date = date(2026, 1, 6)  # Exactly at SK deadline

        assert is_pay_date_compliant(pay_date, period_end, "SK") is True

    def test_is_pay_date_compliant_invalid(self):
        """Test non-compliant pay date (after legal deadline)."""
        period_end = date(2025, 12, 31)
        pay_date = date(2026, 1, 7)  # After SK deadline (Jan 6)

        assert is_pay_date_compliant(pay_date, period_end, "SK") is False

    def test_is_pay_date_compliant_quebec_longer(self):
        """Test compliance with Quebec's longer deadline."""
        period_end = date(2025, 12, 31)
        pay_date = date(2026, 1, 10)  # Valid for QC (16 days) but not for SK

        assert is_pay_date_compliant(pay_date, period_end, "QC") is True
        assert is_pay_date_compliant(pay_date, period_end, "SK") is False

    def test_is_pay_date_compliant_before_period_end_strict(self):
        """Test that pay date before period end is not compliant with strict mode (allow_early_days=0)."""
        period_end = date(2025, 12, 31)
        pay_date = date(2025, 12, 30)  # Before period end

        # With allow_early_days=0 (strict), pay date before period end is not allowed
        assert is_pay_date_compliant(pay_date, period_end, "SK", allow_early_days=0) is False

    def test_is_pay_date_compliant_before_period_end_with_early_allowance(self):
        """Test that pay date within early allowance window is compliant."""
        period_end = date(2025, 12, 31)

        # Default allow_early_days=10, so up to 10 days early is allowed
        pay_date_1_day_early = date(2025, 12, 30)
        pay_date_10_days_early = date(2025, 12, 21)
        pay_date_11_days_early = date(2025, 12, 20)

        assert is_pay_date_compliant(pay_date_1_day_early, period_end, "SK") is True
        assert is_pay_date_compliant(pay_date_10_days_early, period_end, "SK") is True
        assert is_pay_date_compliant(pay_date_11_days_early, period_end, "SK") is False

    def test_get_tax_year_december(self):
        """Test tax year detection for December."""
        assert get_tax_year(date(2025, 12, 31)) == 2025
        assert get_tax_year(date(2025, 12, 15)) == 2025

    def test_get_tax_year_january(self):
        """Test tax year detection for January."""
        assert get_tax_year(date(2026, 1, 1)) == 2026
        assert get_tax_year(date(2026, 1, 6)) == 2026
        assert get_tax_year(date(2026, 1, 31)) == 2026

    def test_all_province_delays(self):
        """Test all province delay configurations."""
        period_end = date(2025, 1, 15)

        expected_delays = [
            ("NB", 5), ("NS", 5), ("SK", 6), ("ON", 7), ("PE", 7), ("NL", 7),
            ("BC", 8), ("AB", 10), ("MB", 10), ("NT", 10), ("NU", 10), ("YT", 10),
            ("QC", 16)
        ]

        for province, expected_delay in expected_delays:
            _, recommended, _ = get_pay_date_range(period_end, province)
            expected_date = date(2025, 1, 15 + expected_delay)
            assert recommended == expected_date, \
                f"{province} failed: expected {expected_date}, got {recommended}"

    def test_cross_year_pay_date(self):
        """Test cross-year pay date calculation."""
        period_end = date(2025, 12, 31)

        # SK: Dec 31 + 6 days = Jan 6, 2026
        _, recommended_sk, latest_sk = get_pay_date_range(period_end, "SK")
        assert recommended_sk == date(2026, 1, 6)
        assert latest_sk == date(2026, 1, 6)

        # QC: Dec 31 + 16 days = Jan 16, 2026
        _, recommended_qc, latest_qc = get_pay_date_range(period_end, "QC")
        assert recommended_qc == date(2026, 1, 16)
        assert latest_qc == date(2026, 1, 16)

    def test_february_pay_date(self):
        """Test pay date calculation in February (leap year)."""
        period_end = date(2024, 2, 15)  # Leap year

        # ON: Feb 15 + 7 days = Feb 22, 2024
        _, recommended, latest = get_pay_date_range(period_end, "ON")
        assert recommended == date(2024, 2, 22)
        assert latest == date(2024, 2, 22)

    def test_unknown_province_uses_default(self):
        """Test that unknown province uses default delay."""
        period_end = date(2025, 12, 31)

        # Default is 7 days
        _, recommended, latest = get_pay_date_range(period_end, "XX")
        assert recommended == date(2026, 1, 7)
        assert latest == date(2026, 1, 7)
