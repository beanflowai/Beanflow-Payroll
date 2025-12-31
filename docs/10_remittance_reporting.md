# Phase 7: Remittance Reporting and CRA Submission

> **Last Updated**: 2025-12-31
> **Status**: Future Implementation (Phase 7)
> **Dependencies**: Phase 4 (API Integration) must be complete

## Overview

Payroll remittance is the process of **sending deducted CPP, EI, and income tax to the Canada Revenue Agency (CRA)**. This is a **legally required compliance task** with strict deadlines and penalties for late or incorrect remittances.

### Legal Requirements

- **Remittance Deadline**: 15th day of the month following payment (or next business day if 15th falls on weekend/holiday)
- **Remittance Types**: Regular, Quarterly, Accelerated Threshold 1, Accelerated Threshold 2
- **Required Forms**: PD7A Remittance Voucher (for manual payments)
- **Electronic Submission**: My Payment (online), Pre-Authorized Debit, Wire Transfer
- **Penalties**:
  - 3% if 1-3 days late
  - 5% if 4-5 days late
  - 7% if 6-7 days late
  - 10% if 8+ days late or not paid at all
  - Additional 20% for repeated failures

### Official References

- **CRA T4001**: Employers' Guide - Payroll Deductions and Remittances
- **Guide**: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4001.html
- **PD7A Form**: https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/pd7a.html
- **My Business Account**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html

---

## Current Implementation Status

### Already Implemented

| Component | Location | Notes |
|-----------|----------|-------|
| `RemitterType` enum | `backend/app/models/payroll.py` | QUARTERLY, REGULAR, THRESHOLD_1, THRESHOLD_2 |
| Company `remitter_type` | `companies` table | Stored per company |
| Frontend types | `frontend/src/lib/types/remittance.ts` | Complete type definitions |
| Frontend UI | `frontend/src/routes/(app)/remittance/+page.svelte` | Mock data UI |
| UI Design | `docs/ui/07_remittance.md` | Complete specification |

### To Be Implemented (This Document)

| Component | Priority | Notes |
|-----------|----------|-------|
| Database tables | High | `remittance_periods` table |
| Backend models | High | Pydantic models |
| Remittance service | High | Calculation and tracking |
| API endpoints | High | REST API |
| PD7A PDF generator | Medium | ReportLab-based |
| Beancount integration | Low | Future enhancement |

---

## 1. Database Schema

### 1.1 Migration: Create Remittance Tables

**File**: `backend/supabase/migrations/YYYYMMDDHHMMSS_create_remittance_tables.sql`

```sql
-- =============================================================================
-- REMITTANCE TABLES
-- =============================================================================
-- Description: Tables for CRA remittance tracking and payment recording
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: remittance_periods
-- -----------------------------------------------------------------------------
-- Tracks remittance obligations for each period (monthly, quarterly, etc.)

CREATE TABLE IF NOT EXISTS remittance_periods (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to Company
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Multi-tenancy
    user_id TEXT NOT NULL,

    -- Remitter Configuration (snapshot at time of creation)
    remitter_type TEXT NOT NULL CHECK (
        remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')
    ),

    -- Period Information
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE NOT NULL,

    -- Employee Deductions
    cpp_employee NUMERIC(12, 2) DEFAULT 0,
    ei_employee NUMERIC(12, 2) DEFAULT 0,
    federal_tax NUMERIC(12, 2) DEFAULT 0,
    provincial_tax NUMERIC(12, 2) DEFAULT 0,

    -- Employer Portions
    cpp_employer NUMERIC(12, 2) DEFAULT 0,
    ei_employer NUMERIC(12, 2) DEFAULT 0,

    -- Generated Column: Total Remittance
    total_amount NUMERIC(14, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_employer +
        ei_employee + ei_employer +
        federal_tax + provincial_tax
    ) STORED,

    -- Payment Tracking
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'due_soon', 'overdue', 'paid', 'paid_late')
    ),
    paid_date DATE,
    payment_method TEXT CHECK (
        payment_method IS NULL OR payment_method IN (
            'my_payment', 'pre_authorized_debit', 'online_banking',
            'wire_transfer', 'cheque'
        )
    ),
    confirmation_number TEXT,
    notes TEXT,

    -- Penalty (calculated if overdue)
    days_overdue INTEGER DEFAULT 0,
    penalty_rate NUMERIC(5, 4) DEFAULT 0,
    penalty_amount NUMERIC(10, 2) DEFAULT 0,

    -- Linked Payroll Runs (for audit)
    payroll_run_ids UUID[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_due_date CHECK (due_date > period_end),
    CONSTRAINT unique_company_period UNIQUE (company_id, period_start, period_end)
);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

-- Primary query path
CREATE INDEX idx_remittance_company ON remittance_periods(company_id);

-- User multi-tenancy
CREATE INDEX idx_remittance_user ON remittance_periods(user_id);

-- Status queries (dashboard)
CREATE INDEX idx_remittance_status ON remittance_periods(status);

-- Due date sorting
CREATE INDEX idx_remittance_due_date ON remittance_periods(due_date);

-- Pending remittances (common filter)
CREATE INDEX idx_remittance_pending ON remittance_periods(company_id, status)
    WHERE status IN ('pending', 'due_soon', 'overdue');

-- -----------------------------------------------------------------------------
-- Row Level Security
-- -----------------------------------------------------------------------------

ALTER TABLE remittance_periods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their company remittances"
ON remittance_periods
FOR ALL
USING (user_id = auth.uid()::text);

-- -----------------------------------------------------------------------------
-- Triggers
-- -----------------------------------------------------------------------------

CREATE TRIGGER update_remittance_periods_updated_at
    BEFORE UPDATE ON remittance_periods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 2. Remitter Type Determination

### 2.1 Four Remitter Types

The CRA assigns remitter types based on the **Average Monthly Withholding Amount (AMWA)** from **two calendar years ago**.

| Remitter Type | AMWA Range | Remittance Frequency | Due Date |
|---------------|------------|---------------------|----------|
| **Quarterly** | < $3,000 | Quarterly (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec) | 15th of month after quarter end |
| **Regular** | $3,000 - $24,999.99 | Monthly | 15th of following month |
| **Accelerated Threshold 1** | $25,000 - $99,999.99 | Twice monthly | 25th for 1st-15th, 10th for 16th-31st |
| **Accelerated Threshold 2** | ≥ $100,000 | Four times monthly (with withholding timing) | Day 1, 4, 11, 20 of following month |

### 2.2 Data Models

**File**: `backend/app/models/remittance.py`

```python
"""
Remittance Pydantic Models

Data models for CRA remittance tracking and reporting.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.models.payroll import RemitterType


class PaymentMethod(str, Enum):
    """CRA accepted payment methods."""
    MY_PAYMENT = "my_payment"
    PRE_AUTHORIZED_DEBIT = "pre_authorized_debit"
    ONLINE_BANKING = "online_banking"
    WIRE_TRANSFER = "wire_transfer"
    CHEQUE = "cheque"


class RemittanceStatus(str, Enum):
    """Remittance period status."""
    PENDING = "pending"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    PAID = "paid"
    PAID_LATE = "paid_late"


# =============================================================================
# Remitter Classification
# =============================================================================

class RemitterClassification(BaseModel):
    """
    Remitter classification for a company based on AMWA.

    Reference: CRA T4001 Chapter 8
    """
    company_id: UUID
    effective_year: int = Field(description="Year this classification applies to")
    classification_based_on_year: int = Field(
        description="AMWA calculated from this year (usually effective_year - 2)"
    )
    average_monthly_withholding_amount: Decimal = Field(
        ...,
        description="AMWA calculated from two years ago"
    )
    remitter_type: RemitterType

    @staticmethod
    def determine_remitter_type(amwa: Decimal) -> RemitterType:
        """
        Determine remitter type based on AMWA.

        Args:
            amwa: Average Monthly Withholding Amount from two years ago

        Returns:
            RemitterType enum value
        """
        if amwa < Decimal("3000"):
            return RemitterType.QUARTERLY
        elif amwa < Decimal("25000"):
            return RemitterType.REGULAR
        elif amwa < Decimal("100000"):
            return RemitterType.THRESHOLD_1
        else:
            return RemitterType.THRESHOLD_2

    model_config = {
        "json_schema_extra": {
            "example": {
                "companyId": "550e8400-e29b-41d4-a716-446655440000",
                "effectiveYear": 2025,
                "classificationBasedOnYear": 2023,
                "averageMonthlyWithholdingAmount": "45000.00",
                "remitterType": "threshold_1"
            }
        }
    }


# =============================================================================
# Remittance Period
# =============================================================================

class RemittancePeriodBase(BaseModel):
    """Base remittance period fields."""
    remitter_type: RemitterType
    period_start: date
    period_end: date
    due_date: date

    # Employee deductions
    cpp_employee: Decimal = Field(default=Decimal("0"), ge=0)
    ei_employee: Decimal = Field(default=Decimal("0"), ge=0)
    federal_tax: Decimal = Field(default=Decimal("0"), ge=0)
    provincial_tax: Decimal = Field(default=Decimal("0"), ge=0)

    # Employer portions
    cpp_employer: Decimal = Field(default=Decimal("0"), ge=0)
    ei_employer: Decimal = Field(default=Decimal("0"), ge=0)


class RemittancePeriodCreate(RemittancePeriodBase):
    """Request to create a remittance period."""
    company_id: UUID
    payroll_run_ids: list[UUID] = Field(default_factory=list)


class RemittancePeriod(RemittancePeriodBase):
    """Complete remittance period model (from database)."""
    id: UUID
    company_id: UUID
    user_id: str

    # Computed total (from database generated column)
    total_amount: Decimal

    # Payment tracking
    status: RemittanceStatus = RemittanceStatus.PENDING
    paid_date: date | None = None
    payment_method: PaymentMethod | None = None
    confirmation_number: str | None = None
    notes: str | None = None

    # Penalty info
    days_overdue: int = 0
    penalty_rate: Decimal = Decimal("0")
    penalty_amount: Decimal = Decimal("0")

    # Linked payroll runs
    payroll_run_ids: list[UUID] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def period_label(self) -> str:
        """Human-readable period label."""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        if self.remitter_type == RemitterType.QUARTERLY:
            quarter = (self.period_end.month - 1) // 3 + 1
            return f"Q{quarter} {self.period_end.year}"
        elif self.remitter_type == RemitterType.REGULAR:
            return f"{month_names[self.period_end.month - 1]} {self.period_end.year}"
        else:
            # Threshold 1 & 2: show date range
            month_short = month_names[self.period_end.month - 1][:3]
            return f"{month_short} {self.period_start.day}-{self.period_end.day}"


class RemittancePeriodUpdate(BaseModel):
    """Request to update remittance period (mark as paid)."""
    paid_date: date
    payment_method: PaymentMethod
    confirmation_number: str | None = None
    notes: str | None = None


# =============================================================================
# Remittance Summary
# =============================================================================

class RemittanceSummary(BaseModel):
    """YTD remittance summary for dashboard."""
    year: int
    ytd_remitted: Decimal = Field(description="Total amount paid this year")
    total_remittances: int = Field(description="Total remittance periods in year")
    completed_remittances: int = Field(description="Number of paid remittances")
    on_time_rate: Decimal = Field(description="Percentage paid on time (0.0 to 1.0)")
    pending_amount: Decimal = Field(description="Total amount still pending")
    pending_count: int = Field(description="Number of pending remittances")


# =============================================================================
# PD7A Remittance Voucher
# =============================================================================

class PD7ARemittanceVoucher(BaseModel):
    """
    PD7A Statement of Account for Current Source Deductions.

    Used for manual remittance payments (cheque, in-person).
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

    @computed_field
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

    @computed_field
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
```

---

## 3. Remittance Service

### 3.1 AMWA Calculation Service

**File**: `backend/app/services/remittance_service.py`

```python
"""
Remittance Service

Handles remittance calculations, period generation, and payment tracking.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from supabase import Client

from app.models.payroll import RemitterType
from app.models.remittance import (
    RemitterClassification,
    RemittancePeriod,
    RemittancePeriodCreate,
    RemittancePeriodUpdate,
    RemittanceSummary,
    RemittanceStatus,
)

if TYPE_CHECKING:
    from app.models.remittance import PD7ARemittanceVoucher


class RemittanceService:
    """
    Service for remittance calculations and tracking.

    Handles:
    - AMWA calculation for remitter classification
    - Remittance period generation
    - Due date calculation
    - Payment recording
    - Summary statistics
    """

    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id

    # =========================================================================
    # AMWA Calculation
    # =========================================================================

    async def calculate_amwa(self, company_id: UUID, year: int) -> Decimal:
        """
        Calculate Average Monthly Withholding Amount (AMWA) for a given year.

        AMWA = Total deductions for the year / 12 months

        Total deductions = Employee CPP + Employer CPP + Employee EI +
                          Employer EI + Federal Tax + Provincial Tax

        Args:
            company_id: Company identifier
            year: Calendar year

        Returns:
            AMWA (Average Monthly Withholding Amount)
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Query payroll_runs for the year
        response = self.supabase.table("payroll_runs").select(
            "total_cpp_employee, total_cpp_employer, "
            "total_ei_employee, total_ei_employer, "
            "total_federal_tax, total_provincial_tax"
        ).eq(
            "company_id", str(company_id)
        ).eq(
            "user_id", self.user_id
        ).gte(
            "pay_date", start_date.isoformat()
        ).lte(
            "pay_date", end_date.isoformat()
        ).in_(
            "status", ["approved", "paid"]
        ).execute()

        if not response.data:
            return Decimal("0")

        total_deductions = Decimal("0")

        for run in response.data:
            total_deductions += Decimal(str(run["total_cpp_employee"] or 0))
            total_deductions += Decimal(str(run["total_cpp_employer"] or 0))
            total_deductions += Decimal(str(run["total_ei_employee"] or 0))
            total_deductions += Decimal(str(run["total_ei_employer"] or 0))
            total_deductions += Decimal(str(run["total_federal_tax"] or 0))
            total_deductions += Decimal(str(run["total_provincial_tax"] or 0))

        # AMWA = Total / 12 months
        amwa = total_deductions / Decimal("12")
        return amwa.quantize(Decimal("0.01"))

    async def determine_remitter_classification(
        self,
        company_id: UUID,
        effective_year: int
    ) -> RemitterClassification:
        """
        Determine remitter classification for a given year.

        Uses AMWA from two calendar years ago.

        Args:
            company_id: Company identifier
            effective_year: Year the classification applies to (e.g., 2025)

        Returns:
            RemitterClassification
        """
        classification_year = effective_year - 2

        # Calculate AMWA from two years ago
        amwa = await self.calculate_amwa(company_id, classification_year)

        # Determine remitter type
        remitter_type = RemitterClassification.determine_remitter_type(amwa)

        return RemitterClassification(
            company_id=company_id,
            effective_year=effective_year,
            classification_based_on_year=classification_year,
            average_monthly_withholding_amount=amwa,
            remitter_type=remitter_type
        )

    # =========================================================================
    # Remittance Period Management
    # =========================================================================

    async def create_remittance_period(
        self,
        data: RemittancePeriodCreate
    ) -> RemittancePeriod:
        """
        Create a new remittance period.

        Args:
            data: Remittance period creation data

        Returns:
            Created RemittancePeriod
        """
        insert_data = {
            "company_id": str(data.company_id),
            "user_id": self.user_id,
            "remitter_type": data.remitter_type.value,
            "period_start": data.period_start.isoformat(),
            "period_end": data.period_end.isoformat(),
            "due_date": data.due_date.isoformat(),
            "cpp_employee": float(data.cpp_employee),
            "cpp_employer": float(data.cpp_employer),
            "ei_employee": float(data.ei_employee),
            "ei_employer": float(data.ei_employer),
            "federal_tax": float(data.federal_tax),
            "provincial_tax": float(data.provincial_tax),
            "payroll_run_ids": [str(id) for id in data.payroll_run_ids],
        }

        response = self.supabase.table("remittance_periods").insert(
            insert_data
        ).execute()

        return RemittancePeriod.model_validate(response.data[0])

    async def get_remittance_period(
        self,
        remittance_id: UUID
    ) -> RemittancePeriod | None:
        """Get a single remittance period."""
        response = self.supabase.table("remittance_periods").select(
            "*"
        ).eq(
            "id", str(remittance_id)
        ).eq(
            "user_id", self.user_id
        ).single().execute()

        if not response.data:
            return None

        return RemittancePeriod.model_validate(response.data)

    async def list_remittance_periods(
        self,
        company_id: UUID,
        year: int | None = None,
        status: RemittanceStatus | None = None
    ) -> list[RemittancePeriod]:
        """
        List remittance periods for a company.

        Args:
            company_id: Company identifier
            year: Optional year filter
            status: Optional status filter

        Returns:
            List of RemittancePeriod
        """
        query = self.supabase.table("remittance_periods").select(
            "*"
        ).eq(
            "company_id", str(company_id)
        ).eq(
            "user_id", self.user_id
        ).order("due_date", desc=True)

        if year:
            query = query.gte(
                "period_start", f"{year}-01-01"
            ).lte(
                "period_end", f"{year}-12-31"
            )

        if status:
            query = query.eq("status", status.value)

        response = query.execute()

        return [RemittancePeriod.model_validate(r) for r in response.data]

    async def record_payment(
        self,
        remittance_id: UUID,
        data: RemittancePeriodUpdate
    ) -> RemittancePeriod:
        """
        Record payment for a remittance period.

        Args:
            remittance_id: Remittance period ID
            data: Payment details

        Returns:
            Updated RemittancePeriod
        """
        # Get existing remittance to check due date
        existing = await self.get_remittance_period(remittance_id)
        if not existing:
            raise ValueError(f"Remittance period not found: {remittance_id}")

        # Determine if paid late
        is_late = data.paid_date > existing.due_date
        new_status = RemittanceStatus.PAID_LATE if is_late else RemittanceStatus.PAID

        update_data = {
            "status": new_status.value,
            "paid_date": data.paid_date.isoformat(),
            "payment_method": data.payment_method.value,
            "confirmation_number": data.confirmation_number,
            "notes": data.notes,
        }

        response = self.supabase.table("remittance_periods").update(
            update_data
        ).eq(
            "id", str(remittance_id)
        ).eq(
            "user_id", self.user_id
        ).execute()

        return RemittancePeriod.model_validate(response.data[0])

    # =========================================================================
    # Due Date Calculation
    # =========================================================================

    def calculate_due_date(
        self,
        remitter_type: RemitterType,
        period_end: date
    ) -> date:
        """
        Calculate remittance due date based on remitter type.

        Args:
            remitter_type: Remitter type
            period_end: End of remittance period

        Returns:
            Due date
        """
        if remitter_type == RemitterType.REGULAR:
            # Regular: 15th of following month
            if period_end.month == 12:
                due_month = 1
                due_year = period_end.year + 1
            else:
                due_month = period_end.month + 1
                due_year = period_end.year
            due_date = date(due_year, due_month, 15)

        elif remitter_type == RemitterType.QUARTERLY:
            # Quarterly: 15th of month after quarter end
            quarter_end_month = period_end.month
            if quarter_end_month in [3, 6, 9, 12]:
                if quarter_end_month == 12:
                    due_month = 1
                    due_year = period_end.year + 1
                else:
                    due_month = quarter_end_month + 1
                    due_year = period_end.year
            else:
                raise ValueError(f"Invalid quarter end month: {quarter_end_month}")
            due_date = date(due_year, due_month, 15)

        elif remitter_type == RemitterType.THRESHOLD_1:
            # Accelerated Threshold 1
            # For 1st-15th: due 25th of same month
            # For 16th-last day: due 10th of following month
            if period_end.day == 15:
                due_date = date(period_end.year, period_end.month, 25)
            else:
                if period_end.month == 12:
                    due_month = 1
                    due_year = period_end.year + 1
                else:
                    due_month = period_end.month + 1
                    due_year = period_end.year
                due_date = date(due_year, due_month, 10)

        elif remitter_type == RemitterType.THRESHOLD_2:
            # Accelerated Threshold 2 (complex - based on withholding dates)
            # Simplified: use next month 1st as default
            if period_end.month == 12:
                due_month = 1
                due_year = period_end.year + 1
            else:
                due_month = period_end.month + 1
                due_year = period_end.year
            due_date = date(due_year, due_month, 1)

        else:
            raise ValueError(f"Unknown remitter type: {remitter_type}")

        # Adjust if due date falls on weekend
        return self._adjust_for_business_day(due_date)

    def _adjust_for_business_day(self, target_date: date) -> date:
        """
        Adjust date to next business day if it falls on weekend.

        Note: Does not account for statutory holidays.
        """
        if target_date.weekday() == 5:  # Saturday
            return target_date + timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            return target_date + timedelta(days=1)
        return target_date

    # =========================================================================
    # Summary Statistics
    # =========================================================================

    async def get_remittance_summary(
        self,
        company_id: UUID,
        year: int
    ) -> RemittanceSummary:
        """
        Get YTD remittance summary for dashboard.

        Args:
            company_id: Company identifier
            year: Calendar year

        Returns:
            RemittanceSummary
        """
        remittances = await self.list_remittance_periods(company_id, year)

        paid_remittances = [
            r for r in remittances
            if r.status in [RemittanceStatus.PAID, RemittanceStatus.PAID_LATE]
        ]
        pending_remittances = [
            r for r in remittances
            if r.status in [
                RemittanceStatus.PENDING,
                RemittanceStatus.DUE_SOON,
                RemittanceStatus.OVERDUE
            ]
        ]

        on_time_count = len([
            r for r in paid_remittances
            if r.status == RemittanceStatus.PAID
        ])

        on_time_rate = (
            Decimal(on_time_count) / Decimal(len(paid_remittances))
            if paid_remittances else Decimal("1.0")
        )

        return RemittanceSummary(
            year=year,
            ytd_remitted=sum(r.total_amount for r in paid_remittances),
            total_remittances=len(remittances),
            completed_remittances=len(paid_remittances),
            on_time_rate=on_time_rate,
            pending_amount=sum(r.total_amount for r in pending_remittances),
            pending_count=len(pending_remittances)
        )

    # =========================================================================
    # Penalty Calculation
    # =========================================================================

    @staticmethod
    def calculate_penalty_rate(days_overdue: int) -> Decimal:
        """
        Calculate late penalty rate based on days overdue.

        Reference: CRA T4001 Chapter 8

        Args:
            days_overdue: Number of days past due date

        Returns:
            Penalty rate as decimal (e.g., 0.03 for 3%)
        """
        if days_overdue <= 0:
            return Decimal("0")
        elif days_overdue <= 3:
            return Decimal("0.03")  # 3%
        elif days_overdue <= 5:
            return Decimal("0.05")  # 5%
        elif days_overdue <= 7:
            return Decimal("0.07")  # 7%
        else:
            return Decimal("0.10")  # 10%

    @staticmethod
    def calculate_penalty_amount(amount: Decimal, days_overdue: int) -> Decimal:
        """Calculate penalty amount."""
        rate = RemittanceService.calculate_penalty_rate(days_overdue)
        return (amount * rate).quantize(Decimal("0.01"))
```

---

## 4. PD7A PDF Generator

### 4.1 PDF Generation Service

**File**: `backend/app/services/remittance/pd7a_generator.py`

```python
"""
PD7A Remittance Voucher PDF Generator

Generates PD7A Statement of Account for Current Source Deductions.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.remittance import PD7ARemittanceVoucher


class PD7APDFGenerator:
    """Generate PD7A Remittance Voucher PDF using ReportLab."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, voucher: PD7ARemittanceVoucher) -> bytes:
        """
        Generate PD7A PDF.

        Args:
            voucher: PD7ARemittanceVoucher data

        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch
        )

        story = []

        # Title
        title = Paragraph(
            "PD7A - Statement of Account for Current Source Deductions",
            self.styles["Title"]
        )
        story.append(title)
        story.append(Spacer(1, 12))

        # Employer Information
        story.extend(self._build_employer_section(voucher))
        story.append(Spacer(1, 18))

        # Period Information
        story.extend(self._build_period_section(voucher))
        story.append(Spacer(1, 24))

        # Deductions Table
        story.extend(self._build_deductions_table(voucher))
        story.append(Spacer(1, 12))

        # Total Table
        story.extend(self._build_total_table(voucher))
        story.append(Spacer(1, 36))

        # Payment Instructions
        story.append(self._build_payment_instructions())

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_employer_section(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list:
        """Build employer information section."""
        data = [
            ["Employer Name:", voucher.employer_name],
            ["Payroll Account Number:", voucher.payroll_account_number]
        ]
        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0)
        ]))
        return [table]

    def _build_period_section(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list:
        """Build period information section."""
        period_str = (
            f"{voucher.period_start.strftime('%B %d, %Y')} to "
            f"{voucher.period_end.strftime('%B %d, %Y')}"
        )
        data = [
            ["Remittance Period:", period_str],
            ["Due Date:", voucher.due_date.strftime("%B %d, %Y")]
        ]
        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0)
        ]))
        return [table]

    def _build_deductions_table(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list:
        """Build Line 10 deductions table."""
        data = [
            ["Line 10: Current Source Deductions", ""],
            ["CPP - Employee Contributions", f"${voucher.line_10_cpp_employee:,.2f}"],
            ["CPP - Employer Contributions", f"${voucher.line_10_cpp_employer:,.2f}"],
            ["EI - Employee Premiums", f"${voucher.line_10_ei_employee:,.2f}"],
            ["EI - Employer Premiums", f"${voucher.line_10_ei_employer:,.2f}"],
            ["Income Tax (Federal + Provincial)", f"${voucher.line_10_income_tax:,.2f}"]
        ]

        table = Table(data, colWidths=[4.5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))
        return [table]

    def _build_total_table(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list:
        """Build Line 11-13 total tables."""
        tables = []

        # Line 11: Total
        total_data = [[
            "Line 11: Total Current Source Deductions",
            f"${voucher.line_11_total_deductions:,.2f}"
        ]]
        total_table = Table(total_data, colWidths=[4.5 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ]))
        tables.append(total_table)

        # Line 12 & 13 (if previous balance exists)
        if voucher.line_12_previous_balance > 0:
            tables.append(Spacer(1, 12))
            balance_data = [
                [
                    "Line 12: Previous Balance Owing",
                    f"${voucher.line_12_previous_balance:,.2f}"
                ],
                [
                    "Line 13: Total Amount Due",
                    f"${voucher.line_13_total_due:,.2f}"
                ]
            ]
            balance_table = Table(balance_data, colWidths=[4.5 * inch, 2 * inch])
            balance_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffcccc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]))
            tables.append(balance_table)

        return tables

    def _build_payment_instructions(self) -> Paragraph:
        """Build payment instructions section."""
        return Paragraph(
            "<b>Payment Instructions:</b><br/><br/>"
            "1. Pay online through CRA My Business Account (recommended)<br/>"
            "2. Pre-authorized debit through CRA<br/>"
            "3. Wire transfer to CRA account<br/>"
            "4. Mail cheque with this voucher to:<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury Tax Centre<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;1050 Notre Dame Avenue<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury ON P3A 5C1",
            self.styles["Normal"]
        )
```

---

## 5. API Endpoints

### 5.1 FastAPI Router

**File**: `backend/app/api/v1/remittance.py`

```python
"""
Remittance API Endpoints

REST API for remittance management and reporting.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase_client
from app.models.payroll import RemitterType
from app.models.remittance import (
    PaymentMethod,
    PD7ARemittanceVoucher,
    RemittancePeriod,
    RemittancePeriodUpdate,
    RemittanceSummary,
    RemitterClassification,
)
from app.services.remittance_service import RemittanceService
from app.services.remittance.pd7a_generator import PD7APDFGenerator

router = APIRouter(prefix="/remittance", tags=["remittance"])


# =============================================================================
# Request/Response Models (camelCase for frontend)
# =============================================================================

class RemitterClassificationResponse(BaseModel):
    """Response for remitter classification."""
    companyId: UUID
    effectiveYear: int
    classificationBasedOnYear: int
    averageMonthlyWithholdingAmount: Decimal
    remitterType: str

    @classmethod
    def from_model(cls, model: RemitterClassification) -> "RemitterClassificationResponse":
        return cls(
            companyId=model.company_id,
            effectiveYear=model.effective_year,
            classificationBasedOnYear=model.classification_based_on_year,
            averageMonthlyWithholdingAmount=model.average_monthly_withholding_amount,
            remitterType=model.remitter_type.value
        )


class RemittancePeriodResponse(BaseModel):
    """Response for remittance period."""
    id: UUID
    companyId: UUID
    remitterType: str
    periodStart: date
    periodEnd: date
    periodLabel: str
    dueDate: date
    cppEmployee: Decimal
    cppEmployer: Decimal
    eiEmployee: Decimal
    eiEmployer: Decimal
    federalTax: Decimal
    provincialTax: Decimal
    totalAmount: Decimal
    status: str
    paidDate: date | None
    paymentMethod: str | None
    confirmationNumber: str | None
    notes: str | None
    daysOverdue: int
    penaltyRate: Decimal
    penaltyAmount: Decimal
    payrollRunIds: list[UUID]
    createdAt: str
    updatedAt: str

    @classmethod
    def from_model(cls, model: RemittancePeriod) -> "RemittancePeriodResponse":
        return cls(
            id=model.id,
            companyId=model.company_id,
            remitterType=model.remitter_type.value,
            periodStart=model.period_start,
            periodEnd=model.period_end,
            periodLabel=model.period_label,
            dueDate=model.due_date,
            cppEmployee=model.cpp_employee,
            cppEmployer=model.cpp_employer,
            eiEmployee=model.ei_employee,
            eiEmployer=model.ei_employer,
            federalTax=model.federal_tax,
            provincialTax=model.provincial_tax,
            totalAmount=model.total_amount,
            status=model.status.value,
            paidDate=model.paid_date,
            paymentMethod=model.payment_method.value if model.payment_method else None,
            confirmationNumber=model.confirmation_number,
            notes=model.notes,
            daysOverdue=model.days_overdue,
            penaltyRate=model.penalty_rate,
            penaltyAmount=model.penalty_amount,
            payrollRunIds=model.payroll_run_ids,
            createdAt=model.created_at.isoformat(),
            updatedAt=model.updated_at.isoformat()
        )


class RemittanceSummaryResponse(BaseModel):
    """Response for remittance summary."""
    year: int
    ytdRemitted: Decimal
    totalRemittances: int
    completedRemittances: int
    onTimeRate: Decimal
    pendingAmount: Decimal
    pendingCount: int

    @classmethod
    def from_model(cls, model: RemittanceSummary) -> "RemittanceSummaryResponse":
        return cls(
            year=model.year,
            ytdRemitted=model.ytd_remitted,
            totalRemittances=model.total_remittances,
            completedRemittances=model.completed_remittances,
            onTimeRate=model.on_time_rate,
            pendingAmount=model.pending_amount,
            pendingCount=model.pending_count
        )


class RecordPaymentRequest(BaseModel):
    """Request to record remittance payment."""
    paidDate: date
    paymentMethod: PaymentMethod
    confirmationNumber: str | None = None
    notes: str | None = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/classification/{company_id}/{year}")
async def get_remitter_classification(
    company_id: UUID,
    year: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> RemitterClassificationResponse:
    """
    Get remitter classification for a given year.

    Uses AMWA from two years ago to determine remitter type.
    """
    service = RemittanceService(supabase, current_user["id"])
    classification = await service.determine_remitter_classification(company_id, year)
    return RemitterClassificationResponse.from_model(classification)


@router.get("/periods/{company_id}")
async def list_remittance_periods(
    company_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)],
    year: Annotated[int | None, Query()] = None,
    status: Annotated[str | None, Query()] = None
) -> list[RemittancePeriodResponse]:
    """
    List remittance periods for a company.

    Optional filters: year, status
    """
    service = RemittanceService(supabase, current_user["id"])

    from app.models.remittance import RemittanceStatus
    status_enum = RemittanceStatus(status) if status else None

    periods = await service.list_remittance_periods(
        company_id=company_id,
        year=year,
        status=status_enum
    )
    return [RemittancePeriodResponse.from_model(p) for p in periods]


@router.get("/periods/{company_id}/{remittance_id}")
async def get_remittance_period(
    company_id: UUID,
    remittance_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> RemittancePeriodResponse:
    """Get a single remittance period."""
    service = RemittanceService(supabase, current_user["id"])
    period = await service.get_remittance_period(remittance_id)

    if not period:
        raise HTTPException(status_code=404, detail="Remittance period not found")

    return RemittancePeriodResponse.from_model(period)


@router.get("/summary/{company_id}/{year}")
async def get_remittance_summary(
    company_id: UUID,
    year: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> RemittanceSummaryResponse:
    """Get YTD remittance summary for dashboard."""
    service = RemittanceService(supabase, current_user["id"])
    summary = await service.get_remittance_summary(company_id, year)
    return RemittanceSummaryResponse.from_model(summary)


@router.post("/periods/{company_id}/{remittance_id}/record-payment")
async def record_remittance_payment(
    company_id: UUID,
    remittance_id: UUID,
    request: RecordPaymentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> RemittancePeriodResponse:
    """
    Record remittance payment.

    Updates remittance status to 'paid' or 'paid_late'.
    """
    service = RemittanceService(supabase, current_user["id"])

    update_data = RemittancePeriodUpdate(
        paid_date=request.paidDate,
        payment_method=request.paymentMethod,
        confirmation_number=request.confirmationNumber,
        notes=request.notes
    )

    updated = await service.record_payment(remittance_id, update_data)
    return RemittancePeriodResponse.from_model(updated)


@router.get("/pd7a/{company_id}/{remittance_id}")
async def generate_pd7a_voucher(
    company_id: UUID,
    remittance_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> Response:
    """
    Generate PD7A remittance voucher PDF.

    Returns PDF file for download.
    """
    service = RemittanceService(supabase, current_user["id"])
    period = await service.get_remittance_period(remittance_id)

    if not period:
        raise HTTPException(status_code=404, detail="Remittance period not found")

    # Get company info for employer name
    company_response = supabase.table("companies").select(
        "company_name, payroll_account_number"
    ).eq(
        "id", str(company_id)
    ).single().execute()

    if not company_response.data:
        raise HTTPException(status_code=404, detail="Company not found")

    company = company_response.data

    # Build PD7A voucher
    voucher = PD7ARemittanceVoucher(
        employer_name=company["company_name"],
        payroll_account_number=company["payroll_account_number"],
        period_start=period.period_start,
        period_end=period.period_end,
        due_date=period.due_date,
        line_10_cpp_employee=period.cpp_employee,
        line_10_cpp_employer=period.cpp_employer,
        line_10_ei_employee=period.ei_employee,
        line_10_ei_employer=period.ei_employer,
        line_10_income_tax=period.federal_tax + period.provincial_tax
    )

    # Generate PDF
    generator = PD7APDFGenerator()
    pdf_bytes = generator.generate_pdf(voucher)

    filename = f"PD7A_{period.period_start}_{period.period_end}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### 5.2 Register Router

Add to `backend/app/api/v1/__init__.py`:

```python
from app.api.v1.remittance import router as remittance_router

# In create_app() or router setup:
app.include_router(remittance_router, prefix="/api/v1")
```

---

## 6. Frontend Service

### 6.1 Remittance API Service

**File**: `frontend/src/lib/services/remittanceService.ts`

```typescript
/**
 * Remittance Service
 *
 * API calls for remittance management.
 */

import { apiClient } from '$lib/api/client';
import type {
	RemittancePeriod,
	RemittanceSummary,
	PaymentMethod
} from '$lib/types/remittance';

export interface RemitterClassification {
	companyId: string;
	effectiveYear: number;
	classificationBasedOnYear: number;
	averageMonthlyWithholdingAmount: number;
	remitterType: string;
}

export interface RecordPaymentRequest {
	paidDate: string;
	paymentMethod: PaymentMethod;
	confirmationNumber?: string;
	notes?: string;
}

/**
 * Get remitter classification for a year
 */
export async function getRemitterClassification(
	companyId: string,
	year: number
): Promise<RemitterClassification> {
	return apiClient.get(`/remittance/classification/${companyId}/${year}`);
}

/**
 * List remittance periods
 */
export async function listRemittancePeriods(
	companyId: string,
	year?: number,
	status?: string
): Promise<RemittancePeriod[]> {
	const params = new URLSearchParams();
	if (year) params.set('year', year.toString());
	if (status) params.set('status', status);

	const query = params.toString();
	const url = `/remittance/periods/${companyId}${query ? `?${query}` : ''}`;

	return apiClient.get(url);
}

/**
 * Get a single remittance period
 */
export async function getRemittancePeriod(
	companyId: string,
	remittanceId: string
): Promise<RemittancePeriod> {
	return apiClient.get(`/remittance/periods/${companyId}/${remittanceId}`);
}

/**
 * Get remittance summary for dashboard
 */
export async function getRemittanceSummary(
	companyId: string,
	year: number
): Promise<RemittanceSummary> {
	return apiClient.get(`/remittance/summary/${companyId}/${year}`);
}

/**
 * Record remittance payment
 */
export async function recordPayment(
	companyId: string,
	remittanceId: string,
	data: RecordPaymentRequest
): Promise<RemittancePeriod> {
	return apiClient.post(
		`/remittance/periods/${companyId}/${remittanceId}/record-payment`,
		data
	);
}

/**
 * Get PD7A voucher download URL
 */
export function getPD7ADownloadUrl(
	companyId: string,
	remittanceId: string
): string {
	return `/api/v1/remittance/pd7a/${companyId}/${remittanceId}`;
}
```

---

## 7. Testing

### 7.1 Unit Tests

**File**: `backend/tests/remittance/test_remittance_service.py`

```python
"""
Remittance Service Tests
"""

import pytest
from decimal import Decimal
from datetime import date

from app.models.payroll import RemitterType
from app.models.remittance import RemitterClassification
from app.services.remittance_service import RemittanceService


class TestRemitterClassification:
    """Test remitter type determination."""

    def test_quarterly_classification(self):
        """AMWA < $3,000 should be quarterly."""
        result = RemitterClassification.determine_remitter_type(Decimal("2000"))
        assert result == RemitterType.QUARTERLY

    def test_regular_classification(self):
        """AMWA $3,000 - $24,999 should be regular."""
        result = RemitterClassification.determine_remitter_type(Decimal("10000"))
        assert result == RemitterType.REGULAR

    def test_threshold_1_classification(self):
        """AMWA $25,000 - $99,999 should be threshold_1."""
        result = RemitterClassification.determine_remitter_type(Decimal("50000"))
        assert result == RemitterType.THRESHOLD_1

    def test_threshold_2_classification(self):
        """AMWA >= $100,000 should be threshold_2."""
        result = RemitterClassification.determine_remitter_type(Decimal("150000"))
        assert result == RemitterType.THRESHOLD_2

    def test_boundary_values(self):
        """Test boundary values."""
        # Just under $3,000
        assert RemitterClassification.determine_remitter_type(
            Decimal("2999.99")
        ) == RemitterType.QUARTERLY

        # Exactly $3,000
        assert RemitterClassification.determine_remitter_type(
            Decimal("3000")
        ) == RemitterType.REGULAR

        # Exactly $25,000
        assert RemitterClassification.determine_remitter_type(
            Decimal("25000")
        ) == RemitterType.THRESHOLD_1

        # Exactly $100,000
        assert RemitterClassification.determine_remitter_type(
            Decimal("100000")
        ) == RemitterType.THRESHOLD_2


class TestPenaltyCalculation:
    """Test late penalty calculations."""

    def test_no_penalty_on_time(self):
        """No penalty if not overdue."""
        rate = RemittanceService.calculate_penalty_rate(0)
        assert rate == Decimal("0")

    def test_penalty_1_to_3_days(self):
        """3% penalty for 1-3 days late."""
        for days in [1, 2, 3]:
            rate = RemittanceService.calculate_penalty_rate(days)
            assert rate == Decimal("0.03")

    def test_penalty_4_to_5_days(self):
        """5% penalty for 4-5 days late."""
        for days in [4, 5]:
            rate = RemittanceService.calculate_penalty_rate(days)
            assert rate == Decimal("0.05")

    def test_penalty_6_to_7_days(self):
        """7% penalty for 6-7 days late."""
        for days in [6, 7]:
            rate = RemittanceService.calculate_penalty_rate(days)
            assert rate == Decimal("0.07")

    def test_penalty_8_plus_days(self):
        """10% penalty for 8+ days late."""
        for days in [8, 10, 30, 100]:
            rate = RemittanceService.calculate_penalty_rate(days)
            assert rate == Decimal("0.10")

    def test_penalty_amount_calculation(self):
        """Test penalty amount calculation."""
        amount = Decimal("10000.00")

        # 3 days late = 3%
        penalty = RemittanceService.calculate_penalty_amount(amount, 3)
        assert penalty == Decimal("300.00")

        # 5 days late = 5%
        penalty = RemittanceService.calculate_penalty_amount(amount, 5)
        assert penalty == Decimal("500.00")


class TestDueDateCalculation:
    """Test due date calculation."""

    def test_regular_due_date(self):
        """Regular remitter: 15th of following month."""
        service = RemittanceService(None, "test")

        # January period -> February 15
        due = service.calculate_due_date(
            RemitterType.REGULAR,
            date(2025, 1, 31)
        )
        assert due == date(2025, 2, 15)

        # December period -> January 15 next year
        due = service.calculate_due_date(
            RemitterType.REGULAR,
            date(2025, 12, 31)
        )
        assert due == date(2026, 1, 15)

    def test_quarterly_due_date(self):
        """Quarterly remitter: 15th of month after quarter end."""
        service = RemittanceService(None, "test")

        # Q1 (Mar 31) -> April 15
        due = service.calculate_due_date(
            RemitterType.QUARTERLY,
            date(2025, 3, 31)
        )
        assert due == date(2025, 4, 15)

        # Q4 (Dec 31) -> January 15 next year
        due = service.calculate_due_date(
            RemitterType.QUARTERLY,
            date(2025, 12, 31)
        )
        assert due == date(2026, 1, 15)

    def test_threshold_1_due_date(self):
        """Threshold 1: 25th for 1st-15th, 10th for 16th-end."""
        service = RemittanceService(None, "test")

        # First half (1-15) -> 25th same month
        due = service.calculate_due_date(
            RemitterType.THRESHOLD_1,
            date(2025, 1, 15)
        )
        assert due == date(2025, 1, 25)

        # Second half (16-31) -> 10th next month
        due = service.calculate_due_date(
            RemitterType.THRESHOLD_1,
            date(2025, 1, 31)
        )
        assert due == date(2025, 2, 10)

    def test_weekend_adjustment(self):
        """Due date should adjust if on weekend."""
        service = RemittanceService(None, "test")

        # February 15, 2025 is a Saturday -> Monday February 17
        due = service.calculate_due_date(
            RemitterType.REGULAR,
            date(2025, 1, 31)
        )
        assert due == date(2025, 2, 17)  # Adjusted to Monday
```

---

## 8. Implementation Checklist

### Phase 7.1: Database & Models

- [ ] Create migration `create_remittance_tables.sql`
- [ ] Apply migration to Supabase
- [ ] Create `backend/app/models/remittance.py`
- [ ] Test models with sample data

### Phase 7.2: Backend Service

- [ ] Create `backend/app/services/remittance_service.py`
- [ ] Implement AMWA calculation
- [ ] Implement due date calculation
- [ ] Implement penalty calculation
- [ ] Write unit tests

### Phase 7.3: PD7A Generator

- [ ] Create `backend/app/services/remittance/pd7a_generator.py`
- [ ] Test PDF generation
- [ ] Verify PDF layout matches CRA format

### Phase 7.4: API Endpoints

- [ ] Create `backend/app/api/v1/remittance.py`
- [ ] Register router in `__init__.py`
- [ ] Test all endpoints with Swagger UI

### Phase 7.5: Frontend Integration

- [ ] Create `frontend/src/lib/services/remittanceService.ts`
- [ ] Update `+page.svelte` to use real API
- [ ] Remove mock data
- [ ] Test full workflow

---

## 9. Future Enhancements

### 9.1 Beancount Integration (Low Priority)

Beancount integration for double-entry bookkeeping of remittance liabilities and payments. This is a future enhancement when Beancount integration is implemented for the broader payroll system.

```python
# Future: backend/app/services/remittance/beancount_integration.py
class BeancountRemittanceService:
    """Track remittance liabilities and payments in Beancount."""

    async def record_remittance_liability(self, remittance: RemittancePeriod) -> str:
        """Record remittance liability entry."""
        pass

    async def record_remittance_payment(
        self,
        remittance: RemittancePeriod,
        payment_date: date
    ) -> str:
        """Record remittance payment entry."""
        pass
```

### 9.2 Automatic Remittance Period Generation

Automatically generate remittance periods when payroll runs are approved, aggregating deductions by period.

### 9.3 CRA My Business Account Deep Links

Add direct links to CRA My Business Account for payment submission.

---

**Document Version**: 2.0
**Created**: 2025-10-09
**Updated**: 2025-12-31
**For**: Beanflow-Payroll - Phase 7 Implementation
