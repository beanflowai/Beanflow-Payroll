# Phase 1: Data Layer & Tax Tables

**Duration**: 2 weeks
**Complexity**: Low
**Prerequisites**: None

> **Last Updated**: 2025-12-07
> **Architecture Version**: v2.0 (Supabase-based)

---

## 🎯 Objectives

Build the foundational data structures and tax tables for all payroll calculations.

### Deliverables
1. ✅ **Supabase database schema** (employees, payroll_runs, payroll_records)
2. ✅ Tax rate tables for 12 provinces/territories
3. ✅ CPP and EI configuration constants
4. ✅ Pydantic models for type safety
5. ✅ **Repository layer** for data access
6. ✅ Dynamic BPA calculation functions
7. ✅ Helper functions for tax lookups

---

## 📦 Task 1.0: Create Supabase Database Schema (NEW)

### LLM Agent Prompt

```markdown
TASK: Create Supabase Migration for Payroll Tables

CONTEXT:
You are creating PostgreSQL tables for the payroll module. Follow the existing patterns
from invoice_repository.py and document_files migration.

FILE TO CREATE:
backend/supabase/migrations/YYYYMMDDHHMMSS_create_payroll_tables.sql

IMPORTANT: Replace YYYYMMDDHHMMSS with current timestamp (e.g., 20251207120000)

REQUIREMENTS:

1. Create employees table:

```sql
-- =============================================================================
-- EMPLOYEES TABLE
-- =============================================================================
-- Employee master data for payroll processing
-- Stores TD1 claim amounts, salary info, and payroll configuration

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Basic Information
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    sin_encrypted TEXT NOT NULL,  -- SIN must be encrypted at rest
    email TEXT,

    -- Employment Details
    province_of_employment TEXT NOT NULL CHECK (
        province_of_employment IN ('AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'SK', 'YT')
    ),
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time', 'contract', 'casual')
    ),

    -- Compensation
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),

    -- TD1 Claim Amounts (required for tax calculation)
    federal_claim_amount NUMERIC(12, 2) NOT NULL,
    provincial_claim_amount NUMERIC(12, 2) NOT NULL,

    -- Exemptions
    is_cpp_exempt BOOLEAN DEFAULT FALSE,
    is_ei_exempt BOOLEAN DEFAULT FALSE,
    cpp2_exempt BOOLEAN DEFAULT FALSE,  -- CPT30 form exemption

    -- Optional Per-Period Deductions
    rrsp_per_period NUMERIC(10, 2) DEFAULT 0,
    union_dues_per_period NUMERIC(10, 2) DEFAULT 0,

    -- Dates
    hire_date DATE NOT NULL,
    termination_date DATE,

    -- Vacation Configuration (JSONB for flexibility)
    vacation_config JSONB DEFAULT '{"payout_method": "accrual", "vacation_rate": "0.04"}'::JSONB,
    vacation_balance NUMERIC(12, 2) DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_salary_or_hourly CHECK (
        annual_salary IS NOT NULL OR hourly_rate IS NOT NULL
    ),
    CONSTRAINT unique_employee_sin UNIQUE (user_id, ledger_id, sin_encrypted)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_employees_user_ledger
    ON employees(user_id, ledger_id);
CREATE INDEX IF NOT EXISTS idx_employees_province
    ON employees(province_of_employment);
CREATE INDEX IF NOT EXISTS idx_employees_active
    ON employees(user_id, ledger_id)
    WHERE termination_date IS NULL;

-- RLS Policy
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own employees"
    ON employees
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));

-- Trigger for updated_at
CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

2. Create payroll_runs table:

```sql
-- =============================================================================
-- PAYROLL_RUNS TABLE
-- =============================================================================
-- Payroll run header - groups all employee payments for a pay period

CREATE TABLE IF NOT EXISTS payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Period Information
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    pay_date DATE NOT NULL,

    -- Status
    status TEXT DEFAULT 'draft' CHECK (
        status IN ('draft', 'calculating', 'pending_approval', 'approved', 'paid', 'cancelled')
    ),

    -- Summary Totals (aggregated from payroll_records)
    total_employees INTEGER DEFAULT 0,
    total_gross NUMERIC(14, 2) DEFAULT 0,
    total_cpp_employee NUMERIC(12, 2) DEFAULT 0,
    total_cpp_employer NUMERIC(12, 2) DEFAULT 0,
    total_ei_employee NUMERIC(12, 2) DEFAULT 0,
    total_ei_employer NUMERIC(12, 2) DEFAULT 0,
    total_federal_tax NUMERIC(12, 2) DEFAULT 0,
    total_provincial_tax NUMERIC(12, 2) DEFAULT 0,
    total_net_pay NUMERIC(14, 2) DEFAULT 0,
    total_employer_cost NUMERIC(14, 2) DEFAULT 0,

    -- Beancount Integration
    beancount_transaction_ids TEXT[],  -- Array of transaction IDs

    -- Approval Tracking
    approved_by TEXT,
    approved_at TIMESTAMPTZ,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_pay_date CHECK (pay_date >= period_end)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payroll_runs_user_ledger
    ON payroll_runs(user_id, ledger_id);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_status
    ON payroll_runs(status);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_pay_date
    ON payroll_runs(pay_date DESC);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_period
    ON payroll_runs(user_id, ledger_id, period_start, period_end);

-- RLS Policy
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll runs"
    ON payroll_runs
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));

-- Trigger for updated_at
CREATE TRIGGER update_payroll_runs_updated_at
    BEFORE UPDATE ON payroll_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

3. Create payroll_records table:

```sql
-- =============================================================================
-- PAYROLL_RECORDS TABLE
-- =============================================================================
-- Individual employee pay record for each payroll run

CREATE TABLE IF NOT EXISTS payroll_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id),
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Earnings
    gross_regular NUMERIC(12, 2) NOT NULL,
    gross_overtime NUMERIC(10, 2) DEFAULT 0,
    holiday_pay NUMERIC(10, 2) DEFAULT 0,
    holiday_premium_pay NUMERIC(10, 2) DEFAULT 0,
    vacation_pay_paid NUMERIC(10, 2) DEFAULT 0,
    other_earnings NUMERIC(10, 2) DEFAULT 0,

    -- Employee Deductions
    cpp_employee NUMERIC(10, 2) DEFAULT 0,
    cpp_additional NUMERIC(10, 2) DEFAULT 0,  -- CPP2 (above YMPE)
    ei_employee NUMERIC(10, 2) DEFAULT 0,
    federal_tax NUMERIC(10, 2) DEFAULT 0,
    provincial_tax NUMERIC(10, 2) DEFAULT 0,
    rrsp NUMERIC(10, 2) DEFAULT 0,
    union_dues NUMERIC(10, 2) DEFAULT 0,
    garnishments NUMERIC(10, 2) DEFAULT 0,
    other_deductions NUMERIC(10, 2) DEFAULT 0,

    -- Employer Costs
    cpp_employer NUMERIC(10, 2) DEFAULT 0,
    ei_employer NUMERIC(10, 2) DEFAULT 0,

    -- Computed Totals (stored for performance)
    total_gross NUMERIC(12, 2) GENERATED ALWAYS AS (
        gross_regular + gross_overtime + holiday_pay +
        holiday_premium_pay + vacation_pay_paid + other_earnings
    ) STORED,

    total_deductions NUMERIC(12, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_additional + ei_employee +
        federal_tax + provincial_tax + rrsp +
        union_dues + garnishments + other_deductions
    ) STORED,

    net_pay NUMERIC(12, 2) GENERATED ALWAYS AS (
        (gross_regular + gross_overtime + holiday_pay +
         holiday_premium_pay + vacation_pay_paid + other_earnings) -
        (cpp_employee + cpp_additional + ei_employee +
         federal_tax + provincial_tax + rrsp +
         union_dues + garnishments + other_deductions)
    ) STORED,

    total_employer_cost NUMERIC(12, 2) GENERATED ALWAYS AS (
        cpp_employer + ei_employer
    ) STORED,

    -- YTD Snapshot (at time of record creation)
    ytd_gross NUMERIC(14, 2) DEFAULT 0,
    ytd_cpp NUMERIC(10, 2) DEFAULT 0,
    ytd_ei NUMERIC(10, 2) DEFAULT 0,
    ytd_federal_tax NUMERIC(12, 2) DEFAULT 0,
    ytd_provincial_tax NUMERIC(12, 2) DEFAULT 0,

    -- Vacation Tracking
    vacation_accrued NUMERIC(10, 2) DEFAULT 0,
    vacation_hours_taken NUMERIC(6, 2) DEFAULT 0,

    -- Calculation Details (for audit/debugging)
    calculation_details JSONB,

    -- Paystub
    paystub_storage_key TEXT,  -- DigitalOcean Spaces path
    paystub_generated_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_employee_per_run UNIQUE (payroll_run_id, employee_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payroll_records_run
    ON payroll_records(payroll_run_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_employee
    ON payroll_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_user_ledger
    ON payroll_records(user_id, ledger_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_paystub
    ON payroll_records(paystub_storage_key)
    WHERE paystub_storage_key IS NOT NULL;

-- RLS Policy
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll records"
    ON payroll_records
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
```

4. Create helper function for updated_at if not exists:

```sql
-- Helper function for updated_at trigger (if not already exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

VALIDATION:
After applying migration, verify:
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN ('employees', 'payroll_runs', 'payroll_records');

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename IN ('employees', 'payroll_runs', 'payroll_records');

-- Check generated columns
SELECT column_name, generation_expression
FROM information_schema.columns
WHERE table_name = 'payroll_records' AND is_generated = 'ALWAYS';
```
```

---

## 📦 Task 1.1: Create Employee Repository (NEW)

### LLM Agent Prompt

```markdown
TASK: Create Employee Repository for Payroll

CONTEXT:
Follow the existing repository pattern from invoice_repository.py and file_repository.py.
Use Supabase Python client with asyncio.to_thread() for async operations.

FILE TO CREATE:
backend/app/repositories/payroll/employee_repository.py

REFERENCE FILES:
- backend/app/repositories/invoice_repository.py (pattern to follow)
- backend/app/repositories/file_repository.py (complex example)

REQUIREMENTS:

```python
"""
Employee repository for payroll module.

Handles CRUD operations for employee data in Supabase.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.supabase_client import get_supabase_client
from app.utils.json_serializer import make_json_serializable

logger = logging.getLogger(__name__)


class EmployeeRepository:
    """
    Repository for employee CRUD operations.

    Follows the Repository pattern to isolate data access from business logic.
    All methods are async and use Supabase PostgreSQL.
    """

    TABLE_NAME = "employees"

    def __init__(self, client: Client | None = None):
        """
        Initialize repository.

        Args:
            client: Optional Supabase client for dependency injection (testing)
        """
        self.client = client or get_supabase_client()

    async def create_employee(
        self,
        user_id: str,
        ledger_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Create a new employee.

        Args:
            user_id: User ID for multi-tenancy
            ledger_id: Ledger ID for multi-tenancy
            data: Employee data (first_name, last_name, sin_encrypted, etc.)

        Returns:
            Created employee record or None on failure
        """
        try:
            record = {
                "user_id": user_id,
                "ledger_id": ledger_id,
                **make_json_serializable(data)
            }

            def _insert():
                return (
                    self.client.table(self.TABLE_NAME)
                    .insert(record)
                    .execute()
                )

            response = await asyncio.to_thread(_insert)

            if response.data:
                logger.info(
                    "Created employee",
                    extra={
                        "employee_id": response.data[0]["id"],
                        "ledger_id": ledger_id
                    }
                )
                return response.data[0]
            return None

        except Exception as e:
            logger.error(
                f"Failed to create employee: {e}",
                extra={"ledger_id": ledger_id}
            )
            raise

    async def get_employee_by_id(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: str | UUID
    ) -> dict[str, Any] | None:
        """
        Get employee by ID.

        Args:
            user_id: User ID for multi-tenancy
            ledger_id: Ledger ID for multi-tenancy
            employee_id: Employee UUID

        Returns:
            Employee record or None if not found
        """
        try:
            def _query():
                return (
                    self.client.table(self.TABLE_NAME)
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("ledger_id", ledger_id)
                    .eq("id", str(employee_id))
                    .single()
                    .execute()
                )

            response = await asyncio.to_thread(_query)
            return response.data

        except Exception as e:
            logger.warning(
                f"Employee not found: {employee_id}",
                extra={"ledger_id": ledger_id}
            )
            return None

    async def list_employees(
        self,
        user_id: str,
        ledger_id: str,
        *,
        active_only: bool = True,
        province: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List employees for a ledger.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            active_only: If True, exclude terminated employees
            province: Filter by province code
            limit: Max results
            offset: Pagination offset

        Returns:
            List of employee records
        """
        try:
            def _query():
                query = (
                    self.client.table(self.TABLE_NAME)
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("ledger_id", ledger_id)
                )

                if active_only:
                    query = query.is_("termination_date", "null")

                if province:
                    query = query.eq("province_of_employment", province)

                return (
                    query
                    .order("last_name")
                    .order("first_name")
                    .range(offset, offset + limit - 1)
                    .execute()
                )

            response = await asyncio.to_thread(_query)
            return response.data or []

        except Exception as e:
            logger.error(
                f"Failed to list employees: {e}",
                extra={"ledger_id": ledger_id}
            )
            return []

    async def update_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: str | UUID,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Update employee.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            data: Fields to update

        Returns:
            Updated employee record or None
        """
        try:
            update_data = make_json_serializable(data)

            def _update():
                return (
                    self.client.table(self.TABLE_NAME)
                    .update(update_data)
                    .eq("user_id", user_id)
                    .eq("ledger_id", ledger_id)
                    .eq("id", str(employee_id))
                    .execute()
                )

            response = await asyncio.to_thread(_update)

            if response.data:
                logger.info(
                    "Updated employee",
                    extra={
                        "employee_id": str(employee_id),
                        "fields": list(data.keys())
                    }
                )
                return response.data[0]
            return None

        except Exception as e:
            logger.error(
                f"Failed to update employee: {e}",
                extra={"employee_id": str(employee_id)}
            )
            raise

    async def terminate_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: str | UUID,
        termination_date: date
    ) -> dict[str, Any] | None:
        """
        Terminate employee (soft delete).

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            termination_date: Last day of employment

        Returns:
            Updated employee record or None
        """
        return await self.update_employee(
            user_id,
            ledger_id,
            employee_id,
            {"termination_date": termination_date.isoformat()}
        )

    async def get_employee_count(
        self,
        user_id: str,
        ledger_id: str,
        active_only: bool = True
    ) -> int:
        """Get count of employees."""
        try:
            def _count():
                query = (
                    self.client.table(self.TABLE_NAME)
                    .select("id", count="exact")
                    .eq("user_id", user_id)
                    .eq("ledger_id", ledger_id)
                )

                if active_only:
                    query = query.is_("termination_date", "null")

                return query.execute()

            response = await asyncio.to_thread(_count)
            return response.count or 0

        except Exception as e:
            logger.error(f"Failed to count employees: {e}")
            return 0

    async def update_vacation_balance(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: str | UUID,
        new_balance: Decimal
    ) -> bool:
        """
        Update employee vacation balance.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            new_balance: New vacation balance amount

        Returns:
            True if successful
        """
        result = await self.update_employee(
            user_id,
            ledger_id,
            employee_id,
            {"vacation_balance": str(new_balance)}
        )
        return result is not None
```

VALIDATION:
```python
# Test repository instantiation
repo = EmployeeRepository()
assert repo.TABLE_NAME == "employees"
```
```

---

## 📦 Task 1.2: Create Tax Tables Module

### LLM Agent Prompt

```markdown
TASK: Create Canadian Payroll Tax Tables for 2025

CONTEXT:
You are implementing official CRA tax tables for a payroll system. All data comes from the T4127 document (121st Edition, July 2025).

NOTE: This task creates the initial hardcoded implementation. For the configuration-driven architecture (future enhancement), see `docs/planning/payroll/06_configuration_architecture.md`.

FILE TO CREATE:
backend/app/services/payroll/tax_tables_2025.py

REQUIREMENTS:

1. Import dependencies:
```python
from decimal import Decimal
from typing import Dict, List, Optional, tuple
from pydantic import BaseModel
```

2. Create Pydantic models:

```python
class TaxBracket(BaseModel):
    """Tax bracket definition"""
    threshold: Decimal  # Income threshold (A)
    rate: Decimal       # Tax rate (R/V)
    constant: Decimal   # Tax constant (K/KP)

class ProvinceTaxConfig(BaseModel):
    """Provincial/territorial tax configuration"""
    code: str
    name: str
    basic_personal_amount: Decimal
    bpa_is_dynamic: bool = False
    tax_brackets: List[TaxBracket]
    indexing_rate: Optional[Decimal] = None

    # Special features
    has_surtax: bool = False
    has_health_premium: bool = False
    has_tax_reduction: bool = False
    lcp_rate: Optional[Decimal] = None
    lcp_max_amount: Optional[Decimal] = None
```

3. Create FEDERAL_TAX_CONFIG dictionary:
   - bpaf: Decimal("16129.00")  # Prorated for July 2025
   - cea: Decimal("1471.00")
   - indexing_rate: Decimal("0.027")
   - tax_brackets: List with 5 brackets from Table 8.1, page 18

   FUTURE: This will be loaded from `backend/config/tax_tables/2025/jul/federal_2025_jul.json`
   (See Phase 6: Configuration Architecture)

4. Create CPP_CONFIG_2025 dictionary:
   - ympe: Decimal("71200.00")
   - yampe: Decimal("76000.00")
   - basic_exemption: Decimal("3500.00")
   - base_rate: Decimal("0.0595")
   - additional_rate: Decimal("0.0100")
   - max_base_contribution: Decimal("3356.10")

   FUTURE: This will be loaded from `backend/config/tax_tables/2025/jul/cpp_ei_2025_jul.json`

5. Create EI_CONFIG_2025 dictionary:
   - mie: Decimal("65000.00")
   - employee_rate: Decimal("0.0170")
   - employer_rate: Decimal("0.0238")
   - max_premium: Decimal("1077.48")

   FUTURE: This will be loaded from `backend/config/tax_tables/2025/jul/cpp_ei_2025_jul.json`

6. Create PROVINCIAL_TAX_CONFIGS dictionary with 12 provinces:
   AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT

   Use EXACT values from T4127 Table 8.1 (page 18):
   - Alberta: 6 brackets, BPA=22323, indexing=0.020
   - British Columbia: 7 brackets, BPA=12932, has_tax_reduction=True
   - Manitoba: 3 brackets, BPA=15591, bpa_is_dynamic=True
   - New Brunswick: 4 brackets, BPA=13396
   - Newfoundland: 8 brackets, BPA=11067
   - Nova Scotia: 5 brackets, BPA=11744, bpa_is_dynamic=True
   - Northwest Territories: 4 brackets, BPA=17842
   - Nunavut: 4 brackets, BPA=19274
   - Ontario: 5 brackets, BPA=12747, has_surtax=True, has_health_premium=True
   - Prince Edward Island: 5 brackets, BPA=15050
   - Saskatchewan: 3 brackets, BPA=19991
   - Yukon: 5 brackets, BPA=16129, bpa_is_dynamic=True

   FUTURE: These will be loaded from `backend/config/tax_tables/2025/jul/provinces_2025_jul.json`
   Special taxes (Ontario surtax/health premium, BC tax reduction) will come from
   `backend/config/tax_tables/2025/jul/special_taxes_2025_jul.json`

7. Implement helper functions:

```python
def find_tax_bracket(
    annual_income: Decimal,
    brackets: List[TaxBracket]
) -> tuple[Decimal, Decimal]:
    """
    Find applicable tax rate and constant for given income.
    Returns: (rate, constant)
    """
    for bracket in reversed(brackets):
        if annual_income >= bracket.threshold:
            return (bracket.rate, bracket.constant)
    return (brackets[0].rate, brackets[0].constant)

def get_province_config(province_code: str) -> ProvinceTaxConfig:
    """Get tax configuration for a province/territory"""
    if province_code not in PROVINCIAL_TAX_CONFIGS:
        raise ValueError(f"Province '{province_code}' not supported")
    return PROVINCIAL_TAX_CONFIGS[province_code]
```

8. Implement dynamic BPA functions (Chapter 2, Page 7):

```python
def calculate_bpamb(net_income: Decimal) -> Decimal:
    """Manitoba Basic Personal Amount

    NI <= 200,000: BPAMB = 15,591
    200,000 < NI < 400,000: BPAMB = 15,591 - (NI - 200,000) * (15,591/200,000)
    NI >= 400,000: BPAMB = 0
    """
    # Implementation here

def calculate_bpans(annual_income: Decimal) -> Decimal:
    """Nova Scotia Basic Personal Amount

    A <= 25,000: BPANS = 11,744
    25,000 < A < 75,000: BPANS = 11,744 + [(A - 25,000) * 6%]
    A >= 75,000: BPANS = 14,744
    """
    # Implementation here

def calculate_bpayt(annual_income: Decimal) -> Decimal:
    """Yukon Basic Personal Amount (same as federal)"""
    return FEDERAL_TAX_CONFIG["bpaf"]
```

9. Add validation function:

```python
def validate_tax_tables():
    """Validate all tax configurations"""
    errors = []

    # Check federal has 5 brackets
    if len(FEDERAL_TAX_CONFIG["tax_brackets"]) != 5:
        errors.append("Federal should have 5 brackets")

    # Check each province
    for code, config in PROVINCIAL_TAX_CONFIGS.items():
        if not config.tax_brackets:
            errors.append(f"{code}: No brackets")

        # Verify ascending order
        thresholds = [b.threshold for b in config.tax_brackets]
        if thresholds != sorted(thresholds):
            errors.append(f"{code}: Not in ascending order")

        # First bracket must start at 0
        if config.tax_brackets[0].threshold != Decimal("0"):
            errors.append(f"{code}: First bracket must start at 0")

    if errors:
        raise ValueError("Validation errors:\n" + "\n".join(errors))
    return True

# Run on import
validate_tax_tables()
```

CRITICAL RULES:
- Use Decimal("...") for ALL numbers, NEVER float
- Transcribe values EXACTLY from T4127 Table 8.1
- Include docstrings with T4127 page references
- File should be ~500-700 lines

VALIDATION:
After creating, test:
```python
assert len(PROVINCIAL_TAX_CONFIGS) == 12
assert FEDERAL_TAX_CONFIG["bpaf"] == Decimal("16129.00")
assert CPP_CONFIG_2025["ympe"] == Decimal("71200.00")
```
```

---

## 📦 Task 1.3: Create Payroll Data Models

### LLM Agent Prompt

```markdown
TASK: Create Pydantic Models for Payroll System

FILE TO CREATE:
backend/app/models/payroll.py

REQUIREMENTS:

1. Import dependencies:
```python
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, computed_field
from uuid import UUID
```

2. Create enums:

```python
class Province(str, Enum):
    """Canadian provinces and territories (excluding Quebec)"""
    AB = "AB"
    BC = "BC"
    MB = "MB"
    NB = "NB"
    NL = "NL"
    NS = "NS"
    NT = "NT"
    NU = "NU"
    ON = "ON"
    PE = "PE"
    SK = "SK"
    YT = "YT"

class PayPeriodFrequency(str, Enum):
    """Pay period frequencies with periods per year"""
    WEEKLY = "weekly"           # 52
    BIWEEKLY = "bi_weekly"      # 26
    SEMI_MONTHLY = "semi_monthly"  # 24
    MONTHLY = "monthly"         # 12

    @property
    def periods_per_year(self) -> int:
        return {
            "weekly": 52,
            "bi_weekly": 26,
            "semi_monthly": 24,
            "monthly": 12
        }[self.value]

class PayrollRunStatus(str, Enum):
    """Payroll run status"""
    DRAFT = "draft"
    CALCULATING = "calculating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"

class EmploymentType(str, Enum):
    """Employment type"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    CASUAL = "casual"

class VacationPayoutMethod(str, Enum):
    """Vacation pay distribution method"""
    ACCRUAL = "accrual"           # Accrue and pay when taken
    PAY_AS_YOU_GO = "pay_as_you_go"  # Add to each paycheck
    LUMP_SUM = "lump_sum"         # Pay once per year
```

3. Create Vacation Config model:

```python
class VacationConfig(BaseModel):
    """Employee vacation pay configuration"""
    payout_method: VacationPayoutMethod = VacationPayoutMethod.ACCRUAL
    vacation_rate: Decimal = Field(default=Decimal("0.04"), description="4% or 6%")
    lump_sum_month: Optional[int] = Field(None, ge=1, le=12)
```

4. Create Employee models:

```python
class EmployeeBase(BaseModel):
    """Base employee fields"""
    first_name: str
    last_name: str
    email: Optional[str] = None
    province_of_employment: Province
    pay_frequency: PayPeriodFrequency
    employment_type: EmploymentType = EmploymentType.FULL_TIME

    # Compensation (one required)
    annual_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None

    # TD1 claim amounts
    federal_claim_amount: Decimal
    provincial_claim_amount: Decimal

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False

    # Optional deductions
    rrsp_per_period: Decimal = Decimal("0")
    union_dues_per_period: Decimal = Decimal("0")

    # Dates
    hire_date: date
    termination_date: Optional[date] = None

    # Vacation
    vacation_config: VacationConfig = Field(default_factory=VacationConfig)

class EmployeeCreate(EmployeeBase):
    """Employee creation request (API input)"""
    sin: str = Field(..., description="Social Insurance Number (will be encrypted)")

class Employee(EmployeeBase):
    """Complete employee model (from database)"""
    id: UUID
    user_id: str
    ledger_id: str
    sin_encrypted: str = Field(exclude=True)  # Never expose
    vacation_balance: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        return self.termination_date is None

    class Config:
        from_attributes = True

class EmployeeResponse(BaseModel):
    """Employee API response (with masked SIN)"""
    id: UUID
    first_name: str
    last_name: str
    sin_masked: str = Field(description="***-***-XXX format")
    province_of_employment: Province
    pay_frequency: PayPeriodFrequency
    employment_type: EmploymentType
    annual_salary: Optional[Decimal]
    hourly_rate: Optional[Decimal]
    federal_claim_amount: Decimal
    provincial_claim_amount: Decimal
    is_cpp_exempt: bool
    is_ei_exempt: bool
    hire_date: date
    termination_date: Optional[date]
    vacation_balance: Decimal
    is_active: bool
```

5. Create PayrollRun models:

```python
class PayrollRunBase(BaseModel):
    """Base payroll run fields"""
    period_start: date
    period_end: date
    pay_date: date
    notes: Optional[str] = None

class PayrollRunCreate(PayrollRunBase):
    """Payroll run creation request"""
    pass

class PayrollRun(PayrollRunBase):
    """Complete payroll run model"""
    id: UUID
    user_id: str
    ledger_id: str
    status: PayrollRunStatus = PayrollRunStatus.DRAFT

    # Summary totals
    total_employees: int = 0
    total_gross: Decimal = Decimal("0")
    total_cpp_employee: Decimal = Decimal("0")
    total_cpp_employer: Decimal = Decimal("0")
    total_ei_employee: Decimal = Decimal("0")
    total_ei_employer: Decimal = Decimal("0")
    total_federal_tax: Decimal = Decimal("0")
    total_provincial_tax: Decimal = Decimal("0")
    total_net_pay: Decimal = Decimal("0")
    total_employer_cost: Decimal = Decimal("0")

    # Beancount
    beancount_transaction_ids: List[str] = Field(default_factory=list)

    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

6. Create PayrollRecord models:

```python
class PayrollRecordBase(BaseModel):
    """Base payroll record fields"""
    gross_regular: Decimal
    gross_overtime: Decimal = Decimal("0")
    holiday_pay: Decimal = Decimal("0")
    holiday_premium_pay: Decimal = Decimal("0")
    vacation_pay_paid: Decimal = Decimal("0")
    other_earnings: Decimal = Decimal("0")

class PayrollRecord(PayrollRecordBase):
    """Complete payroll record model"""
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    user_id: str
    ledger_id: str

    # Employee Deductions
    cpp_employee: Decimal = Decimal("0")
    cpp_additional: Decimal = Decimal("0")
    ei_employee: Decimal = Decimal("0")
    federal_tax: Decimal = Decimal("0")
    provincial_tax: Decimal = Decimal("0")
    rrsp: Decimal = Decimal("0")
    union_dues: Decimal = Decimal("0")
    garnishments: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")

    # Employer costs
    cpp_employer: Decimal = Decimal("0")
    ei_employer: Decimal = Decimal("0")

    # Computed (from database generated columns)
    total_gross: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    total_employer_cost: Decimal

    # YTD snapshot
    ytd_gross: Decimal = Decimal("0")
    ytd_cpp: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")
    ytd_federal_tax: Decimal = Decimal("0")
    ytd_provincial_tax: Decimal = Decimal("0")

    # Vacation
    vacation_accrued: Decimal = Decimal("0")
    vacation_hours_taken: Decimal = Decimal("0")

    # Calculation details
    calculation_details: Optional[Dict[str, Any]] = None

    # Paystub
    paystub_storage_key: Optional[str] = None
    paystub_generated_at: Optional[datetime] = None

    created_at: datetime

    class Config:
        from_attributes = True
```

7. Create calculation request/response models:

```python
class PayrollCalculationRequest(BaseModel):
    """Request for payroll calculation"""
    employee_id: UUID
    province: Province
    pay_frequency: PayPeriodFrequency
    gross_pay: Decimal
    federal_claim_amount: Decimal
    provincial_claim_amount: Decimal

    # Optional
    gross_overtime: Decimal = Decimal("0")
    rrsp_deduction: Decimal = Decimal("0")
    union_dues: Decimal = Decimal("0")

    # YTD for accurate calculation
    ytd_gross: Decimal = Decimal("0")
    ytd_cpp: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False

class PayrollCalculationResult(BaseModel):
    """Result of payroll calculation"""
    # Earnings
    gross_pay: Decimal
    gross_overtime: Decimal = Decimal("0")
    total_gross: Decimal

    # Employee deductions
    cpp_employee: Decimal
    cpp_additional: Decimal
    ei_employee: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    rrsp: Decimal
    union_dues: Decimal
    total_employee_deductions: Decimal

    # Employer costs
    cpp_employer: Decimal
    ei_employer: Decimal
    total_employer_costs: Decimal

    # Net pay
    net_pay: Decimal

    # Updated YTD
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal

    # Calculation details (for debugging/audit)
    calculation_details: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "gross_pay": "2307.69",
                "total_gross": "2307.69",
                "cpp_employee": "115.40",
                "cpp_additional": "0.00",
                "cpp_employer": "115.40",
                "ei_employee": "39.23",
                "ei_employer": "54.92",
                "federal_tax": "286.15",
                "provincial_tax": "145.80",
                "rrsp": "100.00",
                "union_dues": "0.00",
                "total_employee_deductions": "686.58",
                "total_employer_costs": "170.32",
                "net_pay": "1621.11"
            }
        }
```

VALIDATION:
Test computed fields:
```python
from backend.app.models.payroll import PayPeriodFrequency

assert PayPeriodFrequency.BIWEEKLY.periods_per_year == 26
assert PayPeriodFrequency.WEEKLY.periods_per_year == 52
```
```

---

## ✅ Validation Checklist

After completing Phase 1:

### Database Validation
```sql
-- Verify tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('employees', 'payroll_runs', 'payroll_records');

-- Verify RLS enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename IN ('employees', 'payroll_runs', 'payroll_records');
```

### Tax Tables Validation
```python
from backend.app.services.payroll.tax_tables_2025 import *

# 1. Province count
assert len(PROVINCIAL_TAX_CONFIGS) == 12

# 2. Federal config
assert len(FEDERAL_TAX_CONFIG["tax_brackets"]) == 5
assert FEDERAL_TAX_CONFIG["bpaf"] == Decimal("16129.00")

# 3. CPP/EI configs
assert CPP_CONFIG_2025["ympe"] == Decimal("71200.00")
assert EI_CONFIG_2025["mie"] == Decimal("65000.00")

# 4. Alberta specifics (6 brackets)
ab = get_province_config("AB")
assert len(ab.tax_brackets) == 6
assert ab.basic_personal_amount == Decimal("22323.00")

# 5. Ontario special features
on = get_province_config("ON")
assert on.has_surtax == True
assert on.has_health_premium == True

# 6. Dynamic BPA functions
assert calculate_bpamb(Decimal("100000")) == Decimal("15591.00")
assert calculate_bpans(Decimal("20000")) == Decimal("11744.00")
```

### Data Models Validation
```python
from backend.app.models.payroll import *

# 1. Enums
assert Province.ON == "ON"
assert PayPeriodFrequency.BIWEEKLY.periods_per_year == 26

# 2. Employee model
emp = EmployeeCreate(
    first_name="John",
    last_name="Doe",
    sin="123456789",
    province_of_employment=Province.ON,
    federal_claim_amount=Decimal("16129"),
    provincial_claim_amount=Decimal("12747"),
    annual_salary=Decimal("60000"),
    pay_frequency=PayPeriodFrequency.BIWEEKLY,
    hire_date=date(2024, 1, 1)
)
assert emp.province_of_employment == Province.ON
```

### Repository Validation
```python
from backend.app.repositories.payroll.employee_repository import EmployeeRepository

repo = EmployeeRepository()
assert repo.TABLE_NAME == "employees"
```

---

## 🚨 Common Issues

### Issue 1: Decimal vs Float
**Problem**: `Decimal("0.14") != 0.14`
**Solution**: Always use string: `Decimal("0.14")`

### Issue 2: Province Code Typos
**Problem**: Used "NWT" instead of "NT"
**Solution**: Check Table 8.1 for exact codes:
- NT (not NWT)
- NL (not NF or NFL)
- PE (not PEI)

### Issue 3: Missing RLS Context
**Problem**: Queries return empty despite data existing
**Solution**: Set user context before queries:
```python
# In API endpoint
supabase.rpc('set_config', {'setting': 'app.current_user_id', 'value': user_id})
```

### Issue 4: Migration Order
**Problem**: Foreign key errors
**Solution**: Ensure `update_updated_at_column()` function exists before creating tables

---

**Next**: [Phase 2: Core Calculations](./02_phase2_calculations.md)
