"""
Benefits Calculator for Payroll Run

Handles calculation of group benefits deductions and taxable benefits.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


class BenefitsCalculator:
    """Calculates group benefits deductions and taxable benefits."""

    @staticmethod
    def calculate_benefits_deduction(group_benefits: dict[str, Any]) -> Decimal:
        """Calculate total employee benefits deduction from group benefits config.

        This calculates the post-tax employee deduction amount for all enabled benefits.

        Args:
            group_benefits: Group benefits configuration dict

        Returns:
            Total employee deduction amount
        """
        if not group_benefits.get("enabled"):
            return Decimal("0")

        benefits_deduction = Decimal("0")

        # Health
        health = group_benefits.get("health") or {}
        if health.get("enabled"):
            benefits_deduction += Decimal(str(health.get("employeeDeduction", 0)))

        # Dental
        dental = group_benefits.get("dental") or {}
        if dental.get("enabled"):
            benefits_deduction += Decimal(str(dental.get("employeeDeduction", 0)))

        # Life Insurance
        life = group_benefits.get("lifeInsurance") or {}
        if life.get("enabled"):
            benefits_deduction += Decimal(str(life.get("employeeDeduction", 0)))

        # Vision
        vision = group_benefits.get("vision") or {}
        if vision.get("enabled"):
            benefits_deduction += Decimal(str(vision.get("employeeDeduction", 0)))

        # Disability
        disability = group_benefits.get("disability") or {}
        if disability.get("enabled"):
            benefits_deduction += Decimal(str(disability.get("employeeDeduction", 0)))

        return benefits_deduction

    @staticmethod
    def calculate_taxable_benefits(group_benefits: dict[str, Any]) -> Decimal:
        """Calculate taxable benefits that are pensionable but NOT insurable.

        In Canada, only employer-paid life insurance premiums have this special
        treatment (pensionable for CPP, but NOT insurable for EI).

        Other benefit types (health, dental, vision, disability) are generally
        NOT taxable in Canada. If they were taxable, they would be both
        pensionable AND insurable, but that's extremely rare.

        We only check lifeInsurance.isTaxable to avoid incorrect CPP/EI
        calculations for other benefit types.

        Args:
            group_benefits: Group benefits configuration dict

        Returns:
            Total taxable benefits amount (pensionable but not insurable)
        """
        if not group_benefits.get("enabled"):
            return Decimal("0")

        taxable_benefits = Decimal("0")

        # Only life insurance has the special "pensionable but not insurable" treatment
        # Employer-paid life insurance is ALWAYS a taxable benefit in Canada (CRA rule)
        life = group_benefits.get("lifeInsurance") or {}
        if life.get("enabled"):
            employer_contribution = Decimal(str(life.get("employerContribution", 0)))
            if employer_contribution > 0:
                taxable_benefits += employer_contribution

        return taxable_benefits
