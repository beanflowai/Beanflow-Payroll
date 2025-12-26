"""
CPP (Canada Pension Plan) Calculator

Implements CPP contribution calculations following CRA T4127 Chapter 6.
Includes both base CPP and additional CPP2 (above YMPE).

Reference: T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from app.services.payroll.tax_tables import get_cpp_config

logger = logging.getLogger(__name__)


class CppContribution(NamedTuple):
    """CPP contribution breakdown."""
    base: Decimal
    additional: Decimal  # CPP2
    enhancement: Decimal  # F2: 1% enhancement portion (deductible from taxable income)
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

    def calculate_base_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_base: Decimal = Decimal("0"),
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

        Args:
            pensionable_earnings: Gross pensionable earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings (before this period)
            ytd_cpp_base: Year-to-date base CPP contributions (before this period)

        Returns:
            Base CPP contribution for this period (rounded to 2 decimals)
        """
        # Check if already at annual maximum
        if ytd_cpp_base >= self.max_base_contribution:
            return Decimal("0")

        # Basic exemption per pay period
        exemption_per_period = self.basic_exemption / self.P

        # Pensionable earnings after exemption
        pensionable_after_exemption = max(
            pensionable_earnings - exemption_per_period,
            Decimal("0")
        )

        # Calculate contribution
        base_cpp = self.base_rate * pensionable_after_exemption

        # Check annual maximum
        if ytd_cpp_base + base_cpp > self.max_base_contribution:
            base_cpp = max(self.max_base_contribution - ytd_cpp_base, Decimal("0"))

        return self._round(base_cpp)

    def calculate_additional_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0"),
        cpp2_exempt: bool = False,
    ) -> Decimal:
        """
        Calculate additional CPP (CPP2) contribution.

        Formula from T4127:
        C2 = additional_rate × max(0, PI - (YMPE / P))

        Where:
        - YMPE = Year's Maximum Pensionable Earnings ($71,200)
        - YAMPE = Year's Additional Maximum ($76,000)
        - additional_rate = 1.00%
        - Maximum annual CPP2: $396.00 (2025)

        CPP2 only applies on earnings between YMPE and YAMPE.
        Employees can file CPT30 to be exempt if they have multiple jobs.

        Args:
            pensionable_earnings: Gross pensionable earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings
            ytd_cpp_additional: Year-to-date additional CPP (CPP2)
            cpp2_exempt: If True, employee is exempt from CPP2 (CPT30 on file)

        Returns:
            Additional CPP contribution for this period
        """
        # Check CPP2 exemption (CPT30 on file)
        if cpp2_exempt:
            return Decimal("0")

        # Check if already at annual maximum
        if ytd_cpp_additional >= self.max_additional_contribution:
            return Decimal("0")

        # YMPE and YAMPE per pay period
        ympe_per_period = self.ympe / self.P
        yampe_per_period = self.yampe / self.P

        # Earnings subject to CPP2 (above YMPE, up to YAMPE)
        if pensionable_earnings > ympe_per_period:
            cpp2_earnings = min(
                pensionable_earnings - ympe_per_period,
                yampe_per_period - ympe_per_period
            )
            cpp2 = self.additional_rate * cpp2_earnings
        else:
            cpp2 = Decimal("0")

        # Check annual maximum
        if ytd_cpp_additional + cpp2 > self.max_additional_contribution:
            cpp2 = max(self.max_additional_contribution - ytd_cpp_additional, Decimal("0"))

        return self._round(cpp2)

    def calculate_total_cpp(
        self,
        pensionable_earnings: Decimal,
        ytd_pensionable_earnings: Decimal = Decimal("0"),
        ytd_cpp_base: Decimal = Decimal("0"),
        ytd_cpp_additional: Decimal = Decimal("0"),
        cpp2_exempt: bool = False,
    ) -> CppContribution:
        """
        Calculate both base and additional CPP contributions.

        Args:
            pensionable_earnings: Gross pensionable earnings for this period
            ytd_pensionable_earnings: Year-to-date pensionable earnings
            ytd_cpp_base: Year-to-date base CPP contributions
            ytd_cpp_additional: Year-to-date additional CPP (CPP2)
            cpp2_exempt: If True, employee is exempt from CPP2

        Returns:
            CppContribution namedtuple with base, additional, total, and employer amounts
        """
        base_cpp = self.calculate_base_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_base,
        )

        additional_cpp = self.calculate_additional_cpp(
            pensionable_earnings,
            ytd_pensionable_earnings,
            ytd_cpp_additional,
            cpp2_exempt,
        )

        total = base_cpp + additional_cpp
        employer = total  # Employer matches employee contribution

        # Calculate F2 (CPP enhancement portion) - deductible from taxable income
        # Enhancement = Total CPP × (1% / 5.95%) per T4127
        enhancement = self._calculate_enhancement(base_cpp)

        return CppContribution(
            base=base_cpp,
            additional=additional_cpp,
            enhancement=enhancement,
            total=total,
            employer=employer,
        )

    def _calculate_enhancement(self, base_cpp: Decimal) -> Decimal:
        """
        Calculate CPP enhancement portion (F2) - deductible from taxable income.

        Per T4127: The CPP enhancement (1% of 5.95% total rate) is deductible
        from income when calculating taxable income for tax purposes.

        Formula: F2 = base_cpp × (0.01 / 0.0595)

        Note: Enhancement is calculated from base CPP only, not CPP2 (additional).

        Args:
            base_cpp: Base CPP contribution for this period

        Returns:
            CPP enhancement portion (F2) for this period
        """
        # Enhancement rate is 1%, total base rate is 5.95%
        enhancement_ratio = Decimal("0.01") / Decimal("0.0595")
        return self._round(base_cpp * enhancement_ratio)

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
