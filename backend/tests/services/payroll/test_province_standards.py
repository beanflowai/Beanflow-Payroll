"""Tests for province employment standards service."""

import pytest

from app.services.payroll.province_standards import (
    OVERTIME_RULES,
    STATUTORY_HOLIDAYS_COUNT,
    VALID_PROVINCE_CODES,
    InvalidProvinceCodeError,
    OvertimeRules,
    ProvinceStandards,
    SickLeaveStandards,
    VacationStandards,
    get_province_standards,
)


class TestConstants:
    """Tests for module constants."""

    def test_valid_province_codes_includes_all_provinces(self):
        """Test all Canadian provinces and territories are included."""
        expected_provinces = {
            "Federal", "AB", "BC", "MB", "NB", "NL", "NS",
            "NT", "NU", "ON", "PE", "QC", "SK", "YT"
        }
        assert VALID_PROVINCE_CODES == expected_provinces

    def test_overtime_rules_for_all_provinces(self):
        """Test overtime rules exist for all valid provinces."""
        for code in VALID_PROVINCE_CODES:
            assert code in OVERTIME_RULES, f"Missing overtime rules for {code}"

    def test_statutory_holidays_for_all_provinces(self):
        """Test statutory holidays exist for all valid provinces."""
        for code in VALID_PROVINCE_CODES:
            assert code in STATUTORY_HOLIDAYS_COUNT, f"Missing holidays for {code}"

    def test_overtime_rules_structure(self):
        """Test overtime rules have required fields."""
        for code, rules in OVERTIME_RULES.items():
            assert "daily_threshold" in rules
            assert "weekly_threshold" in rules
            assert "overtime_rate" in rules
            assert "notes" in rules


class TestOvertimeRules:
    """Tests for specific overtime rules."""

    def test_bc_has_double_time(self):
        """Test BC is the only province with double-time."""
        bc_rules = OVERTIME_RULES["BC"]
        assert bc_rules["double_time_daily"] == 12
        assert bc_rules["daily_threshold"] == 8

    def test_ontario_weekly_only(self):
        """Test Ontario has weekly threshold only."""
        on_rules = OVERTIME_RULES["ON"]
        assert on_rules["daily_threshold"] is None
        assert on_rules["weekly_threshold"] == 44

    def test_federal_weekly_only(self):
        """Test Federal has 40 hour weekly threshold."""
        fed_rules = OVERTIME_RULES["Federal"]
        assert fed_rules["daily_threshold"] is None
        assert fed_rules["weekly_threshold"] == 40

    def test_all_overtime_rates_are_1_5(self):
        """Test all provinces use 1.5x overtime rate."""
        for code, rules in OVERTIME_RULES.items():
            assert rules["overtime_rate"] == 1.5, f"{code} has non-standard OT rate"


class TestStatutoryHolidays:
    """Tests for statutory holiday counts."""

    def test_bc_has_most_holidays(self):
        """Test BC has the most statutory holidays."""
        max_holidays = max(STATUTORY_HOLIDAYS_COUNT.values())
        assert STATUTORY_HOLIDAYS_COUNT["BC"] == max_holidays
        assert max_holidays == 11

    def test_nl_and_ns_have_least(self):
        """Test NL and NS have the fewest holidays."""
        min_holidays = min(STATUTORY_HOLIDAYS_COUNT.values())
        assert min_holidays == 6
        assert STATUTORY_HOLIDAYS_COUNT["NL"] == 6
        assert STATUTORY_HOLIDAYS_COUNT["NS"] == 6

    def test_saskatchewan_has_10_holidays(self):
        """Test SK has 10 statutory holidays."""
        assert STATUTORY_HOLIDAYS_COUNT["SK"] == 10


class TestInvalidProvinceCodeError:
    """Tests for InvalidProvinceCodeError exception."""

    def test_error_message_includes_invalid_code(self):
        """Test error message includes the invalid code."""
        error = InvalidProvinceCodeError("XX")
        assert "XX" in str(error)
        assert "Invalid province code" in str(error)

    def test_error_message_lists_valid_codes(self):
        """Test error message lists valid codes."""
        error = InvalidProvinceCodeError("ZZ")
        error_msg = str(error)
        assert "ON" in error_msg
        assert "BC" in error_msg
        assert "Federal" in error_msg

    def test_error_stores_province_code(self):
        """Test error stores the province code."""
        error = InvalidProvinceCodeError("INVALID")
        assert error.province_code == "INVALID"


class TestGetProvinceStandards:
    """Tests for get_province_standards function."""

    def test_get_ontario_standards(self):
        """Test getting Ontario province standards."""
        standards = get_province_standards("ON")

        assert isinstance(standards, ProvinceStandards)
        assert standards.province_code == "ON"
        assert standards.statutory_holidays_count == 9

        # Check overtime
        assert standards.overtime.daily_threshold is None
        assert standards.overtime.weekly_threshold == 44
        assert standards.overtime.overtime_rate == 1.5

    def test_get_bc_standards(self):
        """Test getting BC province standards with double-time."""
        standards = get_province_standards("BC")

        assert standards.province_code == "BC"
        assert standards.overtime.double_time_daily == 12
        assert standards.overtime.daily_threshold == 8

    def test_get_saskatchewan_standards(self):
        """Test getting Saskatchewan province standards."""
        standards = get_province_standards("SK")

        assert standards.province_code == "SK"
        assert standards.statutory_holidays_count == 10
        assert standards.overtime.weekly_threshold == 40

    def test_get_federal_standards(self):
        """Test getting Federal jurisdiction standards."""
        standards = get_province_standards("Federal")

        assert standards.province_code == "Federal"
        assert standards.statutory_holidays_count == 9
        assert standards.overtime.weekly_threshold == 40

    def test_invalid_province_raises_error(self):
        """Test invalid province code raises InvalidProvinceCodeError."""
        with pytest.raises(InvalidProvinceCodeError) as exc_info:
            get_province_standards("XX")

        assert exc_info.value.province_code == "XX"
        assert "Invalid province code" in str(exc_info.value)

    def test_vacation_standards_structure(self):
        """Test vacation standards has expected structure."""
        standards = get_province_standards("ON")

        assert isinstance(standards.vacation, VacationStandards)
        assert standards.vacation.minimum_weeks > 0
        assert standards.vacation.minimum_rate > 0
        assert "%" in standards.vacation.rate_display

    def test_sick_leave_standards_structure(self):
        """Test sick leave standards has expected structure."""
        standards = get_province_standards("ON")

        assert isinstance(standards.sick_leave, SickLeaveStandards)
        assert isinstance(standards.sick_leave.paid_days, int)
        assert isinstance(standards.sick_leave.unpaid_days, int)
        assert isinstance(standards.sick_leave.waiting_period_days, int)

    def test_overtime_rules_structure(self):
        """Test overtime rules has expected structure."""
        standards = get_province_standards("AB")

        assert isinstance(standards.overtime, OvertimeRules)
        assert standards.overtime.daily_threshold == 8
        assert standards.overtime.weekly_threshold == 44
        assert standards.overtime.overtime_rate == 1.5

    def test_all_provinces_return_valid_standards(self):
        """Test all valid provinces return valid standards."""
        for code in VALID_PROVINCE_CODES:
            standards = get_province_standards(code)
            assert standards.province_code == code
            assert standards.statutory_holidays_count > 0
            assert standards.vacation.minimum_rate > 0
            assert standards.overtime.overtime_rate > 0

    def test_province_name_is_set(self):
        """Test province name is set from vacation config."""
        standards = get_province_standards("SK")
        assert standards.province_name is not None
        assert len(standards.province_name) > 0

    def test_custom_year_parameter(self):
        """Test custom year parameter is passed."""
        # Should not raise even with different year
        standards = get_province_standards("ON", year=2024)
        assert standards.province_code == "ON"

    def test_standards_includes_notes(self):
        """Test overtime rules include notes."""
        standards = get_province_standards("BC")
        assert standards.overtime.notes is not None
        assert len(standards.overtime.notes) > 0
