"""Tests for payroll run constants and utility functions."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.services.payroll_run.constants import (
    COMPLETED_RUN_STATUSES,
    DEFAULT_FEDERAL_BPA_FALLBACK,
    DEFAULT_HOURS_PER_PERIOD,
    DEFAULT_PAY_DATE_DELAY,
    DEFAULT_TAX_YEAR,
    PAY_DATE_DELAY_DAYS,
    PERIODS_PER_YEAR,
    calculate_next_pay_date,
    calculate_next_period_end,
    calculate_pay_date,
    extract_year_from_date,
    get_federal_bpa,
    get_provincial_bpa,
)


class TestConstants:
    """Tests for module constants."""

    def test_default_federal_bpa_fallback(self):
        """Test default federal BPA fallback value."""
        assert DEFAULT_FEDERAL_BPA_FALLBACK == Decimal("16129")

    def test_completed_run_statuses(self):
        """Test completed run statuses."""
        assert "approved" in COMPLETED_RUN_STATUSES
        assert "paid" in COMPLETED_RUN_STATUSES
        assert len(COMPLETED_RUN_STATUSES) == 2

    def test_default_tax_year(self):
        """Test default tax year."""
        assert DEFAULT_TAX_YEAR == 2025

    def test_periods_per_year(self):
        """Test periods per year for each frequency."""
        assert PERIODS_PER_YEAR["weekly"] == 52
        assert PERIODS_PER_YEAR["bi_weekly"] == 26
        assert PERIODS_PER_YEAR["semi_monthly"] == 24
        assert PERIODS_PER_YEAR["monthly"] == 12

    def test_default_hours_per_period(self):
        """Test default hours per period for each frequency."""
        assert DEFAULT_HOURS_PER_PERIOD["weekly"] == Decimal("40")
        assert DEFAULT_HOURS_PER_PERIOD["bi_weekly"] == Decimal("80")
        assert DEFAULT_HOURS_PER_PERIOD["semi_monthly"] == Decimal("86.67")
        assert DEFAULT_HOURS_PER_PERIOD["monthly"] == Decimal("173.33")

    def test_pay_date_delay_days(self):
        """Test pay date delay days by province."""
        assert PAY_DATE_DELAY_DAYS["SK"] == 6
        assert PAY_DATE_DELAY_DAYS["ON"] == 7
        assert PAY_DATE_DELAY_DAYS["BC"] == 8
        assert PAY_DATE_DELAY_DAYS["AB"] == 10
        assert PAY_DATE_DELAY_DAYS["QC"] == 16
        assert PAY_DATE_DELAY_DAYS["NB"] == 5
        assert PAY_DATE_DELAY_DAYS["NS"] == 5
        assert DEFAULT_PAY_DATE_DELAY == 7


class TestExtractYearFromDate:
    """Tests for extract_year_from_date function."""

    def test_valid_date_string(self):
        """Test extracting year from valid date string."""
        assert extract_year_from_date("2025-01-15") == 2025
        assert extract_year_from_date("2024-12-31") == 2024
        assert extract_year_from_date("2030-06-01") == 2030

    def test_date_string_with_only_year(self):
        """Test extracting year from string with only year portion."""
        assert extract_year_from_date("2025") == 2025
        assert extract_year_from_date("2025-") == 2025

    def test_empty_string_returns_default(self):
        """Test empty string returns default."""
        assert extract_year_from_date("") == DEFAULT_TAX_YEAR
        assert extract_year_from_date("", 2030) == 2030

    def test_none_returns_default(self):
        """Test None returns default."""
        assert extract_year_from_date(None) == DEFAULT_TAX_YEAR
        assert extract_year_from_date(None, 2030) == 2030

    def test_non_string_returns_default(self):
        """Test non-string input returns default."""
        assert extract_year_from_date(12345) == DEFAULT_TAX_YEAR

    def test_short_string_returns_default(self):
        """Test string shorter than 4 chars returns default."""
        assert extract_year_from_date("202") == DEFAULT_TAX_YEAR
        assert extract_year_from_date("20") == DEFAULT_TAX_YEAR

    def test_non_numeric_year_returns_default(self):
        """Test non-numeric year portion returns default."""
        assert extract_year_from_date("ABCD-01-15") == DEFAULT_TAX_YEAR
        assert extract_year_from_date("20AB-01-15") == DEFAULT_TAX_YEAR


class TestGetFederalBpa:
    """Tests for get_federal_bpa function."""

    def test_get_federal_bpa_success(self):
        """Test getting federal BPA from tax tables."""
        with patch("app.services.payroll_run.constants.get_federal_config") as mock_config:
            mock_config.return_value = {"bpaf": 16129}

            result = get_federal_bpa(2025)

            assert result == Decimal("16129")
            mock_config.assert_called_once_with(2025, None)

    def test_get_federal_bpa_with_pay_date(self):
        """Test getting federal BPA with pay date."""
        with patch("app.services.payroll_run.constants.get_federal_config") as mock_config:
            mock_config.return_value = {"bpaf": 16500}
            pay_date = date(2025, 7, 15)

            result = get_federal_bpa(2025, pay_date)

            assert result == Decimal("16500")
            mock_config.assert_called_once_with(2025, pay_date)

    def test_get_federal_bpa_fallback_on_error(self):
        """Test fallback to default BPA on error."""
        with patch("app.services.payroll_run.constants.get_federal_config") as mock_config:
            mock_config.side_effect = Exception("Config not found")

            result = get_federal_bpa(2025)

            assert result == DEFAULT_FEDERAL_BPA_FALLBACK


class TestGetProvincialBpa:
    """Tests for get_provincial_bpa function."""

    def test_get_provincial_bpa_success(self):
        """Test getting provincial BPA from tax tables."""
        with patch("app.services.payroll_run.constants.get_province_config") as mock_config:
            mock_config.return_value = {"bpa": 15705}

            result = get_provincial_bpa("ON", 2025)

            assert result == Decimal("15705")
            mock_config.assert_called_once_with("ON", 2025, None)

    def test_get_provincial_bpa_with_pay_date(self):
        """Test getting provincial BPA with pay date for SK/PE."""
        with patch("app.services.payroll_run.constants.get_province_config") as mock_config:
            mock_config.return_value = {"bpa": 18500}
            pay_date = date(2025, 7, 15)

            result = get_provincial_bpa("SK", 2025, pay_date)

            assert result == Decimal("18500")
            mock_config.assert_called_once_with("SK", 2025, pay_date)

    def test_get_provincial_bpa_fallback_on_error(self):
        """Test fallback to Ontario default BPA on error."""
        with patch("app.services.payroll_run.constants.get_province_config") as mock_config:
            mock_config.side_effect = Exception("Province not found")

            result = get_provincial_bpa("XX", 2025)

            assert result == Decimal("12747")


class TestCalculatePayDate:
    """Tests for calculate_pay_date function."""

    def test_calculate_pay_date_sk(self):
        """Test pay date calculation for Saskatchewan (6 days)."""
        period_end = date(2025, 1, 15)
        result = calculate_pay_date(period_end, "SK")
        assert result == date(2025, 1, 21)

    def test_calculate_pay_date_on(self):
        """Test pay date calculation for Ontario (7 days)."""
        period_end = date(2025, 1, 15)
        result = calculate_pay_date(period_end, "ON")
        assert result == date(2025, 1, 22)

    def test_calculate_pay_date_qc(self):
        """Test pay date calculation for Quebec (16 days)."""
        period_end = date(2025, 1, 15)
        result = calculate_pay_date(period_end, "QC")
        assert result == date(2025, 1, 31)

    def test_calculate_pay_date_unknown_province(self):
        """Test pay date calculation for unknown province uses default."""
        period_end = date(2025, 1, 15)
        result = calculate_pay_date(period_end, "XX")
        assert result == date(2025, 1, 22)  # Default 7 days

    def test_calculate_pay_date_across_month(self):
        """Test pay date calculation across month boundary."""
        period_end = date(2025, 1, 28)
        result = calculate_pay_date(period_end, "AB")  # 10 days
        assert result == date(2025, 2, 7)


class TestCalculateNextPeriodEnd:
    """Tests for calculate_next_period_end function."""

    def test_weekly_period_end(self):
        """Test weekly period end calculation."""
        current = date(2025, 1, 15)
        result = calculate_next_period_end(current, "weekly")
        assert result == date(2025, 1, 22)

    def test_bi_weekly_period_end(self):
        """Test bi-weekly period end calculation."""
        current = date(2025, 1, 15)
        result = calculate_next_period_end(current, "bi_weekly")
        assert result == date(2025, 1, 29)

    def test_semi_monthly_period_end_from_15th(self):
        """Test semi-monthly from 15th goes to end of month."""
        current = date(2025, 1, 15)
        result = calculate_next_period_end(current, "semi_monthly")
        assert result == date(2025, 1, 31)

    def test_semi_monthly_period_end_from_end_of_month(self):
        """Test semi-monthly from end of month goes to 15th."""
        current = date(2025, 1, 31)
        result = calculate_next_period_end(current, "semi_monthly")
        assert result == date(2025, 2, 15)

    def test_semi_monthly_period_end_december(self):
        """Test semi-monthly from December end goes to January 15."""
        current = date(2025, 12, 31)
        result = calculate_next_period_end(current, "semi_monthly")
        assert result == date(2026, 1, 15)

    def test_monthly_period_end_last_day(self):
        """Test monthly from last day stays on last day."""
        current = date(2025, 1, 31)
        result = calculate_next_period_end(current, "monthly")
        assert result == date(2025, 2, 28)

    def test_monthly_period_end_mid_month(self):
        """Test monthly from mid-month stays on same day."""
        current = date(2025, 1, 20)
        result = calculate_next_period_end(current, "monthly")
        assert result == date(2025, 2, 20)

    def test_monthly_period_end_december(self):
        """Test monthly from December goes to next year."""
        current = date(2025, 12, 31)
        result = calculate_next_period_end(current, "monthly")
        assert result == date(2026, 1, 31)

    def test_monthly_period_end_day_31_to_shorter_month(self):
        """Test monthly handles day 31 to shorter month."""
        current = date(2025, 3, 31)
        result = calculate_next_period_end(current, "monthly")
        assert result == date(2025, 4, 30)  # April has 30 days

    def test_unknown_frequency_defaults_to_bi_weekly(self):
        """Test unknown frequency defaults to bi-weekly."""
        current = date(2025, 1, 15)
        result = calculate_next_period_end(current, "unknown")
        assert result == date(2025, 1, 29)


class TestCalculateNextPayDate:
    """Tests for calculate_next_pay_date function (legacy)."""

    def test_weekly_pay_date(self):
        """Test weekly pay date calculation."""
        current = date(2025, 1, 15)
        result = calculate_next_pay_date(current, "weekly")
        assert result == date(2025, 1, 22)

    def test_bi_weekly_pay_date(self):
        """Test bi-weekly pay date calculation."""
        current = date(2025, 1, 15)
        result = calculate_next_pay_date(current, "bi_weekly")
        assert result == date(2025, 1, 29)

    def test_semi_monthly_pay_date_from_15th(self):
        """Test semi-monthly from 15th goes to end of month."""
        current = date(2025, 1, 15)
        result = calculate_next_pay_date(current, "semi_monthly")
        assert result == date(2025, 1, 31)

    def test_semi_monthly_pay_date_from_end_of_month(self):
        """Test semi-monthly from end of month goes to 15th."""
        current = date(2025, 1, 31)
        result = calculate_next_pay_date(current, "semi_monthly")
        assert result == date(2025, 2, 15)

    def test_semi_monthly_pay_date_december(self):
        """Test semi-monthly from December end goes to January 15."""
        current = date(2025, 12, 31)
        result = calculate_next_pay_date(current, "semi_monthly")
        assert result == date(2026, 1, 15)

    def test_monthly_pay_date_last_day(self):
        """Test monthly from last day stays on last day."""
        current = date(2025, 1, 31)
        result = calculate_next_pay_date(current, "monthly")
        assert result == date(2025, 2, 28)

    def test_monthly_pay_date_mid_month(self):
        """Test monthly from mid-month stays on same day."""
        current = date(2025, 1, 20)
        result = calculate_next_pay_date(current, "monthly")
        assert result == date(2025, 2, 20)

    def test_monthly_pay_date_december(self):
        """Test monthly from December goes to next year."""
        current = date(2025, 12, 31)
        result = calculate_next_pay_date(current, "monthly")
        assert result == date(2026, 1, 31)

    def test_monthly_pay_date_day_31_to_shorter_month(self):
        """Test monthly handles day 31 to shorter month."""
        current = date(2025, 3, 31)
        result = calculate_next_pay_date(current, "monthly")
        assert result == date(2025, 4, 30)

    def test_unknown_frequency_defaults_to_bi_weekly(self):
        """Test unknown frequency defaults to bi-weekly."""
        current = date(2025, 1, 15)
        result = calculate_next_pay_date(current, "unknown")
        assert result == date(2025, 1, 29)
