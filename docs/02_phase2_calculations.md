# Phase 2: Core Calculation Engine

> **Note:** 本文档中的税率和金额基于 CRA T4127 121st Edition (July 2025)
>
> **2025 Mid-Year Tax Rate Change:** 2025年联邦最低税率从15%降至14%，生效日期为7月1日：
> - **2025年1月1日 - 6月30日**: 120th Edition (15% rate)
> - **2025年7月1日起**: 121st Edition (14% rate)
>
> 系统会根据 `pay_date` 自动选择对应的税率版本。

**Duration**: 3 weeks
**Complexity**: Medium
**Prerequisites**: Phase 1 completed

---

## 🎯 Objectives

Implement the core payroll calculation logic following CRA T4127 formulas.

---

## 📊 Tax Calculation Methods

CRA T4127 provides two official methods for calculating income tax withholding. This system supports both methods, configurable at the Pay Group level.

### Option 1: Annualization Method (Default)

**How it works:**
- Each pay period is calculated independently
- Current period income is annualized: `A = P × (I - F - F2 - U1 - CPP2)`
- Annual tax is calculated, then divided by pay periods

**Formula Variables:**
- `I` = Gross income per period
- `F` = RRSP deduction per period
- `F2` = CPP enhancement portion (1% of 5.95% base rate, deductible from taxable income)
- `U1` = Union dues per period
- `CPP2` = CPP additional contribution per period (for income > YMPE)
- `P` = Pay periods per year

**Best for:**
- Employees with stable, predictable income
- Salaried employees

**Pros:**
- Simple to understand and implement
- Each pay period is self-contained
- No need to track YTD tax amounts

**Cons:**
- May over/under-withhold for variable income
- Year-end reconciliation through personal tax return

### Option 2: Cumulative Averaging Method (Coming Soon)

**How it works:**
- Considers YTD earnings and YTD tax already withheld
- Calculates what total tax *should be* for YTD period
- Deducts current period tax as the difference

**Formula:**
```
Current Period Tax = (Cumulative Tax on YTD Income) - (YTD Tax Already Withheld)
```

**Best for:**
- Employees with variable income (commissions, bonuses)
- Sales teams with fluctuating earnings

**Pros:**
- More accurate throughout the year
- Reduces over/under-withholding
- Better cash flow management for employees

**Cons:**
- More complex calculation
- Requires accurate YTD tracking

### Configuration

Tax calculation method is configured at the **Pay Group** level:

```typescript
interface PayGroup {
  // ...other fields...
  taxCalculationMethod: 'annualization' | 'cumulative_averaging';
}
```

This allows different employee groups (e.g., salaried vs. sales) to use appropriate methods.

---

### Deliverables
1. ✅ CPP calculator (base + additional CPP2)
2. ✅ EI calculator
3. ✅ Federal tax calculator
4. ✅ Provincial/territorial tax calculator
5. ✅ Main payroll orchestration engine

---

## 📦 Task 2.1: CPP Calculator

### LLM Agent Prompt

```markdown
TASK: Implement CPP (Canada Pension Plan) Calculator

CONTEXT:
CPP has two components:
1. Base CPP: 5.95% on earnings between $3,500 and $71,200
2. Additional CPP (CPP2): 1.00% on earnings between $71,200 and $76,000

REFERENCE: T4127 Chapter 6

FILE TO CREATE:
backend/app/services/payroll/cpp_calculator.py

REQUIREMENTS:

1. Import dependencies and define return type:
```python
from decimal import Decimal
from typing import NamedTuple
from ..tax_tables_2025 import CPP_CONFIG_2025


class CppContribution(NamedTuple):
    """CPP contribution breakdown."""
    base: Decimal           # Base CPP (5.95% rate)
    additional: Decimal     # CPP2 (1.00% rate, for income > YMPE)
    enhancement: Decimal    # F2: 1% enhancement portion (deductible from taxable income)
    total: Decimal          # base + additional
    employer: Decimal       # Employer contribution (matches employee total)
```

2. Implement CPPCalculator class:

```python
class CPPCalculator:
    """
    Canada Pension Plan contribution calculator

    Reference: CRA T4127 Chapter 6
    Formulas for calculating base and additional CPP contributions
    """

    def __init__(self, pay_periods_per_year: int = 26):
        """
        Args:
            pay_periods_per_year: Number of pay periods (52=weekly, 26=bi-weekly, etc.)
        """
        self.P = pay_periods_per_year
        self.config = CPP_CONFIG_2025

    def calculate_base_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Calculate base CPP contribution for the pay period

        Formula from T4127:
        C = 0.0595 × (PI - ($3,500 / P))

        Where:
        - PI = Pensionable earnings for the period
        - P = Pay periods per year
        - Maximum annual contribution: $4,034.10

        Args:
            pensionable_earnings: Gross earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings (before this period)
            ytd_cpp: Year-to-date CPP contributions (before this period)

        Returns:
            CPP contribution for this period (rounded to 2 decimals)
        """
        # Basic exemption per pay period
        exemption_per_period = Decimal(str(self.config["basic_exemption"])) / self.P

        # Pensionable earnings after exemption
        pensionable_after_exemption = max(
            pensionable_earnings - exemption_per_period,
            Decimal("0")
        )

        # Calculate contribution
        base_cpp = Decimal(str(self.config["base_rate"])) * pensionable_after_exemption

        # Check annual maximum
        max_annual_contribution = Decimal(str(self.config["max_base_contribution"]))
        if ytd_cpp + base_cpp > max_annual_contribution:
            base_cpp = max(max_annual_contribution - ytd_cpp, Decimal("0"))

        return round(base_cpp, 2)

    def calculate_additional_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Calculate additional CPP (CPP2) contribution

        Formula from T4127:
        C2 = 0.0100 × max(0, PI - (YMPE / P))

        Where:
        - YMPE = Year's Maximum Pensionable Earnings ($71,200)
        - YAMPE = Year's Additional Maximum ($76,000)
        - Maximum annual CPP2: $396.00

        Args:
            pensionable_earnings: Gross earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings
            ytd_cpp_additional: Year-to-date additional CPP

        Returns:
            Additional CPP contribution for this period
        """
        ympe = Decimal(str(self.config["ympe"]))
        yampe = Decimal(str(self.config["yampe"]))
        additional_rate = Decimal(str(self.config["additional_rate"]))

        # YMPE per pay period
        ympe_per_period = ympe / self.P
        yampe_per_period = yampe / self.P

        # Earnings subject to CPP2 (above YMPE, up to YAMPE)
        if pensionable_earnings > ympe_per_period:
            cpp2_earnings = min(
                pensionable_earnings - ympe_per_period,
                yampe_per_period - ympe_per_period
            )
            cpp2 = additional_rate * cpp2_earnings
        else:
            cpp2 = Decimal("0")

        # Check annual maximum
        max_cpp2 = Decimal(str(self.config["max_additional_contribution"]))
        if ytd_cpp_additional + cpp2 > max_cpp2:
            cpp2 = max(max_cpp2 - ytd_cpp_additional, Decimal("0"))

        return round(cpp2, 2)

    def calculate(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_base: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0")
    ) -> CppContribution:
        """
        Calculate CPP contributions for the pay period.

        Returns:
            CppContribution NamedTuple with fields:
            - base: Base CPP contribution (5.95% rate)
            - additional: CPP2 contribution (1.00% rate, for income > YMPE)
            - enhancement: F2 portion (1% of 5.95%, deductible from taxable income)
            - total: base + additional
            - employer: Employer contribution (matches employee total)
        """
        base_cpp = self.calculate_base_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_base
        )

        additional_cpp = self.calculate_additional_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_additional
        )

        # F2: Enhancement portion = base_cpp × (0.01 / 0.0595)
        enhancement = self._round(base_cpp * (Decimal("0.01") / Decimal("0.0595")))
        total = base_cpp + additional_cpp

        return CppContribution(
            base=base_cpp,
            additional=additional_cpp,
            enhancement=enhancement,
            total=total,
            employer=total
        )

    def get_employer_contribution(self, employee_cpp: Decimal) -> Decimal:
        """
        Calculate employer CPP contribution (matches employee contribution)

        Args:
            employee_cpp: Total employee CPP (base + additional)

        Returns:
            Employer CPP contribution (same as employee)
        """
        return employee_cpp
```

VALIDATION:
Test with T4127 example or realistic scenarios:
```python
calc = CPPCalculator(pay_periods_per_year=26)  # Bi-weekly

# Scenario 1: Low income (below YMPE)
result = calc.calculate(pensionable_earnings=Decimal("2000.00"))
assert result.additional == Decimal("0")  # No CPP2
assert result.base > Decimal("0")
assert result.enhancement > Decimal("0")  # F2 is calculated from base

# Scenario 2: High income (above YMPE)
result = calc.calculate(pensionable_earnings=Decimal("3500.00"))
assert result.additional > Decimal("0")  # Has CPP2
assert result.enhancement > Decimal("0")  # F2 portion for tax deduction
```
```

---

## 📦 Task 2.1.1: CPP2 Multi-Job Exemption

### LLM Agent Prompt

```markdown
TASK: Implement CPP2 Multi-Job Exemption Handling

CONTEXT:
Employees with multiple jobs can request exemption from CPP2 on their second (or subsequent) job if they expect to maximize CPP contributions at their first job. This is done by filing Form CPT30 with their employer.

REFERENCE:
- CRA Form CPT30: Election to Stop Contributing to the Canada Pension Plan, or Revocation of a Prior Election
- https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/cpt30.html

FILE TO UPDATE:
backend/app/models/employee.py

REQUIREMENTS:

1. Add CPP2 exemption fields to Employee model:

```python
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class EmployeePayrollConfig(BaseModel):
    """
    Employee payroll configuration including tax exemptions
    """
    # Existing fields...
    is_cpp_exempt: bool = Field(default=False, description="Employee is CPP-exempt (e.g., age 65+)")
    is_ei_exempt: bool = Field(default=False, description="Employee is EI-exempt")

    # CPP2 Multi-Job Exemption (NEW)
    cpp2_exemption_on_file: bool = Field(
        default=False,
        description="Employee has filed CPT30 form to stop CPP2 contributions"
    )
    cpp2_exemption_effective_date: Optional[date] = Field(
        None,
        description="Date CPT30 exemption becomes effective"
    )
    cpp2_exemption_revoked: bool = Field(
        default=False,
        description="Employee has revoked CPT30 exemption"
    )
    cpp2_exemption_revocation_date: Optional[date] = Field(
        None,
        description="Date CPT30 exemption was revoked"
    )
```

2. Update CPPCalculator to respect CPP2 exemption:

```python
def calculate_additional_cpp(
    self,
    pensionable_earnings: Decimal,
    ytd_pensionable_earnings: Decimal = Decimal("0"),
    ytd_cpp_additional: Decimal = Decimal("0"),
    cpp2_exempt: bool = False  # NEW PARAMETER
) -> Decimal:
    """
    Calculate additional CPP (CPP2) contribution

    Args:
        pensionable_earnings: Gross earnings for this period
        ytd_pensionable_earnings: Year-to-date pensionable earnings
        ytd_cpp_additional: Year-to-date additional CPP
        cpp2_exempt: If True, employee is exempt from CPP2 (CPT30 on file)

    Returns:
        Additional CPP contribution for this period
    """
    # Check CPP2 exemption
    if cpp2_exempt:
        return Decimal("0")

    # Rest of calculation as before...
    ympe = Decimal(str(self.config["ympe"]))
    yampe = Decimal(str(self.config["yampe"]))
    additional_rate = Decimal(str(self.config["additional_rate"]))

    # ... (existing logic)
```

3. Update PayrollEngine to pass CPP2 exemption status:

```python
def calculate_payroll(
    self,
    request: PayrollCalculationRequest
) -> PayrollCalculationResult:
    """
    Calculate complete payroll for one pay period
    """
    # ... existing code ...

    # 1. Calculate CPP
    if request.is_cpp_exempt:
        cpp_base = Decimal("0")
        cpp_additional = Decimal("0")
    else:
        cpp_base, cpp_additional, _ = cpp_calc.calculate_total_cpp(
            request.gross_pay,
            request.ytd_gross,
            request.ytd_cpp,
            request.ytd_cpp_additional,
            cpp2_exempt=request.cpp2_exempt  # NEW PARAMETER
        )

    # ... rest of calculation ...
```

VALIDATION:
Test scenarios:
1. Employee with CPT30 on file should have CPP2 = $0
2. Employee without CPT30 should have CPP2 calculated normally for income > YMPE
```
```

---

## 📦 Task 2.2: EI Calculator

### LLM Agent Prompt

```markdown
TASK: Implement EI (Employment Insurance) Calculator

REFERENCE: T4127 Chapter 7

FILE TO CREATE:
backend/app/services/payroll/ei_calculator.py

REQUIREMENTS:

1. Implement EICalculator class:

```python
from decimal import Decimal
from ..tax_tables_2025 import EI_CONFIG_2025

class EICalculator:
    """
    Employment Insurance premium calculator

    Reference: CRA T4127 Chapter 7
    Formula: EI = IE × 0.0164 (1.64%)
    """

    def __init__(self, pay_periods_per_year: int = 26):
        self.P = pay_periods_per_year
        self.config = EI_CONFIG_2025

    def calculate_ei_premium(
        self,
        insurable_earnings: Decimal,
        ytd_insurable_earnings: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Calculate EI premium for the pay period

        Formula: EI = IE × 0.0164
        Maximum insurable earnings: $65,700
        Maximum annual premium: $1,077.48

        Args:
            insurable_earnings: Insurable earnings for this period
            ytd_insurable_earnings: Year-to-date insurable earnings
            ytd_ei: Year-to-date EI premiums

        Returns:
            EI premium for this period
        """
        employee_rate = Decimal(str(self.config["employee_rate"]))
        max_premium = Decimal(str(self.config["max_premium"]))
        max_insurable = Decimal(str(self.config["mie"]))

        # Check if already at annual maximum
        if ytd_ei >= max_premium:
            return Decimal("0")

        # Check if YTD insurable earnings exceed maximum
        if ytd_insurable_earnings >= max_insurable:
            return Decimal("0")

        # Calculate premium for this period
        ei_premium = employee_rate * insurable_earnings

        # Ensure we don't exceed annual maximum
        if ytd_ei + ei_premium > max_premium:
            ei_premium = max(max_premium - ytd_ei, Decimal("0"))

        return round(ei_premium, 2)

    def get_employer_premium(self, employee_ei: Decimal) -> Decimal:
        """
        Calculate employer EI premium (1.4 times employee premium)

        Args:
            employee_ei: Employee EI premium

        Returns:
            Employer EI premium
        """
        employer_rate = Decimal(str(self.config["employer_rate"]))
        employee_rate = Decimal(str(self.config["employee_rate"]))

        # Employer rate is 1.4x employee rate
        employer_premium = employee_ei * (employer_rate / employee_rate)
        return round(employer_premium, 2)
```

VALIDATION:
```python
calc = EICalculator(pay_periods_per_year=26)

# Test regular premium
ei = calc.calculate_ei_premium(Decimal("2000.00"))
assert ei == Decimal("32.80")  # 2000 * 0.0164

# Test employer premium
employer_ei = calc.get_employer_premium(ei)
assert employer_ei == Decimal("45.92")  # 32.80 * 1.4
```
```

---

## 📦 Task 2.3: Federal Tax Calculator

### LLM Agent Prompt

```markdown
TASK: Implement Federal Income Tax Calculator

REFERENCE: T4127 Chapter 4, Step 2-3

FILE TO CREATE:
backend/app/services/payroll/federal_tax_calculator.py

REQUIREMENTS:

Implement federal tax calculation following T4127 Option 1 formula.

```python
from decimal import Decimal
from typing import Dict
from ..tax_tables_2025 import FEDERAL_TAX_CONFIG, find_tax_bracket

class FederalTaxCalculator:
    """
    Federal income tax calculator

    Reference: CRA T4127 Chapter 4
    Formula: T3 = (R × A) - K - K1 - K2 - K3 - K4

    Note: For 2025, the lowest federal tax bracket changed from 15% to 14%
    effective July 1, 2025. The calculator accepts a pay_date parameter to
    automatically select the appropriate tax edition.
    """

    def __init__(self, pay_periods_per_year: int = 26, year: int = 2025, pay_date: date | None = None):
        self.P = pay_periods_per_year
        self.year = year
        self.pay_date = pay_date
        # Selects 120th Edition (Jan, 15%) or 121st Edition (Jul, 14%) based on pay_date
        self.config = get_federal_config(year, pay_date)

    def calculate_annual_taxable_income(
        self,
        gross_per_period: Decimal,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        cpp2_per_period: Decimal = Decimal("0"),
        cpp_enhancement_per_period: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Calculate annual taxable income (Factor A)

        Formula: A = P × (I - F - F2 - U1 - CPP2)

        Where:
        - I = Gross income per period
        - F = RRSP deduction
        - F2 = CPP enhancement portion (1% of 5.95%, deductible)
        - U1 = Union dues
        - CPP2 = CPP additional contribution (deductible)
        - P = Pay periods per year

        Returns:
            Annual taxable income
        """
        net_per_period = (
            gross_per_period
            - rrsp_per_period
            - union_dues_per_period
            - cpp_enhancement_per_period  # F2
            - cpp2_per_period             # CPP2
        )
        return max(self.P * net_per_period, Decimal("0"))

    def calculate_k1(self, total_claim_amount: Decimal) -> Decimal:
        """
        Calculate K1 (personal tax credits)

        Formula: K1 = 0.15 × TC

        Where TC = Total claim amount from TD1 form
        """
        return Decimal("0.15") * total_claim_amount

    def calculate_k2(
        self,
        cpp_per_period: Decimal,
        ei_per_period: Decimal
    ) -> Decimal:
        """
        Calculate K2 (CPP and EI tax credits)

        Formula: K2 = [0.15 × (P × C × (0.0495/0.0595))] + [0.15 × (P × EI)]

        Note: CPP credit uses base rate only (0.0495), not total rate (0.0595)
        """
        # CPP credit (using base rate proportion)
        cpp_credit_base = self.P * cpp_per_period * (Decimal("0.0495") / Decimal("0.0595"))
        max_cpp_credit = Decimal("4034.10")  # Annual maximum (2025)
        cpp_credit = min(cpp_credit_base, max_cpp_credit)

        # EI credit
        ei_credit_base = self.P * ei_per_period
        max_ei_credit = Decimal("1077.48")  # Annual maximum
        ei_credit = min(ei_credit_base, max_ei_credit)

        # Total K2
        k2 = Decimal("0.15") * (cpp_credit + ei_credit)
        return k2

    def calculate_k4(self, annual_income: Decimal) -> Decimal:
        """
        Calculate K4 (Canada Employment Amount credit)

        Formula: K4 = lesser of (0.15 × A) or (0.15 × CEA)
        CEA = $1,471 for 2025
        """
        cea = Decimal(str(self.config["cea"]))
        k4 = min(Decimal("0.15") * annual_income, Decimal("0.15") * cea)
        return k4

    def calculate_federal_tax(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        k3: Decimal = Decimal("0")
    ) -> Dict[str, Decimal]:
        """
        Calculate annual federal tax (T3 and T1)

        Formula: T3 = (R × A) - K - K1 - K2 - K3 - K4

        Returns:
            Dictionary with calculation breakdown
        """
        A = annual_taxable_income

        # Find applicable tax bracket
        R, K = find_tax_bracket(A, self.config["tax_brackets"])

        # Calculate credits
        K1 = self.calculate_k1(total_claim_amount)
        K2 = self.calculate_k2(cpp_per_period, ei_per_period)
        K4 = self.calculate_k4(A)

        # Calculate T3 (basic federal tax)
        T3 = (R * A) - K - K1 - K2 - k3 - K4
        T3 = max(T3, Decimal("0"))

        # T1 = T3 for standard employees (no additional credits/levies)
        T1 = T3

        return {
            "annual_taxable_income": A,
            "tax_rate": R,
            "constant_k": K,
            "personal_credits_k1": K1,
            "cpp_ei_credits_k2": K2,
            "other_credits_k3": k3,
            "employment_credit_k4": K4,
            "basic_federal_tax_t3": T3,
            "annual_federal_tax_t1": T1,
            "federal_tax_per_period": T1 / self.P
        }

    def calculate_tax_per_period(
        self,
        gross_per_period: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Convenience method to calculate federal tax for one pay period

        Returns:
            Federal tax to deduct this period
        """
        A = self.calculate_annual_taxable_income(
            gross_per_period,
            rrsp_per_period,
            union_dues_per_period
        )

        result = self.calculate_federal_tax(
            A,
            total_claim_amount,
            cpp_per_period,
            ei_per_period
        )

        return round(result["federal_tax_per_period"], 2)
```

VALIDATION:
Use T4127 page 13 example to verify accuracy.
```
```

---

## 📦 Task 2.4: Provincial Tax Calculator

### LLM Agent Prompt

```markdown
TASK: Implement Provincial/Territorial Tax Calculator

REFERENCE: T4127 Chapter 4, Step 4-5

NOTE: This task implements basic provincial tax (T4). Special taxes (Ontario surtax/health premium, BC tax reduction) are documented but deferred to Phase 3+. See:
- backend/rag/cra_tax/ontario_surtax_health_premium_2025.md
- backend/rag/cra_tax/bc_tax_reduction_2025.md
- docs/planning/payroll/06_configuration_architecture.md (configuration approach)

FILE TO CREATE:
backend/app/services/payroll/provincial_tax_calculator.py

REQUIREMENTS:

Implement provincial tax with special handling for ON, AB, BC.

```python
from decimal import Decimal
from typing import Dict
from ..tax_tables_2025 import (
    PROVINCIAL_TAX_CONFIGS,
    get_province_config,
    get_lowest_provincial_rate,
    find_tax_bracket,
    calculate_bpamb,
    calculate_bpans,
    calculate_bpayt
)

class ProvincialTaxCalculator:
    """
    Provincial/Territorial income tax calculator

    Handles 12 jurisdictions with special features:
    - Alberta: K5P supplemental credit
    - Ontario: Surtax (V1) + Health Premium (V2)
    - BC: Tax reduction (Factor S)
    - Manitoba/Nova Scotia/Yukon: Dynamic BPA
    """

    def __init__(self, province_code: str, pay_periods_per_year: int = 26):
        self.province_code = province_code
        self.P = pay_periods_per_year
        self.config = get_province_config(province_code)
        self.lowest_rate = get_lowest_provincial_rate(province_code)

    def get_basic_personal_amount(
        self,
        annual_income: Decimal,
        net_income: Decimal = None
    ) -> Decimal:
        """
        Get BPA (may be dynamic based on province)

        Args:
            annual_income: Annual taxable income (A)
            net_income: Net income (for Manitoba only)

        Returns:
            Basic Personal Amount for this province
        """
        if not self.config.bpa_is_dynamic:
            return self.config.basic_personal_amount

        # Dynamic BPA provinces
        if self.province_code == "MB":
            ni = net_income if net_income else annual_income
            return calculate_bpamb(ni)
        elif self.province_code == "NS":
            return calculate_bpans(annual_income)
        elif self.province_code == "YT":
            return calculate_bpayt(annual_income)

        return self.config.basic_personal_amount

    def calculate_k1p(self, total_claim_amount: Decimal) -> Decimal:
        """
        Calculate K1P (provincial personal tax credits)

        Formula: K1P = lowest_rate × TCP
        """
        return self.lowest_rate * total_claim_amount

    def calculate_k2p(
        self,
        cpp_per_period: Decimal,
        ei_per_period: Decimal
    ) -> Decimal:
        """
        Calculate K2P (provincial CPP/EI credits)

        Formula: K2P = lowest_rate × [(P × C × base_ratio) + (P × EI)]
        """
        # CPP credit
        cpp_credit_base = self.P * cpp_per_period * (Decimal("0.0495") / Decimal("0.0595"))
        max_cpp = Decimal("4034.10")  # 2025 Annual maximum
        cpp_credit = min(cpp_credit_base, max_cpp)

        # EI credit
        ei_credit_base = self.P * ei_per_period
        max_ei = Decimal("1077.48")
        ei_credit = min(ei_credit_base, max_ei)

        k2p = self.lowest_rate * (cpp_credit + ei_credit)
        return k2p

    def calculate_k5p_alberta(self, k1p: Decimal, k2p: Decimal) -> Decimal:
        """
        Calculate K5P for Alberta (supplemental tax credit)

        Reference: T4127 Page 4, Alberta section
        Formula: K5P = ((K1P + K2P) - $3,600.00) × (0.04/0.06)

        Only applies if (K1P + K2P) > $3,600
        """
        if self.province_code != "AB":
            return Decimal("0")

        threshold = Decimal("3600.00")
        total_credits = k1p + k2p

        if total_credits <= threshold:
            return Decimal("0")

        k5p = (total_credits - threshold) * (Decimal("0.04") / Decimal("0.06"))
        return k5p

    def calculate_provincial_tax(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate annual provincial tax (T4 and T2)

        Formula: T4 = (V × A) - KP - K1P - K2P - K3P - K4P - K5P

        Returns:
            Dictionary with calculation breakdown
        """
        A = annual_taxable_income

        # Find applicable tax bracket
        V, KP = find_tax_bracket(A, self.config.tax_brackets)

        # Calculate credits
        K1P = self.calculate_k1p(total_claim_amount)
        K2P = self.calculate_k2p(cpp_per_period, ei_per_period)
        K5P = self.calculate_k5p_alberta(K1P, K2P)

        # Calculate T4 (basic provincial tax)
        T4 = (V * A) - KP - K1P - K2P - K5P
        T4 = max(T4, Decimal("0"))

        # Apply special provincial features
        if self.province_code == "ON":
            # Ontario: Surtax (V1) + Health Premium (V2)
            # IMPLEMENTATION: See backend/rag/cra_tax/ontario_surtax_health_premium_2025.md
            # Formula V1: if T4 <= 5710: V1=0; elif T4 <= 7307: V1=0.20×(T4-5710); else: V1=0.20×(T4-5710)+0.36×(T4-7307)
            # Formula V2: Income-based brackets from $0 (income ≤$20k) to $900 (income >$200k)
            # Configuration: backend/config/tax_tables/{year}/{edition}/special_taxes_{year}_{edition}.json
            # See: docs/planning/payroll/06_configuration_architecture.md
            V1 = self._calculate_ontario_surtax(T4)
            V2 = self._calculate_ontario_health_premium(A)
            T2 = T4 + V1 + V2

        elif self.province_code == "BC":
            # BC: Tax Reduction (Factor S) - reduces provincial tax for low-income individuals
            # IMPLEMENTATION: See backend/rag/cra_tax/bc_tax_reduction_2025.md
            # Formula: if A <= 25020: S=562; elif A < 40807: S=562-(0.0356×(A-25020)); else: S=0
            # Configuration: Same special_taxes JSON file with BC-specific parameters
            # See: docs/planning/payroll/06_configuration_architecture.md
            S = self._calculate_bc_tax_reduction(A)
            T2 = max(T4 - S, Decimal("0"))

        else:
            # Other provinces: T2 = T4 (no special features)
            T2 = T4

        return {
            "annual_taxable_income": A,
            "tax_rate": V,
            "constant_kp": KP,
            "personal_credits_k1p": K1P,
            "cpp_ei_credits_k2p": K2P,
            "supplemental_credit_k5p": K5P,
            "basic_provincial_tax_t4": T4,
            "annual_provincial_tax_t2": T2,
            "provincial_tax_per_period": T2 / self.P
        }

    def calculate_tax_per_period(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal
    ) -> Decimal:
        """
        Convenience method for one pay period

        Returns:
            Provincial tax to deduct this period
        """
        result = self.calculate_provincial_tax(
            annual_taxable_income,
            total_claim_amount,
            cpp_per_period,
            ei_per_period
        )
        return round(result["provincial_tax_per_period"], 2)
```

VALIDATION:
Test each province, especially AB (K5P), MB/NS (dynamic BPA).
```
```

---

## 📦 Task 2.5: Payroll Engine (Orchestrator)

### LLM Agent Prompt

```markdown
TASK: Create Main Payroll Calculation Engine

FILE TO CREATE:
backend/app/services/payroll/payroll_engine.py

REQUIREMENTS:

Orchestrate all calculators to produce final payroll result.

```python
from decimal import Decimal
from typing import Dict, Any
from ..models.payroll import (
    PayrollCalculationRequest,
    PayrollCalculationResult
)
from .cpp_calculator import CPPCalculator
from .ei_calculator import EICalculator
from .federal_tax_calculator import FederalTaxCalculator
from .provincial_tax_calculator import ProvincialTaxCalculator

class PayrollEngine:
    """
    Main payroll calculation orchestrator

    Coordinates CPP, EI, federal tax, and provincial tax calculations
    """

    def calculate_payroll(
        self,
        request: PayrollCalculationRequest
    ) -> PayrollCalculationResult:
        """
        Calculate complete payroll for one pay period

        Args:
            request: PayrollCalculationRequest with employee details

        Returns:
            PayrollCalculationResult with all deductions
        """
        # Determine pay periods per year
        pay_periods_map = {
            "weekly": 52,
            "bi_weekly": 26,
            "semi_monthly": 24,
            "monthly": 12
        }
        P = pay_periods_map[request.pay_frequency]

        # Initialize calculators
        cpp_calc = CPPCalculator(P)
        ei_calc = EICalculator(P)
        fed_calc = FederalTaxCalculator(P)
        prov_calc = ProvincialTaxCalculator(request.province, P)

        # 1. Calculate CPP
        if request.is_cpp_exempt:
            cpp_base = Decimal("0")
            cpp_additional = Decimal("0")
        else:
            cpp_base, cpp_additional, _ = cpp_calc.calculate_total_cpp(
                request.gross_pay,
                request.ytd_gross,
                request.ytd_cpp,
                Decimal("0")  # YTD additional CPP
            )

        cpp_employee = cpp_base + cpp_additional
        cpp_employer = cpp_calc.get_employer_contribution(cpp_employee)

        # 2. Calculate EI
        if request.is_ei_exempt:
            ei_employee = Decimal("0")
        else:
            ei_employee = ei_calc.calculate_ei_premium(
                request.gross_pay,
                request.ytd_gross,
                request.ytd_ei
            )

        ei_employer = ei_calc.get_employer_premium(ei_employee)

        # 3. Calculate Federal Tax
        annual_taxable_income = fed_calc.calculate_annual_taxable_income(
            request.gross_pay,
            request.rrsp_deduction,
            request.union_dues
        )

        federal_tax = fed_calc.calculate_tax_per_period(
            request.gross_pay,
            request.federal_claim_amount,
            cpp_base,  # Use base CPP only for tax credit
            ei_employee,
            request.rrsp_deduction,
            request.union_dues
        )

        # 4. Calculate Provincial Tax
        provincial_tax = prov_calc.calculate_tax_per_period(
            annual_taxable_income,
            request.provincial_claim_amount,
            cpp_base,
            ei_employee
        )

        # 5. Calculate totals
        total_employee_deductions = (
            cpp_employee + ei_employee + federal_tax + provincial_tax +
            request.rrsp_deduction + request.union_dues
        )

        total_employer_costs = cpp_employer + ei_employer

        net_pay = request.gross_pay - total_employee_deductions

        # 6. Build result
        return PayrollCalculationResult(
            gross_pay=request.gross_pay,
            cpp_employee=cpp_base,
            cpp_additional=cpp_additional,
            cpp_employer=cpp_employer,
            ei_employee=ei_employee,
            ei_employer=ei_employer,
            federal_tax=federal_tax,
            provincial_tax=provincial_tax,
            rrsp=request.rrsp_deduction,
            union_dues=request.union_dues,
            total_employee_deductions=total_employee_deductions,
            total_employer_costs=total_employer_costs,
            net_pay=net_pay,
            calculation_details={
                "pay_frequency": request.pay_frequency,
                "pay_periods_per_year": P,
                "province": request.province,
                "annual_taxable_income": str(annual_taxable_income)
            }
        )
```

VALIDATION:
End-to-end test with realistic employee data.
```
```

---

## ✅ Phase 2 Validation

### Integration Test

```python
from backend.app.services.payroll.payroll_engine import PayrollEngine
from backend.app.models.payroll import PayrollCalculationRequest, Province, PayPeriodFrequency
from decimal import Decimal

engine = PayrollEngine()

# Test Ontario employee, bi-weekly, $60k annual ($2,307.69 per period)
request = PayrollCalculationRequest(
    employee_id="emp_001",
    province=Province.ON,
    pay_frequency=PayPeriodFrequency.BIWEEKLY,
    gross_pay=Decimal("2307.69"),
    federal_claim_amount=Decimal("16129.00"),
    provincial_claim_amount=Decimal("12747.00"),
    rrsp_deduction=Decimal("100.00"),
    union_dues=Decimal("0"),
    ytd_gross=Decimal("0"),
    ytd_cpp=Decimal("0"),
    ytd_ei=Decimal("0")
)

result = engine.calculate_payroll(request)

# Verify calculations
assert result.cpp_employee > Decimal("0")
assert result.ei_employee == round(Decimal("2307.69") * Decimal("0.0164"), 2)
assert result.federal_tax > Decimal("0")
assert result.provincial_tax > Decimal("0")
assert result.net_pay == result.gross_pay - result.total_employee_deductions

print(f"Gross: ${result.gross_pay}")
print(f"CPP: ${result.cpp_employee}")
print(f"EI: ${result.ei_employee}")
print(f"Federal Tax: ${result.federal_tax}")
print(f"Provincial Tax: ${result.provincial_tax}")
print(f"Net Pay: ${result.net_pay}")
```

---

## 🚨 Common Issues

### Issue 1: YTD Not Considered
**Problem**: CPP/EI max exceeded
**Solution**: Always pass YTD values to calculators

### Issue 2: Tax Credit Calculation Wrong
**Problem**: K2 uses total CPP rate instead of base rate
**Solution**: Use 0.0495/0.0595 ratio for CPP credit

### Issue 3: Alberta K5P Missing
**Problem**: Alberta tax too high
**Solution**: Implement K5P calculation (only if credits > $3,600)

---

**Next**: [Phase 3: Paystub Generation](./03_phase3_paystub.md)
