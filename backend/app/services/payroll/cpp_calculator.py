"""
CPP (Canada Pension Plan) Calculator

Implements CPP contribution calculations following CRA T4127 Chapter 6.
Includes both base CPP and additional CPP2 (above YMPE).

Reference: T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import NamedTuple

from app.services.payroll.tax_tables import get_cpp_config

logger = logging.getLogger(__name__)


class CppContribution(NamedTuple):
    """CPP contribution breakdown."""
    base: Decimal
    additional: Decimal  # CPP2 (C2)
    f5: Decimal  # F5: CPP deduction from taxable income (F2 + C2) per T4127
    total: Decimal
    employer: Decimal


class CPPCalculator:
    """
    Canada Pension Plan contribution calculator.

    Reference: CRA T4127 Chapter 6

    CPP has two components:
    1. Base CPP: 5.95% on earnings between basic exemption ($3,500) and YMPE ($71,200)
    2. Additional CPP (CPP2): 1.00% on earnings between YMPE ($71,200) and YAMPE ($76,000)

    Both employee and employer pay the same amount.
    """

    def __init__(self, pay_periods_per_year: int = 26, year: int = 2025):
        """
        Initialize CPP calculator.

        Args:
            pay_periods_per_year: Number of pay periods (52=weekly, 26=bi-weekly, etc.)
            year: Tax year for configuration lookup
        """
        self.P = pay_periods_per_year
        self.year = year
        self._config = get_cpp_config(year)

        # Load configuration values as Decimal
        self.ympe = Decimal(str(self._config["ympe"]))
        self.yampe = Decimal(str(self._config["yampe"]))
        self.basic_exemption = Decimal(str(self._config["basic_exemption"]))
        self.base_rate = Decimal(str(self._config["base_rate"]))
        self.additional_rate = Decimal(str(self._config["additional_rate"]))
        self.max_base_contribution = Decimal(str(self._config["max_base_contribution"]))
        self.max_additional_contribution = Decimal(
            str(self._config.get("max_additional_contribution", "396.00"))
        )
        self.max_total_contribution = Decimal(
            str(self._config.get("max_total_contribution", "4430.10"))
        )

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using banker's rounding."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_prorated_max(
        self,
        pensionable_months: int | None = None,
        max_amount: Decimal | None = None,
    ) -> Decimal:
        """
        Get prorated maximum for employees with less than 12 pensionable months.

        Formula: prorated_max = max_annual × (pensionable_months / 12)

        Args:
            pensionable_months: Number of months with pensionable employment (1-12)
            max_amount: The maximum to prorate (default: max_base_contribution)

        Returns:
            Prorated maximum, or full maximum if pensionable_months is None/12
        """
        if max_amount is None:
            max_amount = self.max_base_contribution

        if pensionable_months is None or pensionable_months >= 12:
            return max_amount

        if pensionable_months <= 0:
            return Decimal("0")

        prorated = max_amount * Decimal(pensionable_months) / Decimal("12")
        return self._round(prorated)

    def calculate_base_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_base: Decimal = Decimal("0"),
        pensionable_months: int | None = None,
    ) -> Decimal:
        """
        Calculate base CPP contribution for the pay period.

        Formula from T4127:
        C = base_rate × (PI - (basic_exemption / P))

        Where:
        - PI = Pensionable earnings for the period
        - P = Pay periods per year
        - basic_exemption = $3,500
        - base_rate = 5.95%
        - Maximum annual contribution: $4,034.10 (2025)

        For employees with less than 12 pensionable months, the maximum is prorated.

        Args:
            pensionable_earnings: Gross pensionable earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings (before this period)
            ytd_cpp_base: Year-to-date base CPP contributions (before this period)
            pensionable_months: Months of pensionable employment (for prorated max)

        Returns:
            Base CPP contribution for this period (rounded to 2 decimals)
        """
        # Get prorated maximum if applicable
        effective_max = self.get_prorated_max(pensionable_months)

        # Check if already at annual maximum
        if ytd_cpp_base >= effective_max:
            return Decimal("0")

        # Basic exemption per pay period (T4127: drop 3rd digit)
        exemption_per_period = (self.basic_exemption / self.P).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )

        # Pensionable earnings after exemption
        pensionable_after_exemption = max(
            pensionable_earnings - exemption_per_period,
            Decimal("0")
        )

        # Calculate contribution
        base_cpp = self.base_rate * pensionable_after_exemption

        # Check annual maximum (prorated if applicable)
        if ytd_cpp_base + base_cpp > effective_max:
            base_cpp = max(effective_max - ytd_cpp_base, Decimal("0"))

        return self._round(base_cpp)

    def calculate_additional_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0"),
        cpp2_exempt: bool = False,
        pensionable_months: int | None = None,
    ) -> Decimal:
        """
        Calculate CPP2 (C2) contribution using T4127 formula with W factor.

        Per T4127 (121st Edition, July 2025):

        C2 = lesser of:
           (i)  max_cpp2 × (PM/12) - D2
           (ii) (PIYTD + PI - W) × 0.04

        W = greater of:
           (i)  PIYTD
           (ii) YMPE × (PM/12)

        Where:
        - PIYTD = YTD pensionable income (before this period)
        - PI = Pensionable income for current pay period
        - PM = Pensionable months (1-12)
        - D2 = YTD CPP2 contributions
        - YMPE = Year's Maximum Pensionable Earnings ($71,300 for 2025)
        - max_cpp2 = $396.00 for 2025

        Employees can file CPT30 to be exempt if they have multiple jobs.

        Args:
            pensionable_earnings: Gross pensionable earnings for this period (PI)
            ytd_pensionable_earnings: Year-to-date pensionable earnings before this period (PIYTD)
            ytd_cpp_additional: Year-to-date additional CPP (CPP2) already paid (D2)
            cpp2_exempt: If True, employee is exempt from CPP2 (CPT30 on file)
            pensionable_months: Number of pensionable months in the year (PM, 1-12)

        Returns:
            Additional CPP (C2) contribution for this period
        """
        # Check CPP2 exemption (CPT30 on file)
        if cpp2_exempt:
            return Decimal("0")

        # Default to 12 months if not specified
        PM = Decimal(str(pensionable_months)) if pensionable_months else Decimal("12")

        # Prorated maximum CPP2
        prorated_max = self.max_additional_contribution * PM / Decimal("12")

        # Already at maximum
        if ytd_cpp_additional >= prorated_max:
            return Decimal("0")

        # Calculate W factor per T4127
        # W = max(PIYTD, YMPE × PM/12)
        prorated_ympe = self.ympe * PM / Decimal("12")
        W = max(ytd_pensionable_earnings, prorated_ympe)

        # Option (i): prorated_max - D2
        option_i = prorated_max - ytd_cpp_additional

        # Option (ii): (PIYTD + PI - W) × additional_rate
        earnings_above_w = ytd_pensionable_earnings + pensionable_earnings - W
        option_ii = max(earnings_above_w, Decimal("0")) * self.additional_rate

        # C2 = lesser of option (i) and option (ii)
        cpp2 = min(option_i, option_ii)

        return self._round(max(cpp2, Decimal("0")))

    def calculate_total_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_base: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0"),
        cpp2_exempt: bool = False,
        pensionable_months: int | None = None,
    ) -> CppContribution:
        """
        Calculate both base and additional CPP contributions.

        Args:
            pensionable_earnings: Gross pensionable earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings
            ytd_cpp_base: Year-to-date base CPP contributions
            ytd_cpp_additional: Year-to-date additional CPP (CPP2)
            cpp2_exempt: If True, employee is exempt from CPP2
            pensionable_months: Months of pensionable employment (for prorated max)

        Returns:
            CppContribution namedtuple with base, additional, total, and employer amounts
        """
        base_cpp = self.calculate_base_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_base,
            pensionable_months,
        )

        additional_cpp = self.calculate_additional_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_additional,
            cpp2_exempt,
            pensionable_months,
        )

        total = base_cpp + additional_cpp
        employer = total  # Employer matches employee contribution

        # Calculate F5 (CPP deduction from taxable income) per T4127
        # F5 = C × (0.01/0.0595) + C2
        f5 = self._calculate_f5(base_cpp, additional_cpp)

        return CppContribution(
            base=base_cpp,
            additional=additional_cpp,
            f5=f5,
            total=total,
            employer=employer,
        )

    def _calculate_f5(self, base_cpp: Decimal, cpp2: Decimal) -> Decimal:
        """
        Calculate F5 (CPP deduction from taxable income).

        Per T4127: F5 = C × (0.01 / 0.0595) + C2

        Where:
        - C = base CPP contribution for the period
        - C2 = CPP2 contribution for the period

        F5 is the total CPP-related deduction from taxable income,
        consisting of both the enhancement portion (F2) and CPP2 (C2).

        Args:
            base_cpp: Base CPP contribution for this period (C)
            cpp2: CPP2 contribution for this period (C2)

        Returns:
            F5: Total CPP deduction from taxable income
        """
        # F2 = C × (0.01 / 0.0595) - the enhancement portion of base CPP
        enhancement_ratio = Decimal("0.01") / Decimal("0.0595")
        f2 = base_cpp * enhancement_ratio

        # F5 = F2 + C2
        f5 = f2 + cpp2

        return self._round(f5)

    def get_employer_contribution(self, employee_cpp: Decimal) -> Decimal:
        """
        Calculate employer CPP contribution.

        Employer contribution matches employee contribution exactly.

        Args:
            employee_cpp: Total employee CPP (base + additional)

        Returns:
            Employer CPP contribution (same as employee)
        """
        return employee_cpp

    def get_base_cpp_credit_rate(self) -> Decimal:
        """
        Get the rate used for calculating CPP tax credits.

        The tax credit is based on the base CPP rate (5.95%),
        but the credit calculation uses 4.95% (the rate before
        the enhancement was added).

        This is used in K2 calculation for tax credits.

        Returns:
            The pre-enhancement CPP rate (0.0495)
        """
        # The CPP tax credit is based on 4.95%, not the full 5.95%
        # because the enhancement portion (1%) doesn't qualify for the credit
        return Decimal("0.0495")

    def get_cpp_credit_ratio(self) -> Decimal:
        """
        Get the ratio for CPP credit calculation.

        Used in K2 calculation: CPP credit = rate × (P × C × credit_ratio)

        Returns:
            The ratio of credit rate to total base rate (0.0495 / 0.0595)
        """
        return self.get_base_cpp_credit_rate() / self.base_rate
