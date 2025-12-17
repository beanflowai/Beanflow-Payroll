"""
EI (Employment Insurance) Calculator

Implements EI premium calculations following CRA T4127 Chapter 7.

Reference: T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from app.services.payroll.tax_tables import get_ei_config

logger = logging.getLogger(__name__)


class EiPremium(NamedTuple):
    """EI premium breakdown."""
    employee: Decimal
    employer: Decimal


class EICalculator:
    """
    Employment Insurance premium calculator.

    Reference: CRA T4127 Chapter 7

    EI premiums:
    - Employee rate: 1.64% on insurable earnings up to MIE ($65,700)
    - Employer rate: 1.4 × employee rate
    - Maximum employee premium: $1,077.48 (2025)
    - Maximum employer premium: $1,508.47 (2025)
    """

    def __init__(self, pay_periods_per_year: int = 26, year: int = 2025):
        """
        Initialize EI calculator.

        Args:
            pay_periods_per_year: Number of pay periods (52=weekly, 26=bi-weekly, etc.)
            year: Tax year for configuration lookup
        """
        self.P = pay_periods_per_year
        self.year = year
        self._config = get_ei_config(year)

        # Load configuration values as Decimal
        self.mie = Decimal(str(self._config["mie"]))  # Maximum Insurable Earnings
        self.employee_rate = Decimal(str(self._config["employee_rate"]))
        self.employer_rate_multiplier = Decimal(str(self._config["employer_rate_multiplier"]))
        self.max_employee_premium = Decimal(str(self._config["max_employee_premium"]))
        self.max_employer_premium = Decimal(
            str(self._config.get("max_employer_premium", "1508.47"))
        )

        # Calculate employer rate
        self.employer_rate = self.employee_rate * self.employer_rate_multiplier

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using banker's rounding."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_ei_premium(
        self,
        insurable_earnings: Decimal,
        ytd_insurable_earnings: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Calculate employee EI premium for the pay period.

        Formula: EI = employee_rate × IE

        Where:
        - IE = Insurable earnings for the period
        - employee_rate = 1.64% (2025)
        - Maximum insurable earnings: $65,700 (2025)
        - Maximum annual premium: $1,077.48 (2025)

        Args:
            insurable_earnings: Insurable earnings for this period
            ytd_insurable_earnings: Year-to-date insurable earnings (before this period)
            ytd_ei: Year-to-date EI premiums (before this period)

        Returns:
            EI premium for this period
        """
        # Check if already at annual maximum
        if ytd_ei >= self.max_employee_premium:
            return Decimal("0")

        # Check if YTD insurable earnings exceed maximum
        if ytd_insurable_earnings >= self.mie:
            return Decimal("0")

        # Calculate how much insurable earnings remain for this year
        remaining_insurable = self.mie - ytd_insurable_earnings
        earnings_to_insure = min(insurable_earnings, remaining_insurable)

        # Calculate premium for this period
        ei_premium = self.employee_rate * earnings_to_insure

        # Ensure we don't exceed annual maximum
        if ytd_ei + ei_premium > self.max_employee_premium:
            ei_premium = max(self.max_employee_premium - ytd_ei, Decimal("0"))

        return self._round(ei_premium)

    def calculate_employer_premium(self, employee_ei: Decimal) -> Decimal:
        """
        Calculate employer EI premium.

        Employer rate is 1.4 times the employee rate.

        Args:
            employee_ei: Employee EI premium

        Returns:
            Employer EI premium
        """
        # Employer pays 1.4x the employee premium
        employer_premium = employee_ei * self.employer_rate_multiplier
        return self._round(employer_premium)

    def calculate_total_premium(
        self,
        insurable_earnings: Decimal,
        ytd_insurable_earnings: Decimal = Decimal("0"),
        ytd_ei: Decimal = Decimal("0"),
    ) -> EiPremium:
        """
        Calculate both employee and employer EI premiums.

        Args:
            insurable_earnings: Insurable earnings for this period
            ytd_insurable_earnings: Year-to-date insurable earnings
            ytd_ei: Year-to-date EI premiums (employee portion)

        Returns:
            EiPremium namedtuple with employee and employer amounts
        """
        employee_ei = self.calculate_ei_premium(
            insurable_earnings,
            ytd_insurable_earnings,
            ytd_ei,
        )
        employer_ei = self.calculate_employer_premium(employee_ei)

        return EiPremium(employee=employee_ei, employer=employer_ei)

    def get_remaining_annual_premium(self, ytd_ei: Decimal) -> Decimal:
        """
        Get remaining EI premium room for the year.

        Useful for employees to know how much more they'll pay.

        Args:
            ytd_ei: Year-to-date EI premiums

        Returns:
            Remaining annual EI premium
        """
        return max(self.max_employee_premium - ytd_ei, Decimal("0"))

    def is_at_annual_maximum(self, ytd_ei: Decimal) -> bool:
        """
        Check if employee has reached annual EI maximum.

        Args:
            ytd_ei: Year-to-date EI premiums

        Returns:
            True if at or above annual maximum
        """
        return ytd_ei >= self.max_employee_premium
