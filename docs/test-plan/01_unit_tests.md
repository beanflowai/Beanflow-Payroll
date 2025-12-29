# Phase 1: Unit Tests

**Duration**: 3-4 days
**Priority**: P0 (Critical)
**Prerequisites**: Payroll calculators implemented

---

## Objectives

Create comprehensive unit tests for all payroll calculators:
1. CPP Calculator (base + CPP2)
2. EI Calculator
3. Federal Tax Calculator
4. Provincial Tax Calculator (12 provinces)

---

## Test File Structure

```
backend/tests/payroll/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_cpp_calculator.py         # Task 1.1
├── test_ei_calculator.py          # Task 1.2
├── test_federal_tax.py            # Task 1.3
└── test_provincial_tax.py         # Task 1.4
```

---

## Task 1.1: CPP Calculator Tests

**File**: `backend/tests/payroll/test_cpp_calculator.py`

### 2025 CPP Parameters (Reference)

| Parameter | Value |
|-----------|-------|
| YMPE | $71,300 |
| YAMPE | $81,200 |
| Basic Exemption | $3,500 |
| Base CPP Rate | 5.95% |
| CPP2 Rate (additional) | 4.00% |
| Max Base CPP | $4,034.10 |
| Max CPP2 | $396.00 |

### Test Cases

```python
# backend/tests/payroll/test_cpp_calculator.py

import pytest
from decimal import Decimal
from app.services.payroll.cpp_calculator import CPPCalculator


class TestCPPCalculator:
    """CPP contribution calculation tests"""

    # ========== Setup ==========

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)"""
        self.calc = CPPCalculator(year=2025, pay_periods_per_year=26)

    # ========== Task 1.1.1: Base CPP Tests ==========

    def test_base_cpp_standard_income(self):
        """Test: Standard income below YMPE"""
        # $2,000/period × 26 = $52,000 annual (below YMPE $71,300)
        result = self.calc.calculate(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable=Decimal("0"),
            ytd_cpp=Decimal("0")
        )

        # Expected: (2000 - 3500/26) × 5.95%
        # = (2000 - 134.62) × 0.0595 = 110.90
        assert result.base_cpp > Decimal("100")
        assert result.base_cpp < Decimal("130")
        assert result.cpp2 == Decimal("0")  # No CPP2 below YMPE

    def test_base_cpp_low_income(self):
        """Test: Income below basic exemption - should be $0"""
        # $100/period is below exemption threshold
        result = self.calc.calculate(
            pensionable_earnings=Decimal("100.00"),
            ytd_pensionable=Decimal("0"),
            ytd_cpp=Decimal("0")
        )

        assert result.base_cpp == Decimal("0")

    def test_base_cpp_max_reached(self):
        """Test: YTD already at maximum - no more deduction"""
        result = self.calc.calculate(
            pensionable_earnings=Decimal("5000.00"),
            ytd_pensionable=Decimal("70000"),
            ytd_cpp=Decimal("4034.10")  # Max already reached
        )

        assert result.base_cpp == Decimal("0")

    def test_base_cpp_partial_max(self):
        """Test: Partial deduction when approaching max"""
        # YTD CPP is close to max, should only deduct remaining
        result = self.calc.calculate(
            pensionable_earnings=Decimal("3000.00"),
            ytd_pensionable=Decimal("68000"),
            ytd_cpp=Decimal("4000.00")  # $34.10 remaining to max
        )

        assert result.base_cpp <= Decimal("34.10")

    # ========== Task 1.1.2: CPP2 (Additional) Tests ==========

    def test_cpp2_income_above_ympe(self):
        """Test: CPP2 kicks in for income above YMPE"""
        # High income that exceeds YMPE
        result = self.calc.calculate(
            pensionable_earnings=Decimal("4000.00"),  # ~$104k annual
            ytd_pensionable=Decimal("75000"),  # Already past YMPE
            ytd_cpp=Decimal("4034.10"),  # Base CPP maxed
            ytd_cpp2=Decimal("0")
        )

        assert result.cpp2 > Decimal("0")

    def test_cpp2_max_reached(self):
        """Test: CPP2 stops at $396 maximum"""
        result = self.calc.calculate(
            pensionable_earnings=Decimal("5000.00"),
            ytd_pensionable=Decimal("80000"),
            ytd_cpp=Decimal("4034.10"),
            ytd_cpp2=Decimal("396.00")  # CPP2 max reached
        )

        assert result.cpp2 == Decimal("0")

    def test_cpp2_exemption(self):
        """Test: Employee with CPP2 exemption (CPT30)"""
        result = self.calc.calculate(
            pensionable_earnings=Decimal("4000.00"),
            ytd_pensionable=Decimal("75000"),
            ytd_cpp=Decimal("4034.10"),
            cpp2_exempt=True
        )

        assert result.cpp2 == Decimal("0")

    # ========== Task 1.1.3: Pay Frequency Tests ==========

    @pytest.mark.parametrize("periods,gross,expected_min", [
        (52, Decimal("1000"), Decimal("50")),    # Weekly
        (26, Decimal("2000"), Decimal("100")),   # Bi-weekly
        (24, Decimal("2167"), Decimal("110")),   # Semi-monthly
        (12, Decimal("5000"), Decimal("250")),   # Monthly
    ])
    def test_different_pay_frequencies(self, periods, gross, expected_min):
        """Test: CPP calculation with different pay frequencies"""
        calc = CPPCalculator(year=2025, pay_periods_per_year=periods)
        result = calc.calculate(
            pensionable_earnings=gross,
            ytd_pensionable=Decimal("0"),
            ytd_cpp=Decimal("0")
        )

        assert result.base_cpp >= expected_min

    # ========== Task 1.1.4: Employer Contribution ==========

    def test_employer_cpp_matches_employee(self):
        """Test: Employer CPP equals employee CPP"""
        result = self.calc.calculate(
            pensionable_earnings=Decimal("2500.00"),
            ytd_pensionable=Decimal("0"),
            ytd_cpp=Decimal("0")
        )

        assert result.employer_cpp == result.base_cpp + result.cpp2


# ========== PDOC Validation Cases ==========

class TestCPPPDOCValidation:
    """Test cases validated against CRA PDOC"""

    def setup_method(self):
        self.calc = CPPCalculator(year=2025, pay_periods_per_year=26)

    def test_pdoc_case_ontario_60k(self):
        """
        PDOC Validation Case: Ontario, $60k annual, bi-weekly

        PDOC Input:
        - Province: Ontario
        - Gross: $2,307.69
        - Pay periods: 26
        - YTD: $0

        PDOC Expected: CPP = $XXX.XX (fill after PDOC run)
        """
        result = self.calc.calculate(
            pensionable_earnings=Decimal("2307.69"),
            ytd_pensionable=Decimal("0"),
            ytd_cpp=Decimal("0")
        )

        # TODO: Update with actual PDOC value
        expected_cpp = Decimal("119.23")  # Placeholder
        assert abs(result.base_cpp - expected_cpp) < Decimal("1.00")
```

---

## Task 1.2: EI Calculator Tests

**File**: `backend/tests/payroll/test_ei_calculator.py`

### 2025 EI Parameters (Reference)

| Parameter | Value |
|-----------|-------|
| MIE (Maximum Insurable Earnings) | $65,700 |
| Employee Rate | 1.64% |
| Max Employee Premium | $1,077.48 |
| Employer Multiplier | 1.4× |
| Max Employer Premium | $1,508.47 |

### Test Cases

```python
# backend/tests/payroll/test_ei_calculator.py

import pytest
from decimal import Decimal
from app.services.payroll.ei_calculator import EICalculator


class TestEICalculator:
    """EI premium calculation tests"""

    def setup_method(self):
        self.calc = EICalculator(year=2025, pay_periods_per_year=26)

    # ========== Task 1.2.1: Basic EI Tests ==========

    def test_ei_standard_income(self):
        """Test: Standard income below MIE"""
        result = self.calc.calculate(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        # Expected: 2000 × 1.64% = $32.80
        assert result.employee_ei == Decimal("32.80")

    def test_ei_max_reached(self):
        """Test: YTD already at maximum"""
        result = self.calc.calculate(
            insurable_earnings=Decimal("3000.00"),
            ytd_insurable=Decimal("65700"),
            ytd_ei=Decimal("1077.48")  # Max reached
        )

        assert result.employee_ei == Decimal("0")

    def test_ei_partial_max(self):
        """Test: Partial deduction when approaching max"""
        result = self.calc.calculate(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable=Decimal("64000"),
            ytd_ei=Decimal("1050.00")  # $27.48 remaining
        )

        assert result.employee_ei <= Decimal("27.48")

    def test_ei_exemption(self):
        """Test: EI exempt employee"""
        result = self.calc.calculate(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable=Decimal("0"),
            ytd_ei=Decimal("0"),
            ei_exempt=True
        )

        assert result.employee_ei == Decimal("0")

    # ========== Task 1.2.2: Employer Premium ==========

    def test_employer_ei_multiplier(self):
        """Test: Employer EI is 1.4× employee"""
        result = self.calc.calculate(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        expected_employer = result.employee_ei * Decimal("1.4")
        assert result.employer_ei == expected_employer

    # ========== Task 1.2.3: Pay Frequency Tests ==========

    @pytest.mark.parametrize("periods,gross,expected", [
        (52, Decimal("1000"), Decimal("16.40")),   # Weekly
        (26, Decimal("2000"), Decimal("32.80")),   # Bi-weekly
        (12, Decimal("5000"), Decimal("82.00")),   # Monthly
    ])
    def test_different_pay_frequencies(self, periods, gross, expected):
        """Test: EI with different pay frequencies"""
        calc = EICalculator(year=2025, pay_periods_per_year=periods)
        result = calc.calculate(
            insurable_earnings=gross,
            ytd_insurable=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        assert result.employee_ei == expected
```

---

## Task 1.3: Federal Tax Calculator Tests

**File**: `backend/tests/payroll/test_federal_tax.py`

### 2025 Federal Parameters (Reference)

| Parameter | Value |
|-----------|-------|
| BPAF (Basic Personal Amount) | $16,129 |
| CEA (Canada Employment Amount) | $1,471 |
| Lowest Tax Rate (Jul 2025+) | 14% |
| Tax Brackets | See T4127 Table 8.1 |

### Test Cases

```python
# backend/tests/payroll/test_federal_tax.py

import pytest
from decimal import Decimal
from datetime import date
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator


class TestFederalTaxCalculator:
    """Federal income tax calculation tests"""

    def setup_method(self):
        self.calc = FederalTaxCalculator(
            year=2025,
            pay_periods_per_year=26,
            pay_date=date(2025, 7, 15)  # After rate change
        )

    # ========== Task 1.3.1: Annual Taxable Income (Factor A) ==========

    def test_annual_taxable_income_simple(self):
        """Test: Basic annualization"""
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2000.00"),
            rrsp_per_period=Decimal("0"),
            union_dues_per_period=Decimal("0"),
            f2_per_period=Decimal("0"),
            cpp2_per_period=Decimal("0")
        )

        # A = 26 × 2000 = 52,000
        assert A == Decimal("52000.00")

    def test_annual_taxable_income_with_deductions(self):
        """Test: Annualization with pre-tax deductions"""
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2500.00"),
            rrsp_per_period=Decimal("200.00"),
            union_dues_per_period=Decimal("50.00"),
            f2_per_period=Decimal("20.00"),
            cpp2_per_period=Decimal("10.00")
        )

        # A = 26 × (2500 - 200 - 50 - 20 - 10) = 26 × 2220 = 57,720
        assert A == Decimal("57720.00")

    # ========== Task 1.3.2: Tax Credit Tests (K1, K2, K4) ==========

    def test_k1_personal_credit(self):
        """Test: K1 calculation from TD1 claim"""
        k1 = self.calc.calculate_k1(tc=Decimal("16129.00"))

        # K1 = 0.14 × 16129 = 2258.06
        assert k1 == Decimal("2258.06")

    def test_k2_cpp_ei_credit(self):
        """Test: K2 from CPP/EI contributions"""
        k2 = self.calc.calculate_k2(
            cpp_per_period=Decimal("110.00"),
            ei_per_period=Decimal("35.00")
        )

        # K2 involves CPP base rate adjustment (4.95%/5.95%)
        assert k2 > Decimal("300")
        assert k2 < Decimal("500")

    def test_k4_employment_credit_full(self):
        """Test: K4 for income above CEA"""
        k4 = self.calc.calculate_k4(annual_income=Decimal("60000.00"))

        # K4 = 0.14 × min(A, 1471) = 0.14 × 1471 = 205.94
        assert k4 == Decimal("205.94")

    def test_k4_employment_credit_low_income(self):
        """Test: K4 capped at actual income"""
        k4 = self.calc.calculate_k4(annual_income=Decimal("1000.00"))

        # K4 = 0.14 × min(1000, 1471) = 0.14 × 1000 = 140.00
        assert k4 == Decimal("140.00")

    # ========== Task 1.3.3: Tax Bracket Tests ==========

    @pytest.mark.parametrize("income,expected_rate", [
        (Decimal("40000"), Decimal("0.14")),   # Bracket 1
        (Decimal("60000"), Decimal("0.205")),  # Bracket 2
        (Decimal("120000"), Decimal("0.26")),  # Bracket 3
        (Decimal("180000"), Decimal("0.29")),  # Bracket 4
        (Decimal("300000"), Decimal("0.33")),  # Bracket 5
    ])
    def test_tax_brackets(self, income, expected_rate):
        """Test: Correct tax bracket selection"""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=income,
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35")
        )

        assert result["tax_rate"] == expected_rate

    # ========== Task 1.3.4: Mid-Year Rate Change ==========

    def test_jan_to_jun_rate(self):
        """Test: 15% rate before July 2025"""
        calc_jan = FederalTaxCalculator(
            year=2025,
            pay_periods_per_year=26,
            pay_date=date(2025, 3, 15)
        )

        result = calc_jan.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35")
        )

        assert result["tax_rate"] == Decimal("0.15")

    def test_jul_onwards_rate(self):
        """Test: 14% rate from July 2025"""
        calc_jul = FederalTaxCalculator(
            year=2025,
            pay_periods_per_year=26,
            pay_date=date(2025, 8, 15)
        )

        result = calc_jul.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35")
        )

        assert result["tax_rate"] == Decimal("0.14")
```

---

## Task 1.4: Provincial Tax Calculator Tests

**File**: `backend/tests/payroll/test_provincial_tax.py`

### Test Cases

```python
# backend/tests/payroll/test_provincial_tax.py

import pytest
from decimal import Decimal
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator
from app.models.payroll import Province


class TestProvincialTaxCalculator:
    """Provincial/territorial tax calculation tests"""

    # ========== Task 1.4.1: All Provinces Smoke Test ==========

    @pytest.mark.parametrize("province", [
        Province.AB, Province.BC, Province.MB, Province.NB,
        Province.NL, Province.NS, Province.NT, Province.NU,
        Province.ON, Province.PE, Province.SK, Province.YT
    ])
    def test_all_provinces_calculate(self, province):
        """Test: All provinces calculate without errors"""
        calc = ProvincialTaxCalculator(
            province=province,
            year=2025,
            pay_periods_per_year=26
        )

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=calc.get_basic_personal_amount(),
            cpp_per_period=Decimal("110"),
            ei_per_period=Decimal("35")
        )

        assert result["annual_provincial_tax"] >= Decimal("0")
        assert result["provincial_tax_per_period"] >= Decimal("0")

    # ========== Task 1.4.2: Ontario Surtax Tests ==========

    def test_ontario_no_surtax(self):
        """Test: Ontario low income - no surtax"""
        calc = ProvincialTaxCalculator(Province.ON, 2025, 26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("50000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35")
        )

        assert result.get("surtax", Decimal("0")) == Decimal("0")

    def test_ontario_with_surtax(self):
        """Test: Ontario high income - triggers surtax"""
        calc = ProvincialTaxCalculator(Province.ON, 2025, 26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("150000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("155"),
            ei_per_period=Decimal("41")
        )

        # Ontario surtax: 20% on tax > $5,554, 36% on tax > $7,108
        assert result.get("surtax", Decimal("0")) > Decimal("0")

    # ========== Task 1.4.3: BC Tax Reduction Tests ==========

    def test_bc_tax_reduction_low_income(self):
        """Test: BC low income gets tax reduction (Factor S)"""
        calc = ProvincialTaxCalculator(Province.BC, 2025, 26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("25000"),
            total_claim_amount=Decimal("12932"),
            cpp_per_period=Decimal("50"),
            ei_per_period=Decimal("15")
        )

        # BC S = $521 - (A - threshold) × reduction_rate
        assert "tax_reduction" in result or result["annual_provincial_tax"] < Decimal("500")

    # ========== Task 1.4.4: Dynamic BPA Tests ==========

    def test_manitoba_dynamic_bpa_low_income(self):
        """Test: Manitoba full BPA for low income"""
        calc = ProvincialTaxCalculator(Province.MB, 2025, 26)

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("40000"),
            net_income=Decimal("40000")
        )

        # MB full BPA = $15,780 (2025)
        assert bpa == Decimal("15780.00")

    def test_manitoba_dynamic_bpa_high_income(self):
        """Test: Manitoba reduced BPA for high income"""
        calc = ProvincialTaxCalculator(Province.MB, 2025, 26)

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("200000"),
            net_income=Decimal("200000")
        )

        # High income reduces BPA
        assert bpa < Decimal("15780.00")

    def test_nova_scotia_dynamic_bpa(self):
        """Test: Nova Scotia two-tier BPA"""
        calc = ProvincialTaxCalculator(Province.NS, 2025, 26)

        # Below threshold
        bpa_low = calc.get_basic_personal_amount(Decimal("20000"))
        assert bpa_low == Decimal("11744.00")

        # Above threshold
        bpa_high = calc.get_basic_personal_amount(Decimal("80000"))
        assert bpa_high == Decimal("8744.00")

    def test_yukon_dynamic_bpa(self):
        """Test: Yukon matches federal BPA formula"""
        calc = ProvincialTaxCalculator(Province.YT, 2025, 26)

        bpa = calc.get_basic_personal_amount(Decimal("60000"))

        # YT follows federal BPA rules
        assert bpa >= Decimal("14000")

    # ========== Task 1.4.5: Alberta K5P Credit ==========

    def test_alberta_k5p_credit(self):
        """Test: Alberta supplemental tax credit"""
        calc = ProvincialTaxCalculator(Province.AB, 2025, 26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("80000"),
            total_claim_amount=Decimal("22323"),
            cpp_per_period=Decimal("120"),
            ei_per_period=Decimal("40")
        )

        # K5P should be applied for Alberta
        assert "k5p_credit" in result or result["annual_provincial_tax"] < Decimal("3000")
```

---

## Test Fixtures

**File**: `backend/tests/payroll/conftest.py`

```python
# backend/tests/payroll/conftest.py

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.cpp_calculator import CPPCalculator
from app.services.payroll.ei_calculator import EICalculator
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator
from app.models.payroll import Province


@pytest.fixture
def cpp_calc_biweekly():
    """CPP calculator for bi-weekly pay"""
    return CPPCalculator(year=2025, pay_periods_per_year=26)


@pytest.fixture
def ei_calc_biweekly():
    """EI calculator for bi-weekly pay"""
    return EICalculator(year=2025, pay_periods_per_year=26)


@pytest.fixture
def federal_calc_jul2025():
    """Federal tax calculator for July 2025 (14% rate)"""
    return FederalTaxCalculator(
        year=2025,
        pay_periods_per_year=26,
        pay_date=date(2025, 7, 15)
    )


@pytest.fixture
def ontario_calc():
    """Ontario provincial tax calculator"""
    return ProvincialTaxCalculator(Province.ON, 2025, 26)


@pytest.fixture
def standard_employee_input():
    """Standard test employee: Ontario, $60k, bi-weekly"""
    return {
        "gross_per_period": Decimal("2307.69"),
        "province": Province.ON,
        "pay_periods": 26,
        "federal_claim": Decimal("16129.00"),
        "provincial_claim": Decimal("12747.00"),
        "ytd_gross": Decimal("0"),
        "ytd_cpp": Decimal("0"),
        "ytd_ei": Decimal("0"),
    }


# Provincial BPA reference data
PROVINCIAL_BPA_2025 = {
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


@pytest.fixture
def provincial_bpa():
    """Provincial BPA reference data"""
    return PROVINCIAL_BPA_2025
```

---

## Execution Instructions

### Step 1: Create Test Directory

```bash
cd backend
mkdir -p tests/payroll
touch tests/payroll/__init__.py
```

### Step 2: Create Test Files

Copy the test code above into the respective files.

### Step 3: Run Tests

```bash
# Run all unit tests
uv run pytest tests/payroll/ -v

# Run with coverage report
uv run pytest tests/payroll/ -v --cov=app/services/payroll --cov-report=term-missing

# Run specific calculator tests
uv run pytest tests/payroll/test_cpp_calculator.py -v
```

### Step 4: Review Coverage

```bash
# Generate HTML coverage report
uv run pytest tests/payroll/ --cov=app/services/payroll --cov-report=html

# Open report
open htmlcov/index.html
```

---

## Completion Checklist

- [ ] `test_cpp_calculator.py` created and passing
- [ ] `test_ei_calculator.py` created and passing
- [ ] `test_federal_tax.py` created and passing
- [ ] `test_provincial_tax.py` created and passing
- [ ] All 12 provinces covered in parametrized tests
- [ ] Coverage > 80% for payroll services
- [ ] PDOC validation placeholders identified

---

**Next**: [Phase 2: Integration Tests](./02_integration_tests.md)
