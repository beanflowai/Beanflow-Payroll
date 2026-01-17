"""
Tests for pay date configuration loader.

Following TDD: Write test first, watch it fail, then implement.
"""

import pytest
from datetime import date

from app.services.payroll_run.constants import (
    PAY_DATE_DELAY_DAYS,
    DEFAULT_PAY_DATE_DELAY,
    calculate_pay_date,
    get_province_pay_date_info,
    get_province_name,
)


class TestPayDateConfigLoader:
    """Test pay date configuration loading from JSON file."""

    def test_config_loaded_successfully(self):
        """Test that config file is loaded correctly."""
        # Should be able to get province info for all Canadian provinces
        sk_info = get_province_pay_date_info("SK")
        assert sk_info is not None
        assert isinstance(sk_info, dict)

    def test_pay_date_delay_days_structure(self):
        """Test that PAY_DATE_DELAY_DAYS has correct structure."""
        assert isinstance(PAY_DATE_DELAY_DAYS, dict)
        assert all(isinstance(v, int) for v in PAY_DATE_DELAY_DAYS.values())
        assert PAY_DATE_DELAY_DAYS["SK"] == 6
        assert PAY_DATE_DELAY_DAYS["QC"] == 16

    def test_get_province_pay_date_info(self):
        """Test getting full province information."""
        sk_info = get_province_pay_date_info("SK")
        assert sk_info["delay_days"] == 6
        assert sk_info["name"] == "Saskatchewan"
        assert "reference" in sk_info
        assert "The Saskatchewan Employment Act" in sk_info["reference"]

        # Test Ontario
        on_info = get_province_pay_date_info("ON")
        assert on_info["delay_days"] == 7
        assert on_info["name"] == "Ontario"

        # Test Quebec (has longest delay)
        qc_info = get_province_pay_date_info("QC")
        assert qc_info["delay_days"] == 16
        assert qc_info["name"] == "Quebec"

    def test_get_province_name(self):
        """Test getting province name."""
        assert get_province_name("SK") == "Saskatchewan"
        assert get_province_name("ON") == "Ontario"
        assert get_province_name("BC") == "British Columbia"
        assert get_province_name("AB") == "Alberta"

        # Test that invalid province returns the code itself
        assert get_province_name("XX") == "XX"

    def test_all_provinces_have_required_fields(self):
        """Test that all provinces have delay_days and name."""
        provinces_to_test = ["SK", "ON", "BC", "AB", "MB", "QC", "NB", "NS", "PE", "NL", "NT", "NU", "YT"]

        for province in provinces_to_test:
            info = get_province_pay_date_info(province)
            assert "delay_days" in info, f"{province} missing delay_days"
            assert isinstance(info["delay_days"], int), f"{province} delay_days not int"
            assert "name" in info, f"{province} missing name"
            assert isinstance(info["name"], str), f"{province} name not str"

    def test_calculate_pay_date_with_config(self):
        """Test that calculate_pay_date uses config values correctly."""
        period_end = date(2025, 12, 31)

        # Saskatchewan: 6 days
        sk_pay_date = calculate_pay_date(period_end, "SK")
        assert sk_pay_date == date(2026, 1, 6)

        # Ontario: 7 days
        on_pay_date = calculate_pay_date(period_end, "ON")
        assert on_pay_date == date(2026, 1, 7)

        # Quebec: 16 days
        qc_pay_date = calculate_pay_date(period_end, "QC")
        assert qc_pay_date == date(2026, 1, 16)

    def test_default_delay_is_used_for_unknown_province(self):
        """Test that DEFAULT_PAY_DATE_DELAY is used for unknown province."""
        assert DEFAULT_PAY_DATE_DELAY == 7

        period_end = date(2025, 12, 31)
        unknown_pay_date = calculate_pay_date(period_end, "XX")
        assert unknown_pay_date == date(2026, 1, 7)  # 7 days

    def test_all_province_delays_match_expected_values(self):
        """Test all province delay configurations match expected values."""
        expected_delays = {
            "NB": 5, "NS": 5, "SK": 6, "ON": 7, "PE": 7, "NL": 7,
            "BC": 8, "AB": 10, "MB": 10, "NT": 10, "NU": 10, "YT": 10,
            "QC": 16
        }

        for province, expected_delay in expected_delays.items():
            assert PAY_DATE_DELAY_DAYS[province] == expected_delay, \
                f"{province} should have {expected_delay} days delay"
