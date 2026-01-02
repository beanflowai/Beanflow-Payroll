"""
T4 Statement of Remuneration Paid - Data Models

Pydantic models for T4 slip generation and T4 Summary reporting
for Canadian year-end payroll processing.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.models.payroll import Province


class T4Status(str, Enum):
    """T4 slip generation status."""
    DRAFT = "draft"
    GENERATED = "generated"
    AMENDED = "amended"
    FILED = "filed"


class T4SlipData(BaseModel):
    """
    T4 Statement of Remuneration Paid - Individual Slip

    Contains all data needed for one employee's T4 slip,
    mapped to CRA T4 box numbers.
    """

    # Identification
    employee_id: UUID
    tax_year: int
    slip_number: int | None = Field(
        default=None,
        description="Sequential slip number for this employer"
    )

    # SIN (decrypted for T4 generation, validated with Luhn)
    sin: str = Field(
        ...,
        min_length=9,
        max_length=9,
        description="Social Insurance Number (decrypted, 9 digits)"
    )

    # Employee Information
    employee_first_name: str
    employee_last_name: str
    employee_address_line1: str | None = None
    employee_address_line2: str | None = None
    employee_city: str | None = None
    employee_province: Province | None = None
    employee_postal_code: str | None = None

    # Employer Information
    employer_name: str
    employer_account_number: str = Field(
        ...,
        min_length=15,
        max_length=15,
        description="Payroll account number (e.g., 123456789RP0001)"
    )
    employer_address_line1: str | None = None
    employer_city: str | None = None
    employer_province: Province | None = None
    employer_postal_code: str | None = None

    # T4 Boxes - Income
    box_14_employment_income: Decimal = Field(
        default=Decimal("0"),
        description="Employment income"
    )

    # T4 Boxes - Statutory Deductions
    box_16_cpp_contributions: Decimal = Field(
        default=Decimal("0"),
        description="Employee's CPP contributions (base)"
    )
    box_17_cpp2_contributions: Decimal = Field(
        default=Decimal("0"),
        description="Employee's CPP2 contributions (additional)"
    )
    box_18_ei_premiums: Decimal = Field(
        default=Decimal("0"),
        description="Employee's EI premiums"
    )
    box_22_income_tax_deducted: Decimal = Field(
        default=Decimal("0"),
        description="Income tax deducted (federal + provincial)"
    )

    # T4 Boxes - Insurable/Pensionable Earnings
    box_24_ei_insurable_earnings: Decimal = Field(
        default=Decimal("0"),
        description="EI insurable earnings"
    )
    box_26_cpp_pensionable_earnings: Decimal = Field(
        default=Decimal("0"),
        description="CPP/QPP pensionable earnings"
    )

    # T4 Boxes - Optional
    box_20_rpp_contributions: Decimal | None = Field(
        default=None,
        description="Registered pension plan contributions"
    )
    box_44_union_dues: Decimal | None = Field(
        default=None,
        description="Union dues"
    )
    box_46_charitable_donations: Decimal | None = Field(
        default=None,
        description="Charitable donations"
    )
    box_52_pension_adjustment: Decimal | None = Field(
        default=None,
        description="Pension adjustment"
    )

    # Province of employment (Box 10)
    province_of_employment: Province

    # Exemption flags
    cpp_exempt: bool = False
    ei_exempt: bool = False

    # Other info boxes (for future use)
    other_info: dict[str, Decimal] | None = Field(
        default=None,
        description="Other information boxes (e.g., Box 85, 86)"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def employee_full_name(self) -> str:
        """Full name in T4 format (Last, First)."""
        return f"{self.employee_last_name}, {self.employee_first_name}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sin_formatted(self) -> str:
        """SIN formatted with dashes (XXX-XXX-XXX)."""
        if len(self.sin) == 9:
            return f"{self.sin[:3]}-{self.sin[3:6]}-{self.sin[6:]}"
        return self.sin

    model_config = {"from_attributes": True}


class T4SlipRecord(BaseModel):
    """
    T4 Slip database record model.

    Extends T4SlipData with database fields for persistence.
    """
    id: UUID
    company_id: UUID
    user_id: str
    status: T4Status = T4Status.DRAFT

    # Storage locations
    pdf_storage_key: str | None = None
    pdf_generated_at: datetime | None = None

    # Amendment tracking
    original_slip_id: UUID | None = Field(
        default=None,
        description="ID of original slip if this is an amendment"
    )
    amendment_number: int = 0

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Embedded slip data
    slip_data: T4SlipData

    model_config = {"from_attributes": True}


class T4Summary(BaseModel):
    """
    T4 Summary - Aggregates all T4 slips for an employer.

    Used for the T4 Summary form submitted to CRA.
    """
    company_id: UUID
    user_id: str
    tax_year: int

    # Employer Information
    employer_name: str
    employer_account_number: str
    employer_address_line1: str | None = None
    employer_city: str | None = None
    employer_province: Province | None = None
    employer_postal_code: str | None = None

    # Summary Totals
    total_number_of_t4_slips: int = 0
    total_employment_income: Decimal = Decimal("0")  # Sum of Box 14
    total_cpp_contributions: Decimal = Decimal("0")  # Sum of Box 16
    total_cpp2_contributions: Decimal = Decimal("0")  # Sum of Box 17
    total_ei_premiums: Decimal = Decimal("0")  # Sum of Box 18
    total_income_tax_deducted: Decimal = Decimal("0")  # Sum of Box 22
    total_union_dues: Decimal = Decimal("0")  # Sum of Box 44

    # Employer contributions
    total_cpp_employer: Decimal = Decimal("0")
    total_ei_employer: Decimal = Decimal("0")

    # Difference from remittances (for reconciliation)
    remittance_difference: Decimal = Decimal("0")

    # Status
    status: T4Status = T4Status.DRAFT

    # Storage locations
    pdf_storage_key: str | None = None
    xml_storage_key: str | None = None
    generated_at: datetime | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_employer_contributions(self) -> Decimal:
        """Total employer CPP and EI contributions."""
        return self.total_cpp_employer + self.total_ei_employer

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_remittance_required(self) -> Decimal:
        """Total source deductions to remit to CRA."""
        return (
            self.total_cpp_contributions
            + self.total_cpp2_contributions
            + self.total_cpp_employer
            + self.total_ei_premiums
            + self.total_ei_employer
            + self.total_income_tax_deducted
        )

    model_config = {"from_attributes": True}


# =============================================================================
# API Request/Response Models
# =============================================================================


class T4GenerationRequest(BaseModel):
    """Request to generate T4 slips for a tax year."""
    tax_year: int
    employee_ids: list[UUID] | None = Field(
        default=None,
        description="Specific employees to generate T4s for. If None, generates for all."
    )
    regenerate: bool = Field(
        default=False,
        description="Whether to regenerate existing T4s"
    )


class T4GenerationResponse(BaseModel):
    """Response from T4 generation."""
    success: bool
    tax_year: int
    slips_generated: int
    slips_skipped: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)
    message: str | None = None


class T4SlipListResponse(BaseModel):
    """Response for listing T4 slips."""
    tax_year: int
    total_count: int
    slips: list[T4SlipSummary]


class T4SlipSummary(BaseModel):
    """Summary view of a T4 slip for listing."""
    id: UUID
    employee_id: UUID
    employee_name: str
    sin_masked: str = Field(description="Masked SIN: ***-***-XXX")
    box_14_employment_income: Decimal
    box_22_income_tax_deducted: Decimal
    status: T4Status
    pdf_available: bool = False


class T4SummaryResponse(BaseModel):
    """Response containing T4 Summary data."""
    success: bool
    summary: T4Summary | None = None
    message: str | None = None


class T4XmlDownloadInfo(BaseModel):
    """Information about T4 XML download."""
    filename: str
    content_type: str = "application/xml"
    storage_key: str
    size_bytes: int | None = None
