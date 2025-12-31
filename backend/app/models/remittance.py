"""
Remittance Pydantic Models

Data models for PD7A remittance voucher generation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class PaymentMethod(str, Enum):
    """CRA accepted payment methods."""
    MY_PAYMENT = "my_payment"
    PRE_AUTHORIZED_DEBIT = "pre_authorized_debit"
    ONLINE_BANKING = "online_banking"
    WIRE_TRANSFER = "wire_transfer"
    CHEQUE = "cheque"


class PD7ARemittanceVoucher(BaseModel):
    """
    PD7A Statement of Account for Current Source Deductions.

    Used for generating PDF remittance vouchers.
    """
    # Employer Information
    employer_name: str
    payroll_account_number: str = Field(
        ...,
        min_length=15,
        max_length=15,
        pattern=r"^\d{9}RP\d{4}$",
        description="15-character payroll account (e.g., 123456789RP0001)"
    )

    # Remittance Period
    period_start: date
    period_end: date
    due_date: date

    # Line 10: Current Source Deductions
    line_10_cpp_employee: Decimal = Field(default=Decimal("0"), ge=0)
    line_10_cpp_employer: Decimal = Field(default=Decimal("0"), ge=0)
    line_10_ei_employee: Decimal = Field(default=Decimal("0"), ge=0)
    line_10_ei_employer: Decimal = Field(default=Decimal("0"), ge=0)
    line_10_income_tax: Decimal = Field(default=Decimal("0"), ge=0)

    # Line 12: Previous balance owing (if any)
    line_12_previous_balance: Decimal = Field(default=Decimal("0"), ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_11_total_deductions(self) -> Decimal:
        """Line 11: Total Current Source Deductions."""
        return (
            self.line_10_cpp_employee +
            self.line_10_cpp_employer +
            self.line_10_ei_employee +
            self.line_10_ei_employer +
            self.line_10_income_tax
        ).quantize(Decimal("0.01"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_13_total_due(self) -> Decimal:
        """Line 13: Total Amount Due."""
        return (self.line_11_total_deductions + self.line_12_previous_balance).quantize(Decimal("0.01"))

    model_config = {
        "json_schema_extra": {
            "example": {
                "employerName": "Example Corp",
                "payrollAccountNumber": "123456789RP0001",
                "periodStart": "2025-01-01",
                "periodEnd": "2025-01-31",
                "dueDate": "2025-02-15",
                "line10CppEmployee": "1500.00",
                "line10CppEmployer": "1500.00",
                "line10EiEmployee": "400.00",
                "line10EiEmployer": "560.00",
                "line10IncomeTax": "4200.00"
            }
        }
    }
