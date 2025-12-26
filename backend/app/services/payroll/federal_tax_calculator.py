"""
Federal Income Tax Calculator

Implements federal income tax calculations following CRA T4127 Chapter 4, Step 2-3.
Uses Option 1 (annualized tax method).

Reference: T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, NamedTuple

from app.services.payroll.tax_tables import find_tax_bracket, get_cpp_config, get_ei_config, get_federal_config

logger = logging.getLogger(__name__)


class FederalTaxResult(NamedTuple):
    """Federal tax calculation result with breakdown."""
    annual_taxable_income: Decimal
    tax_rate: Decimal
    constant_k: Decimal
    personal_credits_k1: Decimal
    cpp_ei_credits_k2: Decimal
    other_credits_k3: Decimal
    employment_credit_k4: Decimal
    basic_federal_tax_t3: Decimal
    annual_federal_tax_t1: Decimal
    tax_per_period: Decimal


class FederalTaxCalculator:
    """
    Federal income tax calculator.

    Reference: CRA T4127 Chapter 4

    Uses the T4127 Option 1 formula:
    T3 = (R × A) - K - K1 - K2 - K3 - K4

    Where:
    - A = Annual taxable income
    - R = Tax rate for applicable bracket
    - K = Tax constant for applicable bracket
    - K1 = Personal tax credits (rate × TC)
    - K2 = CPP and EI tax credits
    - K3 = Other tax credits (medical, tuition, etc.)
    - K4 = Canada Employment Amount credit
    """

    def __init__(
        self,
        pay_periods_per_year: int = 26,
        year: int = 2025,
        pay_date: date | None = None,
    ):
        """
        Initialize federal tax calculator.

        Args:
            pay_periods_per_year: Number of pay periods (52=weekly, 26=bi-weekly, etc.)
            year: Tax year for configuration lookup
            pay_date: Pay period date for selecting appropriate tax edition
                     (2025: before July 1 uses 15% rate, after uses 14% rate)
        """
        self.P = pay_periods_per_year
        self.year = year
        self.pay_date = pay_date
        self._config = get_federal_config(year, pay_date)
        self._cpp_config = get_cpp_config(year)
        self._ei_config = get_ei_config(year)

        # Load configuration values as Decimal
        self.bpaf = Decimal(str(self._config["bpaf"]))  # Basic Personal Amount Federal
        self.cea = Decimal(str(self._config["cea"]))    # Canada Employment Amount
        self.brackets = self._config["brackets"]

        # Tax credit rates
        self.k1_rate = Decimal(str(self._config.get("k1_rate", "0.15")))
        self.k2_rate = Decimal(str(self._config.get("k2_cpp_ei_rate", "0.15")))
        self.k4_rate = Decimal(str(self._config.get("k4_canada_employment_rate", "0.15")))

        # CPP/EI maximums for credit calculation
        self.max_cpp_credit = Decimal(str(self._cpp_config["max_base_contribution"]))
        self.max_ei_credit = Decimal(str(self._ei_config["max_employee_premium"]))

        # CPP credit ratio (uses 4.95% rate, not full 5.95%)
        self.cpp_credit_ratio = Decimal("0.0495") / Decimal(str(self._cpp_config["base_rate"]))

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using banker's rounding."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_annual_taxable_income(
        self,
        gross_per_period: Decimal,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        cpp2_per_period: Decimal = Decimal("0"),
        cpp_enhancement_per_period: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Calculate annual taxable income (Factor A).

        Formula: A = P × (I - F - F2 - U1 - CPP2)

        Where:
        - I = Gross income per period
        - F = RRSP deduction per period
        - F2 = CPP enhancement portion (1% of 5.95%)
        - U1 = Union dues per period
        - CPP2 = CPP additional contribution per period (deductible from taxable income)
        - P = Pay periods per year

        Note: Both F2 (CPP enhancement) and CPP2 are deducted from taxable income
        per CRA T4127 guidelines.

        Args:
            gross_per_period: Gross income for this pay period
            rrsp_per_period: RRSP deduction for this period
            union_dues_per_period: Union dues for this period
            cpp2_per_period: CPP additional contribution (CPP2) for this period
            cpp_enhancement_per_period: CPP enhancement portion (F2) for this period

        Returns:
            Annual taxable income
        """
        net_per_period = (
            gross_per_period
            - rrsp_per_period
            - union_dues_per_period
            - cpp_enhancement_per_period  # F2: CPP enhancement (1% portion)
            - cpp2_per_period             # CPP2: additional contribution
        )
        annual_income = self.P * net_per_period
        return max(annual_income, Decimal("0"))

    def calculate_k1(self, total_claim_amount: Decimal) -> Decimal:
        """
        Calculate K1 (personal tax credits).

        Formula: K1 = rate × TC

        Where TC = Total claim amount from TD1 form (includes BPA + additional claims)

        Args:
            total_claim_amount: Total claim amount from employee's TD1 form

        Returns:
            K1 personal tax credit amount
        """
        return self._round(self.k1_rate * total_claim_amount)

    def calculate_k2(
        self,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
    ) -> Decimal:
        """
        Calculate K2 (CPP and EI tax credits).

        Formula: K2 = rate × [(P × C × credit_ratio) + (P × EI)]

        Note: CPP credit uses base rate only (4.95%), not total rate (5.95%)
        because the enhancement portion doesn't qualify for the credit.

        The annual amounts are capped at the annual maximums.

        Args:
            cpp_per_period: CPP contribution for this period (base CPP only)
            ei_per_period: EI premium for this period

        Returns:
            K2 CPP/EI tax credit amount
        """
        # Annualize and apply CPP credit ratio
        annual_cpp = self.P * cpp_per_period * self.cpp_credit_ratio
        annual_cpp = min(annual_cpp, self.max_cpp_credit)

        # Annualize EI
        annual_ei = self.P * ei_per_period
        annual_ei = min(annual_ei, self.max_ei_credit)

        # Total K2
        k2 = self.k2_rate * (annual_cpp + annual_ei)
        return self._round(k2)

    def calculate_k4(self, annual_income: Decimal) -> Decimal:
        """
        Calculate K4 (Canada Employment Amount credit).

        Formula: K4 = lesser of (rate × A) or (rate × CEA)

        The Canada Employment Amount is capped at $1,471 (2025).

        Args:
            annual_income: Annual taxable income

        Returns:
            K4 Canada Employment Amount credit
        """
        # K4 is the lesser of the rate applied to income or CEA
        k4 = min(
            self.k4_rate * annual_income,
            self.k4_rate * self.cea
        )
        return self._round(k4)

    def calculate_federal_tax(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        k3: Decimal = Decimal("0"),
    ) -> FederalTaxResult:
        """
        Calculate annual federal tax (T3 and T1).

        Formula: T3 = (R × A) - K - K1 - K2 - K3 - K4

        Where:
        - A = Annual taxable income
        - R = Tax rate for applicable bracket
        - K = Tax constant for applicable bracket
        - K1-K4 = Various tax credits

        T1 = T3 for standard employees (no additional levies)

        Args:
            annual_taxable_income: Annualized taxable income (A)
            total_claim_amount: TD1 total claim amount (for K1)
            cpp_per_period: CPP contribution per period (for K2)
            ei_per_period: EI premium per period (for K2)
            k3: Other tax credits (medical, tuition, etc.)

        Returns:
            FederalTaxResult with full calculation breakdown
        """
        A = annual_taxable_income

        # Find applicable tax bracket
        R, K = find_tax_bracket(A, self.brackets)

        # Calculate credits
        K1 = self.calculate_k1(total_claim_amount)
        K2 = self.calculate_k2(cpp_per_period, ei_per_period)
        K4 = self.calculate_k4(A)

        # Calculate T3 (basic federal tax)
        T3 = (R * A) - K - K1 - K2 - k3 - K4
        T3 = max(T3, Decimal("0"))

        # T1 = T3 for standard employees (no additional federal levies)
        T1 = T3

        # Tax per period
        tax_per_period = self._round(T1 / self.P)

        return FederalTaxResult(
            annual_taxable_income=A,
            tax_rate=R,
            constant_k=K,
            personal_credits_k1=K1,
            cpp_ei_credits_k2=K2,
            other_credits_k3=k3,
            employment_credit_k4=K4,
            basic_federal_tax_t3=self._round(T3),
            annual_federal_tax_t1=self._round(T1),
            tax_per_period=tax_per_period,
        )

    def calculate_tax_per_period(
        self,
        gross_per_period: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        cpp2_per_period: Decimal = Decimal("0"),
        cpp_enhancement_per_period: Decimal = Decimal("0"),
        k3: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Convenience method to calculate federal tax for one pay period.

        Args:
            gross_per_period: Gross income for this period
            total_claim_amount: TD1 total claim amount
            cpp_per_period: CPP contribution for this period
            ei_per_period: EI premium for this period
            rrsp_per_period: RRSP deduction for this period
            union_dues_per_period: Union dues for this period
            cpp2_per_period: CPP additional contribution (CPP2) for this period
            cpp_enhancement_per_period: CPP enhancement portion (F2) for this period
            k3: Other tax credits

        Returns:
            Federal tax to deduct this period
        """
        A = self.calculate_annual_taxable_income(
            gross_per_period,
            rrsp_per_period,
            union_dues_per_period,
            cpp2_per_period,
            cpp_enhancement_per_period,
        )

        result = self.calculate_federal_tax(
            A,
            total_claim_amount,
            cpp_per_period,
            ei_per_period,
            k3,
        )

        return result.tax_per_period

    def get_calculation_details(
        self,
        gross_per_period: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        cpp2_per_period: Decimal = Decimal("0"),
        cpp_enhancement_per_period: Decimal = Decimal("0"),
        k3: Decimal = Decimal("0"),
    ) -> dict[str, Any]:
        """
        Get detailed calculation breakdown for debugging/audit.

        Returns a dictionary with all intermediate calculation values.
        """
        A = self.calculate_annual_taxable_income(
            gross_per_period,
            rrsp_per_period,
            union_dues_per_period,
            cpp2_per_period,
            cpp_enhancement_per_period,
        )

        result = self.calculate_federal_tax(
            A,
            total_claim_amount,
            cpp_per_period,
            ei_per_period,
            k3,
        )

        return {
            "inputs": {
                "gross_per_period": str(gross_per_period),
                "total_claim_amount": str(total_claim_amount),
                "cpp_per_period": str(cpp_per_period),
                "ei_per_period": str(ei_per_period),
                "rrsp_per_period": str(rrsp_per_period),
                "union_dues_per_period": str(union_dues_per_period),
                "cpp2_per_period": str(cpp2_per_period),
                "cpp_enhancement_per_period": str(cpp_enhancement_per_period),
                "pay_periods_per_year": self.P,
            },
            "calculation": {
                "annual_taxable_income_A": str(result.annual_taxable_income),
                "tax_rate_R": str(result.tax_rate),
                "constant_K": str(result.constant_k),
                "personal_credits_K1": str(result.personal_credits_k1),
                "cpp_ei_credits_K2": str(result.cpp_ei_credits_k2),
                "other_credits_K3": str(result.other_credits_k3),
                "employment_credit_K4": str(result.employment_credit_k4),
            },
            "result": {
                "basic_federal_tax_T3": str(result.basic_federal_tax_t3),
                "annual_federal_tax_T1": str(result.annual_federal_tax_t1),
                "tax_per_period": str(result.tax_per_period),
            },
            "formula": "T3 = (R × A) - K - K1 - K2 - K3 - K4",
        }
