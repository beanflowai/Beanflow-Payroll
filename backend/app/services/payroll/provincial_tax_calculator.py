"""
Provincial/Territorial Income Tax Calculator

Implements provincial tax calculations following CRA T4127 Chapter 4, Step 4-5.
Handles all 12 provinces/territories (excluding Quebec).

Includes special handling for:
- Ontario: Surtax (V1) + Health Premium (V2)
- British Columbia: Tax Reduction (Factor S)
- Alberta: K5P supplemental credit
- Manitoba/Nova Scotia/Yukon: Dynamic BPA

Reference: T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, NamedTuple

from app.services.payroll.tax_tables import (
    calculate_dynamic_bpa,
    find_tax_bracket,
    get_cpp_config,
    get_ei_config,
    get_province_config,
)

logger = logging.getLogger(__name__)


class ProvincialTaxResult(NamedTuple):
    """Provincial tax calculation result with breakdown."""
    province_code: str
    annual_taxable_income: Decimal
    tax_rate: Decimal
    constant_kp: Decimal
    personal_credits_k1p: Decimal
    cpp_ei_credits_k2p: Decimal
    employment_credit_k4p: Decimal
    supplemental_credit_k5p: Decimal
    basic_provincial_tax_t4: Decimal
    surtax_v1: Decimal
    health_premium_v2: Decimal
    tax_reduction_s: Decimal
    annual_provincial_tax_t2: Decimal
    tax_per_period: Decimal


class ProvincialTaxCalculator:
    """
    Provincial/Territorial income tax calculator.

    Reference: CRA T4127 Chapter 4, Steps 4-5

    Formula: T4 = (V × A) - KP - K1P - K2P - K3P - K4P - K5P

    Special provincial features:
    - Alberta: K5P supplemental credit
    - British Columbia: Tax reduction (Factor S)
    - Ontario: Surtax (V1) + Health Premium (V2)
    - Manitoba/Nova Scotia/Yukon: Dynamic BPA
    """

    def __init__(
        self,
        province_code: str,
        pay_periods_per_year: int = 26,
        year: int = 2025,
        pay_date: date | None = None,
    ):
        """
        Initialize provincial tax calculator.

        Args:
            province_code: Two-letter province code (e.g., "ON", "BC")
            pay_periods_per_year: Number of pay periods (52=weekly, 26=bi-weekly, etc.)
            year: Tax year for configuration lookup
            pay_date: Pay date for edition selection (SK, PE have different BPA in Jan vs Jul)
        """
        self.province_code = province_code.upper()
        self.P = pay_periods_per_year
        self.year = year
        self.pay_date = pay_date

        self._config = get_province_config(province_code, year, pay_date)
        self._cpp_config = get_cpp_config(year)
        self._ei_config = get_ei_config(year)

        # Load basic configuration
        self.brackets = self._config["brackets"]
        self.bpa = Decimal(str(self._config["bpa"]))
        self.bpa_is_dynamic = self._config.get("bpa_is_dynamic", False)

        # Get lowest tax rate for credit calculations
        self.lowest_rate = Decimal(str(self.brackets[0]["rate"]))

        # Special features
        self.has_surtax = self._config.get("has_surtax", False)
        self.has_health_premium = self._config.get("has_health_premium", False)
        self.has_tax_reduction = self._config.get("has_tax_reduction", False)
        self.has_k4p = self._config.get("has_k4p", False)
        self.cea = Decimal(str(self._config.get("cea", 0)))  # Canada Employment Amount

        # CPP/EI maximums for credit calculation
        self.max_cpp_credit = Decimal(str(self._cpp_config["max_base_contribution"]))
        self.max_ei_credit = Decimal(str(self._ei_config["max_employee_premium"]))
        self.cpp_credit_ratio = Decimal("0.0495") / Decimal(str(self._cpp_config["base_rate"]))

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using banker's rounding."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _get_k2p_effective_periods(
        self,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        ytd_cpp_base: Decimal,
        ytd_ei: Decimal,
    ) -> int:
        """
        Determine effective pay periods for K2P annualization.

        When CPP/EI reaches its annual maximum within the current period,
        PDOC annualizes K2P using one fewer full period.
        """
        effective_periods = self.P

        if (
            ytd_cpp_base > Decimal("0")
            and cpp_per_period > Decimal("0")
            and (ytd_cpp_base + cpp_per_period) >= self.max_cpp_credit
        ):
            effective_periods = max(1, self.P - 1)

        if (
            ytd_ei > Decimal("0")
            and ei_per_period > Decimal("0")
            and (ytd_ei + ei_per_period) >= self.max_ei_credit
        ):
            effective_periods = max(1, self.P - 1)

        return effective_periods

    def get_basic_personal_amount(
        self,
        annual_income: Decimal,
        net_income: Decimal | None = None,
    ) -> Decimal:
        """
        Get BPA (may be dynamic based on province).

        Args:
            annual_income: Annual taxable income (for NS, YT)
            net_income: Net income (for MB calculation)

        Returns:
            Basic Personal Amount for this province
        """
        if not self.bpa_is_dynamic:
            return self.bpa

        return calculate_dynamic_bpa(
            self.province_code,
            annual_income,
            net_income,
            self.year,
            self.pay_date,
        )

    def calculate_k1p(self, total_claim_amount: Decimal) -> Decimal:
        """
        Calculate K1P (provincial personal tax credits).

        Formula: K1P = lowest_rate × TCP

        Args:
            total_claim_amount: Provincial TD1 claim amount

        Returns:
            K1P provincial personal tax credit
        """
        return self._round(self.lowest_rate * total_claim_amount)

    def calculate_k2p(
        self,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        ytd_cpp_base: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0"),
        pensionable_months: int | None = None,
    ) -> Decimal:
        """
        Calculate K2P (provincial CPP/EI credits).

        Formula: K2P = lowest_rate × [min(annual_cpp, max_cpp) × credit_ratio + min(annual_ei, max_ei)]

        For CPP, when YTD values are provided, we use the maximum of
        (actual expected annual, annualized current period) to handle proration
        cases where current period CPP is reduced near the prorated max.

        The annual amounts are capped at the annual maximums BEFORE applying
        the credit ratio.

        Special handling:
        - When YTD has already reached the annual max, use the max for credit
        - For partial-year employees, prorate the CPP max by pensionable_months/12

        Args:
            cpp_per_period: CPP contribution per period (base CPP only)
            ei_per_period: EI premium per period
            ytd_cpp_base: Year-to-date base CPP contributions (before this period)
            ytd_ei: Year-to-date EI premiums (before this period)
            pensionable_months: Number of CPP pensionable months (1-12), None = 12

        Returns:
            K2P provincial CPP/EI tax credit
        """
        effective_periods = self._get_k2p_effective_periods(
            cpp_per_period,
            ei_per_period,
            ytd_cpp_base,
            ytd_ei,
        )

        # Prorate CPP max for partial-year employees (T4127 rule)
        pm = Decimal(pensionable_months) if pensionable_months else Decimal("12")
        prorated_max_cpp = self.max_cpp_credit * pm / Decimal("12")

        # For CPP: handle case where YTD has already reached prorated max
        # or will reach max in this period
        if ytd_cpp_base >= prorated_max_cpp:
            # Already at max - use the prorated max for credit
            annual_cpp_capped = prorated_max_cpp
        elif ytd_cpp_base > Decimal("0") and (ytd_cpp_base + cpp_per_period) >= prorated_max_cpp:
            # Reaches max in this period - use the prorated max for credit
            annual_cpp_capped = prorated_max_cpp
        else:
            # Use max of (actual annual, annualized) to handle proration cases
            # where current period CPP is reduced near the prorated max
            actual_annual_cpp = ytd_cpp_base + cpp_per_period
            annualized_cpp = Decimal(effective_periods) * cpp_per_period
            annual_cpp_raw = max(actual_annual_cpp, annualized_cpp)
            annual_cpp_capped = min(annual_cpp_raw, prorated_max_cpp)

        annual_cpp = annual_cpp_capped * self.cpp_credit_ratio

        # For EI: handle case where YTD has already reached max
        # or will reach max in this period
        if ytd_ei >= self.max_ei_credit:
            # Already at max - use the max for credit
            annual_ei = self.max_ei_credit
        elif ytd_ei > Decimal("0") and (ytd_ei + ei_per_period) >= self.max_ei_credit:
            # Reaches max in this period - use the max for credit
            annual_ei = self.max_ei_credit
        else:
            # Standard annualized approach
            annual_ei = Decimal(effective_periods) * ei_per_period
            annual_ei = min(annual_ei, self.max_ei_credit)

        k2p = self.lowest_rate * (annual_cpp + annual_ei)
        return self._round(k2p)

    def calculate_k5p_alberta(self, k1p: Decimal, k2p: Decimal) -> Decimal:
        """
        Calculate K5P for Alberta (supplemental tax credit).

        Reference: T4127 Alberta section (121st Edition - July 2025)

        IMPORTANT: K5P was introduced in July 2025 (121st Edition).
        For pay dates BEFORE July 1, 2025, K5P = $0.

        Formula varies by year:
        - 2025 (Jul-Dec only): K5P = ((K1P + K2P) - $3,600) × (0.04/0.06)
        - 2026+: K5P = ((K1P + K2P) - $4,896) × 0.25

        Only applies if (K1P + K2P) > threshold

        Args:
            k1p: Provincial personal credit (K1P)
            k2p: Provincial CPP/EI credit (K2P)

        Returns:
            K5P supplemental credit (Alberta only)
        """
        if self.province_code != "AB":
            return Decimal("0")

        # K5P was introduced in July 2025 (T4127 121st Edition)
        # For pay dates before July 1, 2025, K5P does not apply
        if self.year == 2025 and self.pay_date:
            k5p_effective_date = date(2025, 7, 1)
            if self.pay_date < k5p_effective_date:
                return Decimal("0")

        # Get K5P config from province configuration
        k5p_config = self._config.get("k5p_config", {})

        # Default to 2025 values if not configured
        threshold = Decimal(str(k5p_config.get("threshold", "3600.00")))

        # Support both factor formats:
        # - "factor": direct multiplier (e.g., 0.25 for 2026)
        # - "factor_numerator"/"factor_denominator": ratio (e.g., 0.04/0.06 for 2025)
        if "factor" in k5p_config:
            factor = Decimal(str(k5p_config["factor"]))
        else:
            numerator = Decimal(str(k5p_config.get("factor_numerator", "0.04")))
            denominator = Decimal(str(k5p_config.get("factor_denominator", "0.06")))
            factor = numerator / denominator

        total_credits = k1p + k2p

        if total_credits <= threshold:
            return Decimal("0")

        k5p = (total_credits - threshold) * factor
        return self._round(k5p)

    def calculate_k4p(self, annual_taxable_income: Decimal) -> Decimal:
        """
        Calculate K4P (Provincial/Territorial Employment Credit).

        Currently only applies to Yukon.
        Formula: K4P = lowest_rate × min(A, CEA)

        Args:
            annual_taxable_income: Annual taxable income (A)

        Returns:
            K4P employment credit amount
        """
        if not self.has_k4p or self.cea == Decimal("0"):
            return Decimal("0")

        # K4P is the lesser of rate applied to income or CEA
        k4p = self.lowest_rate * min(annual_taxable_income, self.cea)
        return self._round(k4p)

    def _calculate_ontario_surtax(self, basic_tax_t4: Decimal) -> Decimal:
        """
        Calculate Ontario surtax (V1).

        Formula:
        - If T4 <= $5,710: V1 = 0
        - If $5,710 < T4 <= $7,307: V1 = 0.20 × (T4 - $5,710)
        - If T4 > $7,307: V1 = 0.20 × (T4 - $5,710) + 0.36 × (T4 - $7,307)

        Args:
            basic_tax_t4: Basic provincial tax (T4)

        Returns:
            Ontario surtax amount
        """
        if self.province_code != "ON" or not self.has_surtax:
            return Decimal("0")

        config = self._config.get("surtax_config", {})
        first_threshold = Decimal(str(config.get("first_threshold", "5710")))
        first_rate = Decimal(str(config.get("first_rate", "0.20")))
        second_threshold = Decimal(str(config.get("second_threshold", "7307")))
        second_rate = Decimal(str(config.get("second_rate", "0.36")))

        if basic_tax_t4 <= first_threshold:
            return Decimal("0")

        # First tier surtax
        surtax = first_rate * (basic_tax_t4 - first_threshold)

        # Second tier surtax (additional)
        if basic_tax_t4 > second_threshold:
            surtax += second_rate * (basic_tax_t4 - second_threshold)

        return self._round(surtax)

    def _calculate_ontario_health_premium(self, annual_income: Decimal) -> Decimal:
        """
        Calculate Ontario Health Premium (V2).

        Income-based brackets from $0 to $900 based on taxable income.

        Args:
            annual_income: Annual taxable income

        Returns:
            Annual Ontario Health Premium
        """
        if self.province_code != "ON" or not self.has_health_premium:
            return Decimal("0")

        config = self._config.get("health_premium_config", {})
        brackets = config.get("brackets", [])

        if not brackets:
            return Decimal("0")

        # Find applicable bracket
        premium = Decimal("0")

        for i, bracket in enumerate(brackets):
            threshold = Decimal(str(bracket["threshold"]))
            if annual_income >= threshold:
                # Check if this is a flat premium bracket or rate-based
                if "rate" in bracket:
                    base = Decimal(str(bracket.get("base", "0")))
                    rate = Decimal(str(bracket["rate"]))
                    # Next threshold (or income if no next bracket)
                    next_threshold = Decimal(str(brackets[i + 1]["threshold"])) if i + 1 < len(brackets) else annual_income
                    income_in_bracket = min(annual_income, next_threshold) - threshold
                    premium = base + (rate * income_in_bracket)
                else:
                    premium = Decimal(str(bracket.get("premium", "0")))
            else:
                break

        return self._round(premium)

    def _calculate_bc_tax_reduction(self, annual_income: Decimal) -> Decimal:
        """
        Calculate BC Tax Reduction (Factor S).

        Formula:
        - If A <= $25,437: S = $521
        - If $25,437 < A < $39,913: S = $521 - (0.036 × (A - $25,437))
        - If A >= $39,913: S = 0

        Args:
            annual_income: Annual taxable income

        Returns:
            BC tax reduction amount
        """
        if self.province_code != "BC" or not self.has_tax_reduction:
            return Decimal("0")

        config = self._config.get("tax_reduction_config", {})
        base_reduction = Decimal(str(config.get("base_reduction", "521")))
        reduction_rate = Decimal(str(config.get("reduction_rate", "0.036")))
        phase_out_start = Decimal(str(config.get("phase_out_start", "25437")))
        phase_out_end = Decimal(str(config.get("phase_out_end", "39913")))

        if annual_income <= phase_out_start:
            return base_reduction

        if annual_income >= phase_out_end:
            return Decimal("0")

        # Phase out reduction
        reduction = base_reduction - (reduction_rate * (annual_income - phase_out_start))
        return max(self._round(reduction), Decimal("0"))

    def _calculate_pe_surtax(self, basic_tax_t4: Decimal) -> Decimal:
        """
        Calculate PEI surtax.

        Formula: If T4 > $13,500: Surtax = 0.10 × T4

        Args:
            basic_tax_t4: Basic provincial tax (T4)

        Returns:
            PEI surtax amount
        """
        if self.province_code != "PE" or not self.has_surtax:
            return Decimal("0")

        config = self._config.get("surtax_config", {})
        threshold = Decimal(str(config.get("threshold", "13500")))
        rate = Decimal(str(config.get("rate", "0.10")))

        if basic_tax_t4 <= threshold:
            return Decimal("0")

        return self._round(rate * basic_tax_t4)

    def calculate_provincial_tax(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        net_income: Decimal | None = None,
        ytd_cpp_base: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0"),
        pensionable_months: int | None = None,
    ) -> ProvincialTaxResult:
        """
        Calculate annual provincial tax (T4 and T2).

        Formula: T4 = (V × A) - KP - K1P - K2P - K3P - K4P - K5P

        Then apply special adjustments:
        - Ontario: T2 = T4 + V1 (surtax) + V2 (health premium)
        - BC: T2 = max(T4 - S, 0)
        - PEI: T2 = T4 + surtax
        - Others: T2 = T4

        Args:
            annual_taxable_income: Annualized taxable income
            total_claim_amount: Provincial TD1 claim amount
            cpp_per_period: CPP contribution per period
            ei_per_period: EI premium per period
            net_income: Net income (for Manitoba BPA calculation)
            ytd_cpp_base: Year-to-date base CPP contributions (for K2P)
            ytd_ei: Year-to-date EI premiums (for K2P)
            pensionable_months: Number of CPP pensionable months (1-12), None = 12

        Returns:
            ProvincialTaxResult with full calculation breakdown
        """
        A = annual_taxable_income

        # Find applicable tax bracket
        V, KP = find_tax_bracket(A, self.brackets)

        # Calculate credits
        K1P = self.calculate_k1p(total_claim_amount)
        K2P = self.calculate_k2p(cpp_per_period, ei_per_period, ytd_cpp_base, ytd_ei, pensionable_months)
        K4P = self.calculate_k4p(A)  # Employment credit (Yukon)
        K5P = self.calculate_k5p_alberta(K1P, K2P)

        # Calculate T4 (basic provincial tax)
        T4 = (V * A) - KP - K1P - K2P - K4P - K5P
        T4 = max(T4, Decimal("0"))

        # Initialize special adjustments
        surtax_v1 = Decimal("0")
        health_premium_v2 = Decimal("0")
        tax_reduction_s = Decimal("0")

        # Apply province-specific adjustments
        if self.province_code == "ON":
            surtax_v1 = self._calculate_ontario_surtax(T4)
            health_premium_v2 = self._calculate_ontario_health_premium(A)
            T2 = T4 + surtax_v1 + health_premium_v2

        elif self.province_code == "BC":
            tax_reduction_s = self._calculate_bc_tax_reduction(A)
            T2 = max(T4 - tax_reduction_s, Decimal("0"))

        elif self.province_code == "PE":
            surtax_v1 = self._calculate_pe_surtax(T4)
            T2 = T4 + surtax_v1

        else:
            T2 = T4

        # Round T2 before dividing by pay periods (matches CRA calculation order)
        T2 = self._round(T2)

        # Tax per period
        tax_per_period = self._round(T2 / self.P)

        return ProvincialTaxResult(
            province_code=self.province_code,
            annual_taxable_income=A,
            tax_rate=V,
            constant_kp=KP,
            personal_credits_k1p=K1P,
            cpp_ei_credits_k2p=K2P,
            employment_credit_k4p=K4P,
            supplemental_credit_k5p=K5P,
            basic_provincial_tax_t4=self._round(T4),
            surtax_v1=surtax_v1,
            health_premium_v2=health_premium_v2,
            tax_reduction_s=tax_reduction_s,
            annual_provincial_tax_t2=self._round(T2),
            tax_per_period=tax_per_period,
        )

    def calculate_tax_per_period(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        net_income: Decimal | None = None,
    ) -> Decimal:
        """
        Convenience method for one pay period.

        Args:
            annual_taxable_income: Annualized taxable income
            total_claim_amount: Provincial TD1 claim amount
            cpp_per_period: CPP contribution per period
            ei_per_period: EI premium per period
            net_income: Net income (for Manitoba BPA)

        Returns:
            Provincial tax to deduct this period
        """
        result = self.calculate_provincial_tax(
            annual_taxable_income,
            total_claim_amount,
            cpp_per_period,
            ei_per_period,
            net_income,
        )
        return result.tax_per_period

    def get_calculation_details(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        net_income: Decimal | None = None,
    ) -> dict[str, Any]:
        """
        Get detailed calculation breakdown for debugging/audit.
        """
        result = self.calculate_provincial_tax(
            annual_taxable_income,
            total_claim_amount,
            cpp_per_period,
            ei_per_period,
            net_income,
        )

        return {
            "province": {
                "code": self.province_code,
                "name": self._config.get("name", self.province_code),
                "bpa": str(self.get_basic_personal_amount(annual_taxable_income, net_income)),
                "lowest_rate": str(self.lowest_rate),
                "has_surtax": self.has_surtax,
                "has_health_premium": self.has_health_premium,
                "has_tax_reduction": self.has_tax_reduction,
            },
            "inputs": {
                "annual_taxable_income": str(annual_taxable_income),
                "total_claim_amount": str(total_claim_amount),
                "cpp_per_period": str(cpp_per_period),
                "ei_per_period": str(ei_per_period),
                "pay_periods_per_year": self.P,
            },
            "calculation": {
                "tax_rate_V": str(result.tax_rate),
                "constant_KP": str(result.constant_kp),
                "personal_credits_K1P": str(result.personal_credits_k1p),
                "cpp_ei_credits_K2P": str(result.cpp_ei_credits_k2p),
                "supplemental_credit_K5P": str(result.supplemental_credit_k5p),
            },
            "adjustments": {
                "surtax_V1": str(result.surtax_v1),
                "health_premium_V2": str(result.health_premium_v2),
                "tax_reduction_S": str(result.tax_reduction_s),
            },
            "result": {
                "basic_provincial_tax_T4": str(result.basic_provincial_tax_t4),
                "annual_provincial_tax_T2": str(result.annual_provincial_tax_t2),
                "tax_per_period": str(result.tax_per_period),
            },
            "formula": "T4 = (V × A) - KP - K1P - K2P - K5P",
        }
