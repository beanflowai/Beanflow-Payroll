"""
Tests for Holiday Pay Configuration Loading.

Tests:
- Config loading for all provinces
- Formula type validation
- New employee fallback validation
- Province-specific requirements
"""

from decimal import Decimal

from app.services.payroll.holiday_pay_config_loader import get_config


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_get_bc_config(self):
        """Should load BC config from file."""
        config = get_config("BC")
        assert config.province_code == "BC"
        assert config.formula_type == "30_day_average"
        assert config.eligibility.min_employment_days == 30

    def test_get_on_config(self):
        """Should load Ontario config - no 30-day requirement."""
        config = get_config("ON")
        assert config.province_code == "ON"
        assert config.formula_type == "4_week_average"
        assert config.eligibility.min_employment_days == 0
        assert config.eligibility.require_last_first_rule is True

    def test_get_ab_config(self):
        """Should load Alberta config."""
        config = get_config("AB")
        assert config.province_code == "AB"
        assert config.formula_type == "4_week_average_daily"
        assert config.eligibility.min_employment_days == 30

    def test_unknown_province_fallback(self):
        """Unknown province should fall back to BC config."""
        config = get_config("XX")
        assert config.formula_type == "30_day_average"  # BC default


class TestAllProvincesConfigLoading:
    """Tests for loading configs for all provinces and territories."""

    ALL_PROVINCES = [
        "ON", "BC", "AB", "SK", "QC", "MB",
        "NB", "NS", "PE", "NL", "NT", "NU", "YT", "Federal"
    ]

    def test_all_provinces_load_successfully(self):
        """All provinces should load without errors."""
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            assert config is not None, f"Config for {province} should not be None"
            assert config.province_code == province, f"Province code mismatch for {province}"

    def test_all_provinces_have_valid_formula_type(self):
        """All provinces should have a valid formula_type."""
        valid_formulas = {
            "4_week_average",
            "30_day_average",
            "4_week_average_daily",
            "5_percent_28_days",
            "current_period_daily",
            "3_week_average_nl",
            "nt_split_by_compensation",  # NT: hourly→daily rate, salaried→4-week avg
            "yt_split_by_employment",  # YT: regular→30-day avg, casual→irregular hours
            "irregular_hours",  # For casual/irregular workers (percentage of wages)
            "commission",  # For commission-based employees
        }
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            assert config.formula_type in valid_formulas, (
                f"{province} has invalid formula_type: {config.formula_type}"
            )

    def test_all_provinces_have_new_employee_fallback(self):
        """All provinces should have new_employee_fallback defined."""
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            fallback = config.formula_params.new_employee_fallback
            assert fallback in ("pro_rated", "ineligible"), (
                f"{province} should have valid new_employee_fallback, got: {fallback}"
            )

    def test_sk_uses_5_percent_formula(self):
        """SK should use the 5_percent_28_days formula."""
        config = get_config("SK")
        assert config.formula_type == "5_percent_28_days"
        assert config.formula_params.percentage == Decimal("0.05")
        assert config.formula_params.include_vacation_pay is True
        assert config.formula_params.include_previous_holiday_pay is True
        assert config.formula_params.new_employee_fallback == "pro_rated"

    def test_qc_has_no_min_employment_days(self):
        """QC should have min_employment_days = 0."""
        config = get_config("QC")
        assert config.eligibility.min_employment_days == 0
        assert config.formula_params.new_employee_fallback == "pro_rated"

    def test_nb_has_90_day_requirement(self):
        """NB should require 90 days of employment."""
        config = get_config("NB")
        assert config.eligibility.min_employment_days == 90

    def test_pro_rated_provinces(self):
        """Provinces with pro_rated fallback: SK, ON, QC, MB, Federal."""
        pro_rated_provinces = ["SK", "ON", "QC", "MB", "Federal"]
        for province in pro_rated_provinces:
            config = get_config(province)
            assert config.formula_params.new_employee_fallback == "pro_rated", (
                f"{province} should use pro_rated fallback"
            )

    def test_ineligible_provinces(self):
        """Provinces with ineligible fallback: BC, AB, and others."""
        ineligible_provinces = ["BC", "AB", "NB", "NS", "PE", "NL", "NT", "NU", "YT"]
        for province in ineligible_provinces:
            config = get_config(province)
            assert config.formula_params.new_employee_fallback == "ineligible", (
                f"{province} should use ineligible fallback"
            )


class TestFormulaSelection:
    """Tests for correct formula selection by province via config."""

    def test_ontario_uses_4_week_formula(self):
        """Ontario config should specify 4_week_average formula."""
        config = get_config("ON")
        assert config.formula_type == "4_week_average"
        assert config.formula_params.divisor == 20
        assert config.formula_params.include_vacation_pay is True

    def test_alberta_uses_4_week_daily(self):
        """Alberta config should specify 4_week_average_daily formula."""
        config = get_config("AB")
        assert config.formula_type == "4_week_average_daily"

    def test_bc_uses_30_day_average(self):
        """BC config should specify 30_day_average formula."""
        config = get_config("BC")
        assert config.formula_type == "30_day_average"

    def test_unknown_province_uses_bc_default(self):
        """Unknown provinces should fall back to BC formula."""
        config = get_config("XX")
        assert config.formula_type == "30_day_average"
