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
from decimal import Decimal

from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator

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
    ) -> BonusTaxResult:
        """
        Calculate federal and provincial tax on a bonus payment.

        Uses marginal rate method: Tax(Annual Gross + Bonus) - Tax(Annual Gross)
        """
        # Note: ytd_taxable_income passed from engine is actually the base ANNUAL GROSS
        # (annualized regular + prior bonuses)
        base_annual_gross = ytd_taxable_income

        # Annualize deductions
        annual_rrsp = rrsp_per_period * Decimal(str(self.pay_periods))
        annual_union_dues = union_dues_per_period * Decimal(str(self.pay_periods))

        # Use current claims for YTD if not specified
        if federal_claim_amount_ytd is None:
            federal_claim_amount_ytd = federal_claim_amount
        if provincial_claim_amount_ytd is None:
            provincial_claim_amount_ytd = provincial_claim_amount

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
