"""
Bonus Tax Calculator

Implements CRA T4127 Bonus Tax Method for lump-sum payments.
Uses marginal rate method: Tax(YTD + Bonus) - Tax(YTD)

This method correctly taxes bonuses at their marginal rate instead of
incorrectly annualizing them, which would over-tax the bonus.

Reference: CRA T4127 Payroll Deductions Formulas (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator
from app.services.payroll.tax_tables import find_tax_bracket

logger = logging.getLogger(__name__)


@dataclass
class BonusTaxResult:
    """Bonus tax calculation result with breakdown."""

    bonus_amount: Decimal
    ytd_taxable_income: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    total_tax: Decimal

    # Breakdown for audit
    federal_tax_on_ytd: Decimal
    federal_tax_on_total: Decimal
    provincial_tax_on_ytd: Decimal
    provincial_tax_on_total: Decimal


class BonusTaxCalculator:
    """
    Calculate tax on bonus payments using CRA T4127 Bonus Method.

    The Bonus Method calculates the marginal tax rate on a lump-sum payment:
    Bonus Tax = Tax(YTD + Bonus) - Tax(YTD)

    This differs from the annualization method, which incorrectly treats
    bonus as recurring income:
    - Annualization: Tax = [Rate × (Bonus × Pay Periods)] / Pay Periods
    - Bonus Method: Tax = Tax(YTD + Bonus) - Tax(YTD)

    Example:
    - $60,000 bonus, $76,333 YTD, bi-weekly pay
    - Annualization: $60K × 26 = $1.56M "annual income" → highest bracket
    - Bonus Method: Tax($136,333) - Tax($76,333) = actual marginal tax

    Reference: CRA T4127 Bonus/Retroactive Pay Method
    """

    def __init__(
        self,
        province_code: str,
        pay_periods_per_year: int = 26,
        year: int = 2025,
        pay_date: date | None = None,
    ):
        """
        Initialize bonus tax calculator.

        Args:
            province_code: Two-letter province code (e.g., "ON", "BC")
            pay_periods_per_year: Number of pay periods (26=bi-weekly, etc.)
            year: Tax year
            pay_date: Pay date (for tax edition selection)
        """
        self.province_code = province_code
        self.pay_periods = pay_periods_per_year
        self.year = year
        self.pay_date = pay_date

        # Create tax calculators for annual tax calculations
        self.federal_calc = FederalTaxCalculator(
            pay_periods_per_year=pay_periods_per_year,
            year=year,
            pay_date=pay_date,
        )
        self.provincial_calc = ProvincialTaxCalculator(
            province_code=province_code,
            pay_periods_per_year=pay_periods_per_year,
            year=year,
            pay_date=pay_date,
        )
        self._cpp_config = self.federal_calc._cpp_config
        self._ei_config = self.federal_calc._ei_config

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using CRA rounding rules."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _calculate_k2_from_annual(
        self,
        annual_cpp_base: Decimal,
        annual_ei: Decimal,
        is_federal: bool,
        pensionable_months: int | None = None,
    ) -> Decimal:
        """
        Calculate K2/K2P from annual CPP/EI amounts (bonus method).
        """
        if is_federal:
            rate = self.federal_calc.k2_rate
            max_cpp = self.federal_calc.max_cpp_credit
            max_ei = self.federal_calc.max_ei_credit
            cpp_ratio = self.federal_calc.cpp_credit_ratio
        else:
            rate = self.provincial_calc.lowest_rate
            max_cpp = self.provincial_calc.max_cpp_credit
            max_ei = self.provincial_calc.max_ei_credit
            cpp_ratio = self.provincial_calc.cpp_credit_ratio

        pm = Decimal(str(pensionable_months)) if pensionable_months else Decimal("12")
        max_cpp_credit = max_cpp * cpp_ratio * pm / Decimal("12")
        # T4127: EI maximum is NOT prorated by PM (only CPP is)
        max_ei_credit = max_ei

        cpp_credit = min(annual_cpp_base * cpp_ratio, max_cpp_credit)
        cpp_credit = self._round(cpp_credit)
        ei_credit = min(annual_ei, max_ei_credit)
        ei_credit = self._round(ei_credit)

        return self._round(rate * (cpp_credit + ei_credit))

    def _calculate_federal_tax_raw_with_k2(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        k2_override: Decimal,
        k3: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Calculate annual federal tax (raw, unrounded T1) with K2 override.
        """
        rate, constant = find_tax_bracket(annual_taxable_income, self.federal_calc.brackets)
        k1 = self.federal_calc.calculate_k1(total_claim_amount)
        k4 = self.federal_calc.calculate_k4(annual_taxable_income)

        t3_raw = (rate * annual_taxable_income) - constant - k1 - k2_override - k3 - k4
        return max(t3_raw, Decimal("0"))

    def _calculate_provincial_tax_raw_with_k2(
        self,
        annual_taxable_income: Decimal,
        total_claim_amount: Decimal,
        k2_override: Decimal,
        net_income: Decimal | None = None,
    ) -> Decimal:
        """
        Calculate annual provincial tax (raw, unrounded T2) with K2 override.
        """
        rate, constant = find_tax_bracket(annual_taxable_income, self.provincial_calc.brackets)
        k1p = self.provincial_calc.calculate_k1p(total_claim_amount)
        k4p = self.provincial_calc.calculate_k4p(annual_taxable_income)
        k5p = self.provincial_calc.calculate_k5p_alberta(k1p, k2_override)

        t4_raw = (
            (rate * annual_taxable_income)
            - constant
            - k1p
            - k2_override
            - k4p
            - k5p
        )
        t4_raw = max(t4_raw, Decimal("0"))

        if self.province_code == "ON" and self.provincial_calc.has_surtax:
            surtax = self.provincial_calc._calculate_ontario_surtax(t4_raw)
            health = self.provincial_calc._calculate_ontario_health_premium(annual_taxable_income)
            t2_raw = t4_raw + surtax + health
        elif self.province_code == "BC" and self.provincial_calc.has_tax_reduction:
            reduction = self.provincial_calc._calculate_bc_tax_reduction(annual_taxable_income)
            t2_raw = t4_raw - reduction
        elif self.province_code == "PE" and self.provincial_calc.has_surtax:
            surtax = self.provincial_calc._calculate_pe_surtax(t4_raw)
            t2_raw = t4_raw + surtax
        else:
            t2_raw = t4_raw

        return max(t2_raw, Decimal("0"))

    def _calculate_annual_tax_for_gross(
        self,
        annual_gross: Decimal,
        total_claim_amount: Decimal,
        is_federal: bool,
        pensionable_months: int | None = None,
        annual_rrsp: Decimal = Decimal("0"),
        annual_union_dues: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Calculate annual tax for a given annual gross income,
        accounting for CPP/EI credits, F5 deductions, RRSP, and union dues.
        """
        calc = self.federal_calc if is_federal else self.provincial_calc
        cpp_config = calc._cpp_config
        ei_config = calc._ei_config

        # 1. Calculate expected annual CPP
        exemption = Decimal(str(cpp_config["basic_exemption"]))
        base_rate = Decimal(str(cpp_config["base_rate"]))
        max_base = calc.max_cpp_credit

        annual_cpp_base = max((annual_gross - exemption) * base_rate, Decimal("0"))
        annual_cpp_base = min(annual_cpp_base, max_base)

        # 2. Calculate expected annual CPP2
        ympe = Decimal(str(cpp_config["ympe"]))
        yampe = Decimal(str(cpp_config["yampe"]))
        cpp2_rate = Decimal(str(cpp_config["additional_rate"]))
        max_cpp2 = Decimal(str(cpp_config.get("max_additional_contribution", "396.00")))

        if annual_gross > ympe:
            annual_cpp2 = (min(annual_gross, yampe) - ympe) * cpp2_rate
            annual_cpp2 = min(annual_cpp2, max_cpp2)
        else:
            annual_cpp2 = Decimal("0")

        # 3. Calculate F5 deduction
        # F5 = base_cpp * (0.01/0.0595) + cpp2
        f2 = annual_cpp_base * (Decimal("0.01") / Decimal("0.0595"))
        f5 = f2 + annual_cpp2

        # 4. Calculate expected annual EI
        ei_rate = Decimal(str(ei_config["employee_rate"]))
        max_ei = calc.max_ei_credit
        annual_ei = min(annual_gross * ei_rate, max_ei)

        # 5. Determine Taxable Income (Factor A)
        # Factor A = Gross - F5 - RRSP - Union Dues
        annual_taxable = max(annual_gross - f5 - annual_rrsp - annual_union_dues, Decimal("0"))

        if is_federal:
            result = self.federal_calc.calculate_federal_tax(
                annual_taxable_income=annual_taxable,
                total_claim_amount=total_claim_amount,
                cpp_per_period=annual_cpp_base / Decimal(str(self.pay_periods)),
                ei_per_period=annual_ei / Decimal(str(self.pay_periods)),
                ytd_cpp_base=Decimal("0"),
                ytd_ei=Decimal("0"),
                pensionable_months=pensionable_months,
            )
            return result.annual_federal_tax_t1
        else:
            result = self.provincial_calc.calculate_provincial_tax(
                annual_taxable_income=annual_taxable,
                total_claim_amount=total_claim_amount,
                cpp_per_period=annual_cpp_base / Decimal(str(self.pay_periods)),
                ei_per_period=annual_ei / Decimal(str(self.pay_periods)),
                ytd_cpp_base=Decimal("0"),
                ytd_ei=Decimal("0"),
                pensionable_months=pensionable_months,
            )
            return result.annual_provincial_tax_t2


    def calculate_bonus_tax(
        self,
        bonus_amount: Decimal,
        ytd_taxable_income: Decimal,
        ytd_cpp: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0"),
        federal_claim_amount: Decimal = Decimal("0"),
        provincial_claim_amount: Decimal = Decimal("0"),
        federal_claim_amount_ytd: Decimal | None = None,
        provincial_claim_amount_ytd: Decimal | None = None,
        pensionable_months: int | None = None,
        rrsp_per_period: Decimal = Decimal("0"),
        union_dues_per_period: Decimal = Decimal("0"),
        regular_gross_per_period: Decimal | None = None,
        ytd_bonus_earnings: Decimal | None = None,
        total_cpp_base_per_period: Decimal | None = None,
        regular_cpp_base_per_period: Decimal | None = None,
        total_ei_per_period: Decimal | None = None,
        regular_ei_per_period: Decimal | None = None,
        f5a_per_period: Decimal | None = None,
        f5b_per_period: Decimal | None = None,
        f5b_ytd: Decimal = Decimal("0"),
    ) -> BonusTaxResult:
        """
        Calculate federal and provincial tax on a bonus payment.

        Uses marginal rate method: Tax(Annual Gross + Bonus) - Tax(Annual Gross)
        """
        if bonus_amount <= Decimal("0"):
            return BonusTaxResult(
                bonus_amount=bonus_amount,
                ytd_taxable_income=ytd_taxable_income,
                federal_tax=Decimal("0"),
                provincial_tax=Decimal("0"),
                total_tax=Decimal("0"),
                federal_tax_on_ytd=Decimal("0"),
                federal_tax_on_total=Decimal("0"),
                provincial_tax_on_ytd=Decimal("0"),
                provincial_tax_on_total=Decimal("0"),
            )

        # Note: ytd_taxable_income passed from engine is actually the base ANNUAL GROSS
        # (annualized regular + prior bonuses)
        base_annual_gross = ytd_taxable_income

        # Use current claims for YTD if not specified
        if federal_claim_amount_ytd is None:
            federal_claim_amount_ytd = federal_claim_amount
        if provincial_claim_amount_ytd is None:
            provincial_claim_amount_ytd = provincial_claim_amount

        use_t4127 = all(
            value is not None
            for value in [
                regular_gross_per_period,
                total_cpp_base_per_period,
                regular_cpp_base_per_period,
                total_ei_per_period,
                regular_ei_per_period,
                f5a_per_period,
                f5b_per_period,
            ]
        )

        if use_t4127:
            if ytd_bonus_earnings is None:
                ytd_bonus_earnings = Decimal("0")

            periods = Decimal(str(self.pay_periods))
            regular_annual = periods * (
                regular_gross_per_period
                - rrsp_per_period
                - union_dues_per_period
                - f5a_per_period
            )
            regular_annual = max(regular_annual, Decimal("0"))

            bonus_net = max(bonus_amount - f5b_per_period, Decimal("0"))
            bonus_ytd_net = max(ytd_bonus_earnings - f5b_ytd, Decimal("0"))

            annual_with_bonus = self._round(regular_annual + bonus_net + bonus_ytd_net)
            annual_without_bonus = self._round(regular_annual + bonus_ytd_net)

            bonus_cpp_base = max(
                total_cpp_base_per_period - regular_cpp_base_per_period,
                Decimal("0"),
            )
            bonus_ei = max(
                total_ei_per_period - regular_ei_per_period,
                Decimal("0"),
            )

            cpp_base_rate = Decimal(str(self._cpp_config["base_rate"]))
            ei_rate = Decimal(str(self._ei_config["employee_rate"]))
            ytd_bonus_cpp = self._round(cpp_base_rate * ytd_bonus_earnings)
            ytd_bonus_ei = self._round(ei_rate * ytd_bonus_earnings)

            annual_cpp_no_bonus = self._round((periods * regular_cpp_base_per_period) + ytd_bonus_cpp)
            annual_cpp_with_bonus = self._round(
                (periods * regular_cpp_base_per_period) + bonus_cpp_base + ytd_bonus_cpp
            )
            annual_ei_no_bonus = self._round((periods * regular_ei_per_period) + ytd_bonus_ei)
            annual_ei_with_bonus = self._round(
                (periods * regular_ei_per_period) + bonus_ei + ytd_bonus_ei
            )

            federal_k2_ytd = self._calculate_k2_from_annual(
                annual_cpp_no_bonus,
                annual_ei_no_bonus,
                is_federal=True,
                pensionable_months=pensionable_months,
            )
            federal_k2_total = self._calculate_k2_from_annual(
                annual_cpp_with_bonus,
                annual_ei_with_bonus,
                is_federal=True,
                pensionable_months=pensionable_months,
            )
            provincial_k2_ytd = self._calculate_k2_from_annual(
                annual_cpp_no_bonus,
                annual_ei_no_bonus,
                is_federal=False,
                pensionable_months=pensionable_months,
            )
            provincial_k2_total = self._calculate_k2_from_annual(
                annual_cpp_with_bonus,
                annual_ei_with_bonus,
                is_federal=False,
                pensionable_months=pensionable_months,
            )

            federal_tax_on_ytd_raw = self._calculate_federal_tax_raw_with_k2(
                annual_without_bonus,
                federal_claim_amount_ytd,
                federal_k2_ytd,
            )
            federal_tax_on_total_raw = self._calculate_federal_tax_raw_with_k2(
                annual_with_bonus,
                federal_claim_amount,
                federal_k2_total,
            )
            provincial_tax_on_ytd_raw = self._calculate_provincial_tax_raw_with_k2(
                annual_without_bonus,
                provincial_claim_amount_ytd,
                provincial_k2_ytd,
            )
            provincial_tax_on_total_raw = self._calculate_provincial_tax_raw_with_k2(
                annual_with_bonus,
                provincial_claim_amount,
                provincial_k2_total,
            )

            federal_tax = self._round(
                max(federal_tax_on_total_raw - federal_tax_on_ytd_raw, Decimal("0"))
            )
            provincial_tax = self._round(
                max(provincial_tax_on_total_raw - provincial_tax_on_ytd_raw, Decimal("0"))
            )
            total_tax = federal_tax + provincial_tax

            federal_tax_on_ytd = self._round(federal_tax_on_ytd_raw)
            federal_tax_on_total = self._round(federal_tax_on_ytd + federal_tax)
            provincial_tax_on_ytd = self._round(provincial_tax_on_ytd_raw)
            provincial_tax_on_total = self._round(provincial_tax_on_ytd + provincial_tax)
        else:
            # Annualize deductions for legacy method
            annual_rrsp = rrsp_per_period * Decimal(str(self.pay_periods))
            annual_union_dues = union_dues_per_period * Decimal(str(self.pay_periods))

            # Step 1: Calculate tax on base annual income (A without current bonus)
            federal_tax_on_ytd = self._calculate_annual_tax_for_gross(
                annual_gross=base_annual_gross,
                total_claim_amount=federal_claim_amount_ytd,
                is_federal=True,
                pensionable_months=pensionable_months,
                annual_rrsp=annual_rrsp,
                annual_union_dues=annual_union_dues,
            )
            provincial_tax_on_ytd = self._calculate_annual_tax_for_gross(
                annual_gross=base_annual_gross,
                total_claim_amount=provincial_claim_amount_ytd,
                is_federal=False,
                pensionable_months=pensionable_months,
                annual_rrsp=annual_rrsp,
                annual_union_dues=annual_union_dues,
            )

            # Step 2: Calculate tax on (A + current bonus B)
            total_annual_gross = base_annual_gross + bonus_amount
            federal_tax_on_total = self._calculate_annual_tax_for_gross(
                annual_gross=total_annual_gross,
                total_claim_amount=federal_claim_amount,
                is_federal=True,
                pensionable_months=pensionable_months,
                annual_rrsp=annual_rrsp,
                annual_union_dues=annual_union_dues,
            )
            provincial_tax_on_total = self._calculate_annual_tax_for_gross(
                annual_gross=total_annual_gross,
                total_claim_amount=provincial_claim_amount,
                is_federal=False,
                pensionable_months=pensionable_months,
                annual_rrsp=annual_rrsp,
                annual_union_dues=annual_union_dues,
            )

            # Step 3: Bonus tax = difference (marginal tax)
            federal_tax = max(federal_tax_on_total - federal_tax_on_ytd, Decimal("0"))
            provincial_tax = max(provincial_tax_on_total - provincial_tax_on_ytd, Decimal("0"))
            total_tax = federal_tax + provincial_tax

        return BonusTaxResult(
            bonus_amount=bonus_amount,
            ytd_taxable_income=base_annual_gross,
            federal_tax=federal_tax,
            provincial_tax=provincial_tax,
            total_tax=total_tax,
            federal_tax_on_ytd=federal_tax_on_ytd,
            federal_tax_on_total=federal_tax_on_total,
            provincial_tax_on_ytd=provincial_tax_on_ytd,
            provincial_tax_on_total=provincial_tax_on_total,
        )
