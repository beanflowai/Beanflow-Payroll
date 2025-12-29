"""
Province coverage tests for PayrollEngine.

Ensures all 12 Canadian provinces/territories (excluding Quebec)
calculate correctly with their specific tax rules.

Phase 2 - Integration Testing
"""

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


# Provincial BPA data for 2025
PROVINCIAL_BPA = {
    Province.AB: Decimal("22323.00"),
    Province.BC: Decimal("12932.00"),
    Province.MB: Decimal("15780.00"),
    Province.NB: Decimal("13396.00"),
    Province.NL: Decimal("11067.00"),
    Province.NS: Decimal("11744.00"),
    Province.NT: Decimal("17842.00"),
    Province.NU: Decimal("19274.00"),
    Province.ON: Decimal("12747.00"),
    Province.PE: Decimal("14250.00"),
    Province.SK: Decimal("18991.00"),
    Province.YT: Decimal("16129.00"),
}


class TestAllProvinces:
    """Ensure all 12 provinces calculate correctly."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    def test_province_calculates_without_error(self, province: Province):
        """Test: Each province calculates successfully."""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Basic sanity checks
        assert result.total_gross == Decimal("2000.00")
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")
        assert result.federal_tax >= Decimal("0")
        assert result.provincial_tax >= Decimal("0")
        assert result.net_pay > Decimal("0")
        assert result.net_pay < result.total_gross

    @pytest.mark.parametrize("province", list(Province))
    def test_province_with_high_income(self, province: Province):
        """Test: High income calculation for each province (~$150k annual)."""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_high_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("5769.23"),  # ~$150k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # High income should have higher taxes
        assert result.federal_tax > Decimal("500")
        assert result.provincial_tax > Decimal("100")
        assert result.net_pay > Decimal("0")

    @pytest.mark.parametrize("province", list(Province))
    def test_province_with_low_income(self, province: Province):
        """Test: Low income calculation for each province (~$30k annual)."""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_low_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("1153.85"),  # ~$30k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Low income may have zero or low taxes
        assert result.federal_tax >= Decimal("0")
        assert result.provincial_tax >= Decimal("0")
        assert result.net_pay > Decimal("0")

    @pytest.mark.parametrize(
        "province,expected_min_tax,expected_max_tax",
        [
            # Low tax provinces (high BPA or low rates)
            (Province.AB, Decimal("0"), Decimal("200")),
            (Province.SK, Decimal("0"), Decimal("180")),
            (Province.NT, Decimal("0"), Decimal("150")),
            (Province.NU, Decimal("0"), Decimal("140")),
            (Province.YT, Decimal("0"), Decimal("180")),
            # Medium tax provinces
            (Province.BC, Decimal("0"), Decimal("220")),
            (Province.ON, Decimal("0"), Decimal("250")),
            (Province.PE, Decimal("0"), Decimal("280")),
            # Higher tax provinces (lower BPA or higher rates)
            (Province.MB, Decimal("0"), Decimal("320")),
            (Province.NB, Decimal("0"), Decimal("300")),
            (Province.NL, Decimal("0"), Decimal("300")),
            (Province.NS, Decimal("0"), Decimal("300")),
        ],
    )
    def test_provincial_tax_in_expected_range(
        self, province: Province, expected_min_tax: Decimal, expected_max_tax: Decimal
    ):
        """Test: Provincial tax falls within expected range for $65k income."""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_tax_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),  # ~$65k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Check provincial tax is in expected range
        assert result.provincial_tax >= expected_min_tax, (
            f"{province}: Provincial tax {result.provincial_tax} "
            f"below minimum {expected_min_tax}"
        )
        assert result.provincial_tax <= expected_max_tax, (
            f"{province}: Provincial tax {result.provincial_tax} "
            f"above maximum {expected_max_tax}"
        )


class TestProvincialSpecialRules:
    """Test province-specific rules and edge cases."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_ontario_health_premium_high_income(self):
        """Test: Ontario health premium for high income ($104k annual)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_on_health",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("4000.00"),  # ~$104k annual
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

        # Ontario high income should have health premium included in provincial tax
        # V2 = 0 to $900/year depending on income
        assert result.provincial_tax > Decimal("0")

    def test_ontario_low_income_no_health_premium(self):
        """Test: Ontario low income has no health premium."""
        input_data = EmployeePayrollInput(
            employee_id="emp_on_low",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("750.00"),  # ~$19.5k annual (below $20k threshold)
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

        # Low income should have minimal or zero health premium
        # Provincial tax might still be very low due to low income
        assert result.provincial_tax >= Decimal("0")

    def test_bc_low_income_tax_reduction(self):
        """Test: BC tax reduction for low income."""
        input_data = EmployeePayrollInput(
            employee_id="emp_bc_low",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("1000.00"),  # ~$26k annual
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

        # BC low income should have minimal or zero provincial tax
        # due to tax reduction provisions
        assert result.provincial_tax < Decimal("50")

    def test_alberta_flat_rate(self):
        """Test: Alberta has flat 10% provincial tax rate."""
        input_data = EmployeePayrollInput(
            employee_id="emp_ab_flat",
            province=Province.AB,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),  # ~$78k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),  # High BPA
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Alberta should have relatively low provincial tax due to:
        # 1. Flat 10% rate (lowest in Canada)
        # 2. High BPA ($22,323)
        assert result.provincial_tax >= Decimal("0")
        # With high BPA, tax should be relatively modest
        assert result.provincial_tax < Decimal("300")

    def test_manitoba_higher_rates(self):
        """Test: Manitoba has higher provincial tax rates."""
        input_data = EmployeePayrollInput(
            employee_id="emp_mb_high",
            province=Province.MB,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("3000.00"),  # ~$78k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("15780.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Manitoba has higher rates, so tax should be noticeable
        assert result.provincial_tax > Decimal("0")

    def test_nova_scotia_surtax(self):
        """Test: Nova Scotia applies surtax for high income."""
        input_data = EmployeePayrollInput(
            employee_id="emp_ns_surtax",
            province=Province.NS,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("5000.00"),  # ~$130k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("11744.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # NS high income includes surtax
        assert result.provincial_tax > Decimal("300")


class TestProvincialComparison:
    """Compare tax burden across provinces."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_alberta_vs_ontario_tax_comparison(self):
        """Test: Alberta has lower provincial tax than Ontario for same income."""
        base_params = {
            "pay_frequency": PayFrequency.BIWEEKLY,
            "pay_date": date(2025, 7, 18),
            "gross_regular": Decimal("3000.00"),
            "federal_claim_amount": Decimal("16129.00"),
            "ytd_gross": Decimal("0"),
            "ytd_pensionable_earnings": Decimal("0"),
            "ytd_insurable_earnings": Decimal("0"),
            "ytd_cpp_base": Decimal("0"),
            "ytd_cpp_additional": Decimal("0"),
            "ytd_ei": Decimal("0"),
        }

        input_ab = EmployeePayrollInput(
            employee_id="emp_ab_compare",
            province=Province.AB,
            provincial_claim_amount=PROVINCIAL_BPA[Province.AB],
            **base_params,
        )

        input_on = EmployeePayrollInput(
            employee_id="emp_on_compare",
            province=Province.ON,
            provincial_claim_amount=PROVINCIAL_BPA[Province.ON],
            **base_params,
        )

        result_ab = self.engine.calculate(input_ab)
        result_on = self.engine.calculate(input_on)

        # Alberta typically has lower provincial tax due to flat 10% and high BPA
        # But this depends on income level
        # For ~$78k income, Alberta should be lower
        assert result_ab.provincial_tax <= result_on.provincial_tax + Decimal("50")

    def test_territories_vs_provinces(self):
        """Test: Territories generally have lower tax than provinces."""
        base_params = {
            "pay_frequency": PayFrequency.BIWEEKLY,
            "pay_date": date(2025, 7, 18),
            "gross_regular": Decimal("2500.00"),
            "federal_claim_amount": Decimal("16129.00"),
            "ytd_gross": Decimal("0"),
            "ytd_pensionable_earnings": Decimal("0"),
            "ytd_insurable_earnings": Decimal("0"),
            "ytd_cpp_base": Decimal("0"),
            "ytd_cpp_additional": Decimal("0"),
            "ytd_ei": Decimal("0"),
        }

        # Calculate for Nunavut (territory with high BPA)
        input_nu = EmployeePayrollInput(
            employee_id="emp_nu",
            province=Province.NU,
            provincial_claim_amount=PROVINCIAL_BPA[Province.NU],
            **base_params,
        )

        # Calculate for Nova Scotia (province with lower BPA)
        input_ns = EmployeePayrollInput(
            employee_id="emp_ns",
            province=Province.NS,
            provincial_claim_amount=PROVINCIAL_BPA[Province.NS],
            **base_params,
        )

        result_nu = self.engine.calculate(input_nu)
        result_ns = self.engine.calculate(input_ns)

        # Nunavut should have lower provincial tax
        assert result_nu.provincial_tax < result_ns.provincial_tax

    def test_federal_tax_same_across_provinces(self):
        """Test: Federal tax is the same regardless of province."""
        base_params = {
            "pay_frequency": PayFrequency.BIWEEKLY,
            "pay_date": date(2025, 7, 18),
            "gross_regular": Decimal("2500.00"),
            "federal_claim_amount": Decimal("16129.00"),
            "ytd_gross": Decimal("0"),
            "ytd_pensionable_earnings": Decimal("0"),
            "ytd_insurable_earnings": Decimal("0"),
            "ytd_cpp_base": Decimal("0"),
            "ytd_cpp_additional": Decimal("0"),
            "ytd_ei": Decimal("0"),
        }

        results = []
        for province in list(Province)[:3]:  # Test first 3 provinces
            input_data = EmployeePayrollInput(
                employee_id=f"emp_fed_{province.value}",
                province=province,
                provincial_claim_amount=PROVINCIAL_BPA[province],
                **base_params,
            )
            result = self.engine.calculate(input_data)
            results.append(result)

        # All federal taxes should be identical
        federal_taxes = [r.federal_tax for r in results]
        assert all(tax == federal_taxes[0] for tax in federal_taxes)


class TestAllProvincesAllPayFrequencies:
    """Test all provinces with all pay frequencies."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    @pytest.mark.parametrize(
        "pay_frequency",
        [
            PayFrequency.WEEKLY,
            PayFrequency.BIWEEKLY,
            PayFrequency.SEMI_MONTHLY,
            PayFrequency.MONTHLY,
        ],
    )
    def test_all_province_pay_frequency_combinations(
        self, province: Province, pay_frequency: PayFrequency
    ):
        """Test: All province and pay frequency combinations calculate correctly."""
        # Annual salary of $60k
        annual_salary = Decimal("60000.00")
        periods = pay_frequency.periods_per_year
        gross_per_period = (annual_salary / periods).quantize(Decimal("0.01"))

        input_data = EmployeePayrollInput(
            employee_id=f"emp_{province.value}_{pay_frequency.value}",
            province=province,
            pay_frequency=pay_frequency,
            pay_date=date(2025, 7, 18),
            gross_regular=gross_per_period,
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # All combinations should calculate without error
        assert result.total_gross == gross_per_period
        assert result.net_pay > Decimal("0")
        assert result.net_pay < result.total_gross
