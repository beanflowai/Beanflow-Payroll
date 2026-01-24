"""Pure Function Tests for Holiday Pay Formulas.

These tests verify mathematical correctness of holiday pay formulas
WITHOUT database mocks or complex setup. They complement integration tests
by ensuring the underlying math is correct.

Purpose:
- Validate formula calculations are mathematically correct
- Provide quick, isolated tests for formula logic
- Document expected formula behavior with clear examples

IMPORTANT: These are NOT tests of the implementation - they validate
the expected mathematical outcomes. The integration tests in
test_tier1_major_provinces.py verify the actual implementation.
"""

from decimal import Decimal

import pytest


# =============================================================================
# Saskatchewan 5% Formula
# =============================================================================


class TestSK5PercentPure:
    """Pure math tests for Saskatchewan 5% formula.

    Formula: base × 5%
    Base = wages + vacation_pay + previous_holiday_pay (past 28 days)
    Reference: Saskatchewan Employment Act s.42
    """

    @pytest.mark.parametrize("base,expected", [
        (Decimal("2800.00"), Decimal("140.00")),     # Standard full-time
        (Decimal("60.00"), Decimal("3.00")),          # Minimal hours
        (Decimal("0.00"), Decimal("0.00")),           # Zero wages
        (Decimal("2080.00"), Decimal("104.00")),      # With vacation
        (Decimal("2616.00"), Decimal("130.80")),      # Complex (wages + vacation + holiday)
        (Decimal("720.00"), Decimal("36.00")),        # New employee
    ])
    def test_5_percent_formula_math(self, base, expected):
        """Verify 5% calculation is mathematically correct."""
        percentage = Decimal("0.05")
        result = base * percentage
        assert result == expected, f"Base ${base} × 5% should be ${expected}, got ${result}"

    def test_5_percent_with_components(self):
        """Verify 5% formula with all three components.

        Case: SK_WITH_PREVIOUS_HOLIDAY_PAY
        Wages: $2,400 + Vacation: $96 + Previous Holiday: $120 = $2,616
        $2,616 × 5% = $130.80
        """
        wages = Decimal("2400.00")
        vacation_pay = Decimal("96.00")
        previous_holiday_pay = Decimal("120.00")
        percentage = Decimal("0.05")

        base = wages + vacation_pay + previous_holiday_pay
        expected = Decimal("130.80")

        result = base * percentage

        assert result == expected, f"Expected ${expected}, got ${result}"
        assert base == Decimal("2616.00"), f"Base should be $2616.00, got ${base}"

    def test_5_percent_rounding(self):
        """Verify rounding behavior for 5% formula.

        Formula should use standard decimal rounding (banker's rounding).
        """
        # Case that would produce many decimal places
        wages = Decimal("1234.56")
        percentage = Decimal("0.05")

        result = wages * percentage
        expected = Decimal("61.7280")  # Exact result

        assert result == expected, f"Expected ${expected}, got ${result}"

        # Rounded to 2 decimal places
        rounded = result.quantize(Decimal("0.01"))
        assert rounded == Decimal("61.73"), f"Rounded should be $61.73, got ${rounded}"


# =============================================================================
# Ontario 4-Week Average Formula
# =============================================================================


class TestON4WeekAveragePure:
    """Pure math tests for Ontario 4-week average formula.

    Formula: (wages + vacation_pay) / 20
    Reference: Ontario Employment Standards Act s.24
    """

    @pytest.mark.parametrize("wages,vacation,expected", [
        (Decimal("2000.00"), Decimal("80.00"), Decimal("104.00")),
        (Decimal("4800.00"), Decimal("288.00"), Decimal("254.40")),
        (Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
        (Decimal("2500.00"), Decimal("0.00"), Decimal("125.00")),
    ])
    def test_4_week_average_formula(self, wages, vacation, expected):
        """Verify (wages + vacation) / 20 calculation."""
        divisor = Decimal("20")
        result = (wages + vacation) / divisor
        assert result == expected, (
            f"(${wages} + ${vacation}) / 20 should be ${expected}, got ${result}"
        )

    def test_ontario_divisor_is_20(self):
        """Verify Ontario uses divisor of 20 (4 weeks × 5 work days)."""
        wages = Decimal("2000.00")
        vacation = Decimal("100.00")

        # Ontario formula: (wages + vacation) / 20
        divisor = Decimal("20")
        result = (wages + vacation) / divisor

        # Cross-check: 20 days = 4 weeks × 5 days/week
        assert result == Decimal("105.00"), f"Expected $105.00, got ${result}"

    def test_ontario_no_overtime(self):
        """Verify Ontario formula excludes overtime.

        Ontario ESA excludes overtime from the calculation base.
        Only regular wages + vacation pay are included.
        """
        regular_wages = Decimal("2000.00")
        overtime_wages = Decimal("300.00")  # Should NOT be included
        vacation_pay = Decimal("80.00")

        # Correct calculation (without overtime)
        base = regular_wages + vacation_pay
        divisor = Decimal("20")
        result = base / divisor

        assert result == Decimal("104.00"), f"Expected $104.00 (no overtime), got ${result}"


# =============================================================================
# Alberta 4-Week Daily Formula
# =============================================================================


class TestAB4WeekDailyPure:
    """Pure math tests for Alberta 4-week daily average formula.

    Formula: wages / days_worked
    Reference: Alberta Employment Standards Code s.25
    """

    @pytest.mark.parametrize("wages,days,expected", [
        (Decimal("4480.00"), 20, Decimal("224.00")),     # Full-time
        (Decimal("2112.00"), 12, Decimal("176.00")),     # Part-time
        (Decimal("3360.00"), 15, Decimal("224.00")),     # Different schedule
        (Decimal("1600.00"), 10, Decimal("160.00")),     # Low hours
    ])
    def test_daily_average_formula(self, wages, days, expected):
        """Verify wages / days_worked calculation."""
        result = wages / Decimal(str(days))
        assert result == expected, f"${wages} / {days} days should be ${expected}, got ${result}"

    def test_ab_part_time_3_days_week(self):
        """Verify Alberta part-time calculation (3 days/week).

        Case: AB_PART_TIME
        4 weeks × 3 days = 12 days worked
        8h × $22/hr × 12 days = $2,112 total wages
        $2,112 / 12 days = $176/day
        """
        hours_per_day = Decimal("8")
        hourly_rate = Decimal("22.00")
        days_per_week = 3
        weeks = 4

        total_days = days_per_week * weeks  # 12 days
        total_wages = hours_per_day * hourly_rate * total_days
        daily_pay = total_wages / Decimal(str(total_days))

        assert total_days == 12, f"Should be 12 days, got {total_days}"
        assert total_wages == Decimal("2112.00"), f"Wages should be $2112, got ${total_wages}"
        assert daily_pay == Decimal("176.00"), f"Daily pay should be $176, got ${daily_pay}"


# =============================================================================
# British Columbia 30-Day Average Formula
# =============================================================================


class TestBC30DayAveragePure:
    """Pure math tests for BC 30-day average formula.

    Formula: total_wages / days_with_wages
    Alternative: default_daily_hours × hourly_rate
    Reference: BC Employment Standards Act s.45
    """

    @pytest.mark.parametrize("wages,days,expected", [
        (Decimal("3000.00"), 15, Decimal("200.00")),     # Standard
        (Decimal("2000.00"), 10, Decimal("200.00")),     # Part-time
        (Decimal("4000.00"), 20, Decimal("200.00")),     # Full month
        (Decimal("1480.00"), 10, Decimal("148.00")),     # Different rate
    ])
    def test_30_day_average_formula(self, wages, days, expected):
        """Verify wages / days_worked calculation."""
        result = wages / Decimal(str(days))
        assert result == expected, f"${wages} / {days} days should be ${expected}, got ${result}"

    def test_bc_default_hours_fallback(self):
        """Verify BC default hours fallback: 8h × hourly_rate.

        For new employees or when no history, BC uses:
        default_daily_hours (8) × hourly_rate
        """
        default_daily_hours = Decimal("8")
        hourly_rate = Decimal("25.00")

        daily_pay = default_daily_hours * hourly_rate

        assert daily_pay == Decimal("200.00"), f"8h × $25 should be $200, got ${daily_pay}"


# =============================================================================
# Manitoba / Quebec 30-Day Average Formula
# =============================================================================


class TestMBQC30DayPure:
    """Pure math tests for MB/QC 30-day average formula.

    Similar to BC but with pro_rated fallback for new employees.
    """

    def test_mb_standard_calculation(self):
        """Verify MB standard: 8h × hourly_rate."""
        default_daily_hours = Decimal("8")
        hourly_rate = Decimal("20.00")

        daily_pay = default_daily_hours * hourly_rate

        assert daily_pay == Decimal("160.00"), f"8h × $20 should be $160, got ${daily_pay}"

    def test_qc_standard_calculation(self):
        """Verify QC standard: 8h × hourly_rate."""
        default_daily_hours = Decimal("8")
        hourly_rate = Decimal("24.00")

        daily_pay = default_daily_hours * hourly_rate

        assert daily_pay == Decimal("192.00"), f"8h × $24 should be $192, got ${daily_pay}"

    def test_qc_pro_rated_fallback(self):
        """Verify QC pro_rated fallback for new employees.

        QC has no minimum employment period, uses pro_rated fallback.
        """
        default_daily_hours = Decimal("8")
        hourly_rate = Decimal("19.00")

        # Pro-rated fallback: 8h × hourly_rate
        daily_pay = default_daily_hours * hourly_rate

        assert daily_pay == Decimal("152.00"), f"8h × $19 should be $152, got ${daily_pay}"


# =============================================================================
# Newfoundland 3-Week Average Formula
# =============================================================================


class TestNL3WeekAveragePure:
    """Pure math tests for Newfoundland 3-week average formula.

    Formula: hourly_rate × (hours_in_3_weeks / 15)
    Reference: Newfoundland Labour Standards Act
    """

    @pytest.mark.parametrize("hourly_rate,hours,expected", [
        (Decimal("20.00"), Decimal("120"), Decimal("160.00")),   # 120h / 15 × $20
        (Decimal("25.00"), Decimal("90"), Decimal("150.00")),    # 90h / 15 × $25
        (Decimal("18.00"), Decimal("60"), Decimal("72.00")),     # 60h / 15 × $18
    ])
    def test_nl_3_week_formula(self, hourly_rate, hours, expected):
        """Verify hourly_rate × (hours / 15) calculation."""
        divisor = Decimal("15")
        result = hourly_rate * (hours / divisor)
        assert result == expected, (
            f"${hourly_rate} × ({hours}h / 15) should be ${expected}, got ${result}"
        )


# =============================================================================
# Commission Employee Formula
# =============================================================================


class TestCommissionFormulaPure:
    """Pure math tests for commission employee formula.

    Formula: total_wages / divisor (e.g., 60 for 1/60)
    Used for: Quebec and Federal commission employees
    """

    @pytest.mark.parametrize("wages,divisor,expected", [
        (Decimal("6000.00"), 60, Decimal("100.00")),     # 1/60 of 12 weeks
        (Decimal("12000.00"), 60, Decimal("200.00")),    # Higher wages
        (Decimal("3000.00"), 60, Decimal("50.00")),      # Lower wages
    ])
    def test_commission_formula(self, wages, divisor, expected):
        """Verify wages / divisor calculation."""
        result = wages / Decimal(str(divisor))
        assert result == expected, (
            f"${wages} / {divisor} should be ${expected}, got ${result}"
        )


# =============================================================================
# Current Period Daily Formula
# =============================================================================


class TestCurrentPeriodDailyPure:
    """Pure math tests for current period daily formula.

    Formula: current_period_gross / work_days_in_period
    Used as fallback for various provinces.
    """

    @pytest.mark.parametrize("gross,work_days,expected", [
        (Decimal("2000.00"), Decimal("10"), Decimal("200.00")),     # Bi-weekly
        (Decimal("1000.00"), Decimal("5"), Decimal("200.00")),      # Weekly
        (Decimal("4333.33"), Decimal("21.67"), Decimal("199.97")),  # Monthly (approx)
    ])
    def test_current_period_formula(self, gross, work_days, expected):
        """Verify gross / work_days calculation."""
        result = gross / work_days
        # Allow small tolerance for monthly calculation
        assert abs(result - expected) < Decimal("0.01"), (
            f"${gross} / {work_days} days should be ~${expected}, got ${result}"
        )

    def test_work_days_by_frequency(self):
        """Verify work days per pay frequency.

        Standard work days:
        - weekly: 5 days
        - bi_weekly: 10 days
        - semi_monthly: 10.83 days (avg)
        - monthly: 21.67 days (avg)
        """
        work_days = {
            "weekly": Decimal("5"),
            "bi_weekly": Decimal("10"),
            "semi_monthly": Decimal("10.83"),
            "monthly": Decimal("21.67"),
        }

        # Verify bi-weekly: $2000 / 10 = $200
        gross = Decimal("2000.00")
        assert gross / work_days["bi_weekly"] == Decimal("200.00")

        # Verify weekly: $1000 / 5 = $200
        gross = Decimal("1000.00")
        assert gross / work_days["weekly"] == Decimal("200.00")


# =============================================================================
# Irregular Hours (Yukon) Formula
# =============================================================================


class TestIrregularHoursPure:
    """Pure math tests for Yukon irregular hours formula.

    Formula: percentage × wages_in_lookback
    Reference: Yukon Employment Standards Act
    """

    @pytest.mark.parametrize("wages,percentage,expected", [
        (Decimal("2000.00"), Decimal("0.10"), Decimal("200.00")),   # 10%
        (Decimal("3500.00"), Decimal("0.10"), Decimal("350.00")),   # Higher wages
        (Decimal("1500.00"), Decimal("0.10"), Decimal("150.00")),   # Lower wages
    ])
    def test_irregular_hours_formula(self, wages, percentage, expected):
        """Verify wages × percentage calculation."""
        result = wages * percentage
        assert result == expected, (
            f"${wages} × {percentage*100}% should be ${expected}, got ${result}"
        )


# =============================================================================
# Premium Pay Formula
# =============================================================================


class TestPremiumPayPure:
    """Pure math tests for premium pay (working on holiday).

    Formula: hours_worked × hourly_rate × premium_rate
    Premium rate: typically 1.5× (time and a half)
    """

    @pytest.mark.parametrize("hours,rate,premium,expected", [
        (Decimal("8"), Decimal("25.00"), Decimal("1.5"), Decimal("300.00")),
        (Decimal("4"), Decimal("20.00"), Decimal("1.5"), Decimal("120.00")),
        (Decimal("10"), Decimal("30.00"), Decimal("1.5"), Decimal("450.00")),
    ])
    def test_premium_pay_formula(self, hours, rate, premium, expected):
        """Verify hours × rate × premium calculation."""
        result = hours * rate * premium
        assert result == expected, (
            f"{hours}h × ${rate} × {premium}× should be ${expected}, got ${result}"
        )

    def test_total_holiday_pay(self):
        """Verify total holiday pay = regular + premium.

        Example: Employee works 4 hours on holiday
        Regular holiday pay: $200 (calculated normally)
        Premium: 4h × $25 × 1.5 = $150
        Total: $200 + $150 = $350
        """
        regular_pay = Decimal("200.00")
        hours_worked = Decimal("4")
        hourly_rate = Decimal("25.00")
        premium_rate = Decimal("1.5")

        premium_pay = hours_worked * hourly_rate * premium_rate
        total = regular_pay + premium_pay

        assert premium_pay == Decimal("150.00"), f"Premium should be $150, got ${premium_pay}"
        assert total == Decimal("350.00"), f"Total should be $350, got ${total}"
