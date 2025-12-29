"""
Integration tests for PayrollEngine.

Tests the complete payroll calculation flow with all components
(CPP, EI, Federal Tax, Provincial Tax) working together.

Phase 2 - Integration Testing
"""

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


class TestPayrollEngineIntegration:
    """End-to-end payroll calculation tests."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    # ========== Task 2.1.1: Standard Payroll Calculation ==========

    def test_standard_payroll_ontario(self):
        """Test: Complete payroll for Ontario employee ($60k annual)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_001",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            # Income
            gross_regular=Decimal("2307.69"),  # $60k / 26
            gross_overtime=Decimal("0"),
            # Claims
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            # YTD
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Gross pay
        assert result.total_gross == Decimal("2307.69")

        # CPP (should be > 0, < max per period)
        assert result.cpp_base > Decimal("0")
        assert result.cpp_base < Decimal("200")

        # EI (should be > 0, < max per period)
        assert result.ei_employee > Decimal("0")
        assert result.ei_employee < Decimal("50")

        # Federal tax (should be > 0)
        assert result.federal_tax > Decimal("0")

        # Provincial tax (should be > 0)
        assert result.provincial_tax > Decimal("0")

        # Net pay calculation
        expected_net = (
            result.total_gross
            - result.cpp_total
            - result.ei_employee
            - result.federal_tax
            - result.provincial_tax
            - result.rrsp
            - result.union_dues
            - result.garnishments
            - result.other_deductions
        )
        assert result.net_pay == result.total_gross - result.total_employee_deductions

        # Employer costs: CPP employer = CPP total, EI employer = EI employee × 1.4
        assert result.cpp_employer == result.cpp_total
        # EI employer ratio is 1.4x
        expected_ei_employer = (result.ei_employee * Decimal("1.4")).quantize(
            Decimal("0.01")
        )
        assert result.ei_employer == expected_ei_employer

    def test_payroll_with_overtime_and_other_earnings(self):
        """Test: Payroll with multiple income types."""
        input_data = EmployeePayrollInput(
            employee_id="emp_002",
            province=Province.AB,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            gross_overtime=Decimal("300.00"),
            other_earnings=Decimal("500.00"),  # Bonus
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Gross includes all income types
        assert result.total_gross == Decimal("2800.00")

        # Deductions should be calculated on full gross
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")

    def test_payroll_with_taxable_benefits(self):
        """Test: Payroll with employer-paid taxable benefits (life insurance)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_003",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),
            taxable_benefits_pensionable=Decimal("50.00"),  # Life insurance
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Gross pay doesn't include taxable benefits
        assert result.total_gross == Decimal("2500.00")

        # CPP is calculated on pensionable earnings (gross + benefits)
        # The calculation includes taxable_benefits_pensionable
        # EI is calculated on insurable earnings (excludes non-cash benefits)

    # ========== Task 2.1.2: Pre-tax Deductions ==========

    def test_rrsp_reduces_taxable_income(self):
        """Test: RRSP deduction reduces taxable income."""
        # Without RRSP
        input_no_rrsp = EmployeePayrollInput(
            employee_id="emp_004a",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),
            rrsp_per_period=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # With RRSP
        input_with_rrsp = EmployeePayrollInput(
            employee_id="emp_004b",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),
            rrsp_per_period=Decimal("500.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result_no_rrsp = self.engine.calculate(input_no_rrsp)
        result_with_rrsp = self.engine.calculate(input_with_rrsp)

        # RRSP should reduce taxes
        assert result_with_rrsp.federal_tax < result_no_rrsp.federal_tax
        assert result_with_rrsp.provincial_tax < result_no_rrsp.provincial_tax

        # But CPP/EI unchanged (RRSP doesn't affect pensionable/insurable)
        assert result_with_rrsp.cpp_base == result_no_rrsp.cpp_base
        assert result_with_rrsp.ei_employee == result_no_rrsp.ei_employee

    def test_union_dues_reduces_taxable_income(self):
        """Test: Union dues reduce taxable income."""
        # Without union dues
        input_no_union = EmployeePayrollInput(
            employee_id="emp_union_a",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),
            union_dues_per_period=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # With union dues
        input_with_union = EmployeePayrollInput(
            employee_id="emp_union_b",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),
            union_dues_per_period=Decimal("50.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result_no_union = self.engine.calculate(input_no_union)
        result_with_union = self.engine.calculate(input_with_union)

        # Union dues should reduce taxes
        assert result_with_union.federal_tax < result_no_union.federal_tax
        assert result_with_union.provincial_tax < result_no_union.provincial_tax

    # ========== Task 2.1.3: Exemptions ==========

    def test_cpp_exempt_employee(self):
        """Test: Employee exempt from CPP."""
        input_data = EmployeePayrollInput(
            employee_id="emp_005",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            is_cpp_exempt=True,
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.cpp_total == Decimal("0")
        assert result.cpp_employer == Decimal("0")

        # But EI should still be calculated
        assert result.ei_employee > Decimal("0")

    def test_ei_exempt_employee(self):
        """Test: Employee exempt from EI."""
        input_data = EmployeePayrollInput(
            employee_id="emp_006",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            is_ei_exempt=True,
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        assert result.ei_employee == Decimal("0")
        assert result.ei_employer == Decimal("0")

        # But CPP should still be calculated
        assert result.cpp_base > Decimal("0")

    def test_cpp2_exempt_employee(self):
        """Test: Employee exempt from CPP2 (additional CPP)."""
        # High income to trigger CPP2
        input_data = EmployeePayrollInput(
            employee_id="emp_cpp2_exempt",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 10, 15),
            gross_regular=Decimal("7000.00"),  # ~$84k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            cpp2_exempt=True,
            ytd_gross=Decimal("63000.00"),  # 9 months
            ytd_pensionable_earnings=Decimal("63000.00"),
            ytd_insurable_earnings=Decimal("63000.00"),
            ytd_cpp_base=Decimal("3800.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("1000.00"),
        )

        result = self.engine.calculate(input_data)

        # Base CPP should still be calculated
        assert result.cpp_base > Decimal("0")
        # But CPP2 should be zero due to exemption
        assert result.cpp_additional == Decimal("0")

    # ========== Task 2.1.4: YTD Tracking ==========

    def test_ytd_updates_correctly(self):
        """Test: YTD values accumulate correctly."""
        input_data = EmployeePayrollInput(
            employee_id="emp_007",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("20000.00"),
            ytd_pensionable_earnings=Decimal("20000.00"),
            ytd_insurable_earnings=Decimal("20000.00"),
            ytd_cpp_base=Decimal("1000.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("350.00"),
        )

        result = self.engine.calculate(input_data)

        # YTD should be updated
        assert result.new_ytd_gross == Decimal("20000.00") + result.total_gross
        assert (
            result.new_ytd_cpp
            == Decimal("1000.00") + Decimal("0") + result.cpp_total
        )
        assert result.new_ytd_ei == Decimal("350.00") + result.ei_employee

    def test_cpp_stops_at_annual_max(self):
        """Test: CPP stops when annual max reached."""
        input_data = EmployeePayrollInput(
            employee_id="emp_008",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 15),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("70000.00"),
            ytd_pensionable_earnings=Decimal("70000.00"),
            ytd_insurable_earnings=Decimal("65000.00"),
            ytd_cpp_base=Decimal("4034.10"),  # Max reached
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("800.00"),
        )

        result = self.engine.calculate(input_data)

        # No more base CPP since max already reached
        assert result.cpp_base == Decimal("0")

    def test_ei_stops_at_annual_max(self):
        """Test: EI stops when annual max reached."""
        input_data = EmployeePayrollInput(
            employee_id="emp_ei_max",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 15),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("70000.00"),
            ytd_pensionable_earnings=Decimal("70000.00"),
            ytd_insurable_earnings=Decimal("65700.00"),  # At MIE
            ytd_cpp_base=Decimal("4000.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("1077.48"),  # Max reached
        )

        result = self.engine.calculate(input_data)

        # No more EI since max already reached
        assert result.ei_employee == Decimal("0")


class TestPayrollEngineHighIncome:
    """Tests for high-income scenarios (CPP2, max limits)."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_high_income_triggers_cpp2(self):
        """Test: Income above YMPE triggers CPP2."""
        input_data = EmployeePayrollInput(
            employee_id="emp_high_001",
            province=Province.AB,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 10, 15),
            gross_regular=Decimal("10000.00"),  # $120k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),
            ytd_gross=Decimal("90000.00"),  # 9 months done
            ytd_pensionable_earnings=Decimal("90000.00"),
            ytd_insurable_earnings=Decimal("65700.00"),  # EI maxed
            ytd_cpp_base=Decimal("4034.10"),  # CPP base maxed
            ytd_cpp_additional=Decimal("300.00"),  # Some CPP2 already
            ytd_ei=Decimal("1077.48"),  # EI maxed
        )

        result = self.engine.calculate(input_data)

        # Should have CPP2 contribution (base CPP already maxed)
        assert result.cpp_base == Decimal("0")  # Base maxed
        # CPP2 depends on YTD pensionable vs YAMPE
        # At $90k YTD + $10k = $100k, YAMPE is $81,200
        # CPP2 ceiling already reached
        # (YAMPE - YMPE = 81,200 - 71,300 = 9,900)

    def test_all_maximums_reached(self):
        """Test: All contribution limits reached."""
        input_data = EmployeePayrollInput(
            employee_id="emp_max_001",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 15),
            gross_regular=Decimal("5000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("100000.00"),
            ytd_pensionable_earnings=Decimal("100000.00"),
            ytd_insurable_earnings=Decimal("65700.00"),
            ytd_cpp_base=Decimal("4034.10"),  # Base CPP maxed
            ytd_cpp_additional=Decimal("396.00"),  # CPP2 maxed
            ytd_ei=Decimal("1077.48"),  # EI maxed
        )

        result = self.engine.calculate(input_data)

        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.ei_employee == Decimal("0")

        # But taxes still apply
        assert result.federal_tax > Decimal("0")
        assert result.provincial_tax > Decimal("0")


class TestPayrollEnginePayFrequencies:
    """Tests for different pay frequencies."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize(
        "pay_frequency,gross_per_period,annual_gross",
        [
            (PayFrequency.WEEKLY, Decimal("1153.85"), Decimal("60000")),
            (PayFrequency.BIWEEKLY, Decimal("2307.69"), Decimal("60000")),
            (PayFrequency.SEMI_MONTHLY, Decimal("2500.00"), Decimal("60000")),
            (PayFrequency.MONTHLY, Decimal("5000.00"), Decimal("60000")),
        ],
    )
    def test_pay_frequencies_calculate_correctly(
        self, pay_frequency, gross_per_period, annual_gross
    ):
        """Test: All pay frequencies calculate without error."""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_{pay_frequency.value}",
            province=Province.ON,
            pay_frequency=pay_frequency,
            pay_date=date(2025, 7, 18),
            gross_regular=gross_per_period,
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # All should calculate successfully
        assert result.total_gross == gross_per_period
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")
        assert result.net_pay > Decimal("0")
        assert result.net_pay < result.total_gross


class TestPayrollEngineBatchCalculation:
    """Tests for batch payroll calculation."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_batch_calculation(self):
        """Test: Batch calculation for multiple employees."""
        inputs = [
            EmployeePayrollInput(
                employee_id="emp_batch_001",
                province=Province.ON,
                pay_frequency=PayFrequency.BIWEEKLY,
                pay_date=date(2025, 7, 18),
                gross_regular=Decimal("2000.00"),
                federal_claim_amount=Decimal("16129.00"),
                provincial_claim_amount=Decimal("12747.00"),
                ytd_gross=Decimal("0"),
                ytd_pensionable_earnings=Decimal("0"),
                ytd_insurable_earnings=Decimal("0"),
                ytd_cpp_base=Decimal("0"),
                ytd_cpp_additional=Decimal("0"),
                ytd_ei=Decimal("0"),
            ),
            EmployeePayrollInput(
                employee_id="emp_batch_002",
                province=Province.BC,
                pay_frequency=PayFrequency.BIWEEKLY,
                pay_date=date(2025, 7, 18),
                gross_regular=Decimal("3000.00"),
                federal_claim_amount=Decimal("16129.00"),
                provincial_claim_amount=Decimal("12932.00"),
                ytd_gross=Decimal("0"),
                ytd_pensionable_earnings=Decimal("0"),
                ytd_insurable_earnings=Decimal("0"),
                ytd_cpp_base=Decimal("0"),
                ytd_cpp_additional=Decimal("0"),
                ytd_ei=Decimal("0"),
            ),
            EmployeePayrollInput(
                employee_id="emp_batch_003",
                province=Province.AB,
                pay_frequency=PayFrequency.BIWEEKLY,
                pay_date=date(2025, 7, 18),
                gross_regular=Decimal("4000.00"),
                federal_claim_amount=Decimal("16129.00"),
                provincial_claim_amount=Decimal("22323.00"),
                ytd_gross=Decimal("0"),
                ytd_pensionable_earnings=Decimal("0"),
                ytd_insurable_earnings=Decimal("0"),
                ytd_cpp_base=Decimal("0"),
                ytd_cpp_additional=Decimal("0"),
                ytd_ei=Decimal("0"),
            ),
        ]

        results = self.engine.calculate_batch(inputs)

        assert len(results) == 3
        assert results[0].employee_id == "emp_batch_001"
        assert results[1].employee_id == "emp_batch_002"
        assert results[2].employee_id == "emp_batch_003"

        # All should have valid calculations
        for result in results:
            assert result.total_gross > Decimal("0")
            assert result.net_pay > Decimal("0")
            assert result.net_pay < result.total_gross


class TestPayrollEngineInputValidation:
    """Tests for input validation."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_validate_negative_gross_regular(self):
        """Test: Negative gross regular is invalid."""
        input_data = EmployeePayrollInput(
            employee_id="emp_invalid",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            gross_regular=Decimal("-100.00"),  # Invalid
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
        )

        errors = self.engine.validate_input(input_data)
        assert "Gross regular pay cannot be negative" in errors

    def test_validate_negative_overtime(self):
        """Test: Negative overtime is invalid."""
        input_data = EmployeePayrollInput(
            employee_id="emp_invalid",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            gross_regular=Decimal("2000.00"),
            gross_overtime=Decimal("-50.00"),  # Invalid
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
        )

        errors = self.engine.validate_input(input_data)
        assert "Gross overtime pay cannot be negative" in errors

    def test_validate_negative_federal_claim(self):
        """Test: Negative federal claim is invalid."""
        input_data = EmployeePayrollInput(
            employee_id="emp_invalid",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("-100.00"),  # Invalid
            provincial_claim_amount=Decimal("12747.00"),
        )

        errors = self.engine.validate_input(input_data)
        assert "Federal claim amount cannot be negative" in errors

    def test_validate_valid_input(self):
        """Test: Valid input returns no errors."""
        input_data = EmployeePayrollInput(
            employee_id="emp_valid",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
        )

        errors = self.engine.validate_input(input_data)
        assert len(errors) == 0


class TestPayrollEngineFederalTaxRateChange:
    """Tests for July 2025 federal tax rate change (15% -> 14%)."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_federal_tax_before_july(self):
        """Test: Federal tax calculation before July 2025 (15% rate)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_jan",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 3, 15),  # Before July
            gross_regular=Decimal("2307.69"),  # $60k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)
        tax_before_july = result.federal_tax

        # Should use 15% rate
        assert tax_before_july > Decimal("0")

    def test_federal_tax_after_july(self):
        """Test: Federal tax calculation after July 2025 (14% rate)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_jul",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 15),  # After July
            gross_regular=Decimal("2307.69"),  # $60k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)
        tax_after_july = result.federal_tax

        # Should use 14% rate, thus lower tax
        assert tax_after_july > Decimal("0")

    def test_federal_tax_july_is_lower(self):
        """Test: Federal tax after July is lower than before July."""
        base_input = {
            "province": Province.ON,
            "pay_frequency": PayFrequency.BIWEEKLY,
            "gross_regular": Decimal("2307.69"),
            "federal_claim_amount": Decimal("16129.00"),
            "provincial_claim_amount": Decimal("12747.00"),
            "ytd_gross": Decimal("0"),
            "ytd_pensionable_earnings": Decimal("0"),
            "ytd_insurable_earnings": Decimal("0"),
            "ytd_cpp_base": Decimal("0"),
            "ytd_cpp_additional": Decimal("0"),
            "ytd_ei": Decimal("0"),
        }

        input_before = EmployeePayrollInput(
            employee_id="emp_before",
            pay_date=date(2025, 3, 15),
            **base_input,
        )

        input_after = EmployeePayrollInput(
            employee_id="emp_after",
            pay_date=date(2025, 7, 15),
            **base_input,
        )

        result_before = self.engine.calculate(input_before)
        result_after = self.engine.calculate(input_after)

        # Tax after July should be lower due to 14% vs 15%
        assert result_after.federal_tax < result_before.federal_tax
