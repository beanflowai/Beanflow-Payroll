"""
Vacation Manager

Manages vacation balance validation and updates.
Extracted from run_operations.py for better modularity.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class VacationManager:
    """Manages vacation balance validation and updates."""

    def __init__(self, supabase: Any):
        """Initialize vacation manager.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    def validate_balances(self, records: list[dict[str, Any]]) -> list[str]:
        """Validate vacation balances are sufficient for all employees.

        Only validates employees with payout_method = "accrual".

        Args:
            records: List of payroll records with employee data

        Returns:
            List of error messages for employees with insufficient balance
        """
        errors: list[str] = []

        for record in records:
            employee_data = record.get("employees", {})
            vacation_config = employee_data.get("vacation_config") or {}

            # Only validate accrual method employees
            if vacation_config.get("payout_method") != "accrual":
                continue

            vacation_pay_paid = Decimal(str(record.get("vacation_pay_paid", 0)))
            if vacation_pay_paid <= 0:
                continue

            current_balance = Decimal(str(employee_data.get("vacation_balance", 0)))
            if vacation_pay_paid > current_balance:
                name = f"{employee_data.get('first_name')} {employee_data.get('last_name')}"
                errors.append(
                    f"{name}: balance ${current_balance:.2f}, requested ${vacation_pay_paid:.2f}"
                )

        return errors

    async def update_balances(self, records: list[dict[str, Any]]) -> None:
        """Update employee vacation_balance: +accrued -paid.

        Only processes employees with payout_method = "accrual".
        Called during payroll run approval.

        Args:
            records: List of payroll records with employee data
        """
        for record in records:
            employee_data = record.get("employees", {})
            vacation_config = employee_data.get("vacation_config") or {}

            # Only process accrual method employees
            if vacation_config.get("payout_method") != "accrual":
                continue

            vacation_accrued = Decimal(str(record.get("vacation_accrued", 0)))
            vacation_pay_paid = Decimal(str(record.get("vacation_pay_paid", 0)))

            # Skip if no changes
            if vacation_accrued == 0 and vacation_pay_paid == 0:
                continue

            current_balance = Decimal(str(employee_data.get("vacation_balance", 0)))
            new_balance = max(current_balance + vacation_accrued - vacation_pay_paid, Decimal("0"))

            self.supabase.table("employees").update({
                "vacation_balance": float(new_balance)
            }).eq("id", employee_data["id"]).execute()

            logger.info(
                "Updated vacation balance for employee %s %s: $%.2f -> $%.2f (accrued: $%.2f, paid: $%.2f)",
                employee_data.get("first_name"),
                employee_data.get("last_name"),
                float(current_balance),
                float(new_balance),
                float(vacation_accrued),
                float(vacation_pay_paid),
            )
