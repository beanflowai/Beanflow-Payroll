"""
Retroactive Pay Tax Calculator

Implements CRA T4127 Retroactive Pay Tax Method.
Uses marginal rate method: Tax(YTD + Retro) - Tax(YTD)

Reference: CRA T4127 Payroll Deductions Formulas (122nd Edition, January 2026)
Based on debug_t4127_retroactive_pay.py implementation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from app.services.payroll.tax_tables import (
    find_tax_bracket,
    get_cpp_config,
    get_ei_config,
    get_federal_config,
    get_province_config,
)

logger = logging.getLogger(__name__)


@dataclass
class RetroactiveTaxResult:
    """Retroactive pay tax calculation result with breakdown."""

    retroactive_amount: Decimal
    retroactive_periods: int
    federal_tax: Decimal
    provincial_tax: Decimal
    total_tax: Decimal
    # For audit trail
    federal_tax_on_regular: Decimal
    federal_tax_on_total: Decimal
    provincial_tax_on_regular: Decimal
    provincial_tax_on_total: Decimal


class RetroactiveTaxCalculator:
    """
    Calculate tax on retroactive pay using CRA T4127 Retroactive Pay Method.

    The Retroactive Pay Method calculates the marginal tax rate:
    Retroactive Tax = Tax(Annual Regular + Retro) - Tax(Annual Regular)
    """

    def __init__(
        self,
        province_code: str,
        pay_periods_per_year: int = 26,
        year: int = 2025,
        pay_date: date | None = None,
    ):
        """Initialize retroactive tax calculator."""
        self.province_code = province_code
        self.pay_periods = pay_periods_per_year
        self.year = year
        self.pay_date = pay_date

        # Load configurations
        self._cpp_config = get_cpp_config(year)
        self._ei_config = get_ei_config(year)
        self._federal_config = get_federal_config(year, pay_date)
        self._provincial_config = get_province_config(province_code, year, pay_date)

        # CPP constants
        self.cpp_base_rate = Decimal(str(self._cpp_config["base_rate"]))
        self.cpp_base_credit_rate = Decimal(
            str(self._cpp_config.get("base_credit_rate", "0.0495"))
        )
        max_base_contribution = Decimal(str(self._cpp_config["max_base_contribution"]))
        self.cpp_max_base_credit = Decimal(
            str(
                self._cpp_config.get(
                    "max_base_credit",
                    max_base_contribution * (self.cpp_base_credit_rate / self.cpp_base_rate),
                )
            )
        )

        # EI constants
        self.ei_rate = Decimal(str(self._ei_config["employee_rate"]))
        self.ei_max_premium = Decimal(str(self._ei_config["max_employee_premium"]))

        # Federal constants
        self.federal_k1_rate = Decimal(str(self._federal_config["k1_rate"]))
        self.federal_k2_rate = Decimal(
            str(self._federal_config.get("k2_rate", self._federal_config["k2_cpp_ei_rate"]))
        )
        self.federal_k4_rate = Decimal(
            str(self._federal_config.get("k4_rate", self._federal_config["k4_canada_employment_rate"]))
        )
        self.federal_cea = Decimal(str(self._federal_config["cea"]))

        # Provincial constants (use lowest bracket rate)
        lowest_rate = Decimal(str(self._provincial_config["brackets"][0]["rate"]))
        self.provincial_k1_rate = lowest_rate
        self.provincial_k2_rate = lowest_rate
        self.has_surtax = bool(self._provincial_config.get("has_surtax", False))
        self.has_health_premium = bool(
            self._provincial_config.get("has_health_premium", False)
        )

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _clamp_min_zero(self, value: Decimal) -> Decimal:
        """Clamp value to minimum of zero."""
        return value if value > Decimal("0") else Decimal("0")

    def calculate_retroactive_tax(
        self,
        retroactive_amount: Decimal,
        retroactive_periods: int,
        gross_regular: Decimal,
        cpp_per_period: Decimal,
        ei_per_period: Decimal,
        f5_per_period: Decimal,
        federal_claim_amount: Decimal,
        provincial_claim_amount: Decimal,
        regular_cpp_per_period: Decimal | None = None,
        regular_ei_per_period: Decimal | None = None,
        f5a_per_period: Decimal | None = None,
        f5b_per_period: Decimal | None = None,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        pensionable_months: int = 12,
    ) -> RetroactiveTaxResult:
        """
        Calculate federal and provincial tax on a retroactive payment.

        Uses marginal rate method: Tax(Annual Regular + Retro) - Tax(Annual Regular)
        """
        pay_periods = Decimal(str(self.pay_periods))
        pay_months = Decimal(str(pensionable_months))

        if f5a_per_period is None or f5b_per_period is None:
            retro_periods = max(1, retroactive_periods)
            retro_per_period = self._round(
                retroactive_amount / Decimal(str(retro_periods))
            )

            # Calculate F5 split (based on debug script lines 302-309)
            pi = gross_regular + retro_per_period
            if pi > Decimal("0"):
                f5a_per_period = self._round(f5_per_period * ((pi - retro_per_period) / pi))
                f5b_per_period = self._round(f5_per_period * (retro_per_period / pi))
            else:
                f5a_per_period = Decimal("0")
                f5b_per_period = Decimal("0")

        if regular_cpp_per_period is None:
            exemption_per_period = (Decimal(str(self._cpp_config["basic_exemption"])) / pay_periods).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )
            pensionable_after_exemption = max(gross_regular - exemption_per_period, Decimal("0"))
            regular_cpp_per_period = self._round(self.cpp_base_rate * pensionable_after_exemption)
            prorated_max = Decimal(str(self._cpp_config["max_base_contribution"])) * (pay_months / Decimal("12"))
            regular_cpp_per_period = min(regular_cpp_per_period, self._round(prorated_max))

        if regular_ei_per_period is None:
            regular_ei_per_period = self._round(self.ei_rate * gross_regular)

        # Calculate CPP/EI for regular income only
        cpp_regular = regular_cpp_per_period
        ei_regular = regular_ei_per_period
        cpp_bonus = self._clamp_min_zero(cpp_per_period - cpp_regular)
        ei_bonus = self._clamp_min_zero(ei_per_period - ei_regular)

        # Annual taxable income WITHOUT retroactive (Step 2)
        # A = [P × (I - F - F5A - U1)]
        annual_taxable_regular = pay_periods * (
            gross_regular - rrsp_per_period - f5a_per_period - union_dues_per_period
        )
        annual_taxable_regular = self._clamp_min_zero(annual_taxable_regular)
        annual_taxable_regular = self._round(annual_taxable_regular)

        # Annual taxable income WITH retroactive (Step 1)
        # A = regular A + (B - F5B)
        bonus_taxable = self._clamp_min_zero(retroactive_amount - f5b_per_period)
        annual_taxable_with_retro = annual_taxable_regular + bonus_taxable
        annual_taxable_with_retro = self._round(annual_taxable_with_retro)

        # Annual CPP/EI for K2 calculation
        annual_cpp_regular = cpp_regular * pay_periods
        annual_ei_regular = ei_regular * pay_periods
        annual_cpp_with_retro = annual_cpp_regular + cpp_bonus
        annual_ei_with_retro = annual_ei_regular + ei_bonus

        # Calculate Federal Tax (raw annual)
        federal_raw_regular = self._calculate_federal_tax_raw(
            annual_taxable_regular,
            federal_claim_amount,
            annual_cpp_regular,
            annual_ei_regular,
            pay_months,
        )

        federal_raw_with_retro = self._calculate_federal_tax_raw(
            annual_taxable_with_retro,
            federal_claim_amount,
            annual_cpp_with_retro,
            annual_ei_with_retro,
            pay_months,
        )

        # Calculate Provincial Tax (raw annual)
        provincial_raw_regular = self._calculate_provincial_tax_raw(
            annual_taxable_regular,
            provincial_claim_amount,
            annual_cpp_regular,
            annual_ei_regular,
            pay_months,
        )

        provincial_raw_with_retro = self._calculate_provincial_tax_raw(
            annual_taxable_with_retro,
            provincial_claim_amount,
            annual_cpp_with_retro,
            annual_ei_with_retro,
            pay_months,
        )

        # Retroactive tax = marginal difference
        federal_tax = self._round(
            self._clamp_min_zero(federal_raw_with_retro - federal_raw_regular)
        )
        provincial_tax = self._round(
            self._clamp_min_zero(provincial_raw_with_retro - provincial_raw_regular)
        )

        return RetroactiveTaxResult(
            retroactive_amount=retroactive_amount,
            retroactive_periods=retroactive_periods,
            federal_tax=federal_tax,
            provincial_tax=provincial_tax,
            total_tax=federal_tax + provincial_tax,
            federal_tax_on_regular=self._round(federal_raw_regular / pay_periods),
            federal_tax_on_total=self._round(federal_raw_with_retro / pay_periods),
            provincial_tax_on_regular=self._round(provincial_raw_regular / pay_periods),
            provincial_tax_on_total=self._round(provincial_raw_with_retro / pay_periods),
        )

    def _calculate_k2(
        self,
        annual_cpp_contrib: Decimal,
        annual_ei_premium: Decimal,
        k2_rate: Decimal,
        pay_months: Decimal,
    ) -> Decimal:
        """Calculate K2/K2P CPP/EI credits."""
        # CPP base for credit (4.95% not 5.95%)
        cpp_base = self._round(
            annual_cpp_contrib * (self.cpp_base_credit_rate / self.cpp_base_rate)
        )
        cpp_base = min(cpp_base, self.cpp_max_base_credit * (pay_months / Decimal("12")))

        # EI base
        ei_base = min(
            self._round(annual_ei_premium),
            self.ei_max_premium * (pay_months / Decimal("12")),
        )

        return self._round(k2_rate * (cpp_base + ei_base))

    def _calculate_federal_tax_raw(
        self,
        annual_income: Decimal,
        federal_claim: Decimal,
        annual_cpp_contrib: Decimal,
        annual_ei_premium: Decimal,
        pay_months: Decimal,
    ) -> Decimal:
        """Calculate raw annual federal tax (T1)."""
        rate, constant = find_tax_bracket(
            annual_income, self._federal_config["brackets"]
        )

        k1 = self._round(self.federal_k1_rate * federal_claim)
        k2 = self._calculate_k2(
            annual_cpp_contrib, annual_ei_premium, self.federal_k2_rate, pay_months
        )
        k4 = self._round(
            min(self.federal_k4_rate * annual_income, self.federal_k4_rate * self.federal_cea)
        )

        t3_raw = (rate * annual_income) - constant - k1 - k2 - k4
        return self._clamp_min_zero(t3_raw)

    def _calculate_provincial_tax_raw(
        self,
        annual_income: Decimal,
        provincial_claim: Decimal,
        annual_cpp_contrib: Decimal,
        annual_ei_premium: Decimal,
        pay_months: Decimal,
    ) -> Decimal:
        """Calculate raw annual provincial tax (T2)."""
        rate, constant = find_tax_bracket(
            annual_income, self._provincial_config["brackets"]
        )

        k1p = self._round(self.provincial_k1_rate * provincial_claim)
        k2p = self._calculate_k2(
            annual_cpp_contrib, annual_ei_premium, self.provincial_k2_rate, pay_months
        )

        t4_raw = (rate * annual_income) - constant - k1p - k2p
        t4_raw = self._clamp_min_zero(t4_raw)

        # Ontario surtax
        surtax = self._calculate_ontario_surtax(t4_raw)

        # Ontario Health Premium
        health_premium = self._calculate_ontario_health_premium(annual_income)

        return t4_raw + surtax + health_premium

    def _calculate_ontario_surtax(self, t4_raw: Decimal) -> Decimal:
        """Calculate Ontario surtax based on T4 basic tax."""
        if self.province_code != "ON" or not self.has_surtax:
            return Decimal("0")

        config = self._provincial_config.get("surtax_config", {})
        first_threshold = Decimal(str(config.get("first_threshold", "0")))
        first_rate = Decimal(str(config.get("first_rate", "0")))
        second_threshold = Decimal(str(config.get("second_threshold", "0")))
        second_rate = Decimal(str(config.get("second_rate", "0")))

        if t4_raw <= first_threshold:
            return Decimal("0")

        surtax = first_rate * (t4_raw - first_threshold)
        if t4_raw > second_threshold:
            surtax += second_rate * (t4_raw - second_threshold)

        return self._round(self._clamp_min_zero(surtax))

    def _calculate_ontario_health_premium(self, annual_income: Decimal) -> Decimal:
        """Calculate Ontario Health Premium based on annual income."""
        if self.province_code != "ON" or not self.has_health_premium:
            return Decimal("0")

        config = self._provincial_config.get("health_premium_config", {})
        brackets = config.get("brackets", [])

        if not brackets:
            return Decimal("0")

        premium = Decimal("0")

        for i, bracket in enumerate(brackets):
            threshold = Decimal(str(bracket["threshold"]))
            if annual_income >= threshold:
                if "rate" in bracket:
                    base = Decimal(str(bracket.get("base", "0")))
                    rate = Decimal(str(bracket["rate"]))
                    next_threshold = Decimal(
                        str(brackets[i + 1]["threshold"])
                    ) if i + 1 < len(brackets) else annual_income
                    income_in_bracket = min(annual_income, next_threshold) - threshold
                    premium = base + (rate * income_in_bracket)
                else:
                    premium = Decimal(str(bracket.get("premium", "0")))
            else:
                break

        return self._round(premium)
