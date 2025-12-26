# Phase 4: API & Integration

**Duration**: 2 weeks
**Complexity**: Medium
**Prerequisites**: Phase 1-3 completed

> **Last Updated**: 2025-12-26
> **Architecture Version**: v2.0 (Supabase + Repository-Service-API pattern)

---

## 🎯 Objectives

Create REST API endpoints and frontend UI for payroll operations following project patterns.

### Deliverables
1. ✅ **Payroll Service layer** (business logic)
2. ✅ FastAPI endpoints for payroll (following existing patterns)
3. ✅ Employee management API with RLS
4. ✅ Pay period/payroll run API
5. ✅ Draft payroll run management API (create-or-get, add/remove employees, sync, delete)
6. ✅ Frontend **Svelte 5** components (using Runes)
7. ✅ Beancount ledger integration (using existing `BeancountService`)
8. ✅ Employee snapshot mechanism for historical accuracy

---

## 🏗️ Architecture Overview

### Three-Layer Pattern

```
API Layer (FastAPI)           → backend/app/api/v1/payroll.py
    ↓
Service Layer (Business Logic) → backend/app/services/payroll/
    ↓
Repository Layer (Data Access) → backend/app/repositories/payroll/
    ↓
Database (Supabase PostgreSQL)
```

### Reference Files to Follow

```bash
# API pattern
backend/app/api/v1/invoices.py        # Endpoint structure, decorators
backend/app/api/v1/company.py         # Simple CRUD example

# Service pattern
backend/app/services/firestore/invoice_service.py  # Business logic
backend/app/services/firestore/company_service.py  # Simpler example

# Repository pattern
backend/app/repositories/invoice_repository.py     # Data access
backend/app/repositories/file_repository.py        # Complex example
```

### Employee Snapshot Mechanism

When creating payroll records, the system stores a snapshot of the employee's data
at the time of payroll creation. This ensures historical accuracy even if employee
details change later.

**Snapshot fields stored in `payroll_records`:**
- `snapshot_name`: Employee full name at payroll time
- `snapshot_province`: Province of employment at payroll time
- `snapshot_salary`: Annual salary at payroll time
- `snapshot_pay_group_name`: Pay group name at payroll time

**Usage:**
- When displaying historical payroll data, use snapshot fields with fallback to current employee data
- Ensures paystubs and reports reflect accurate historical information

**Database migration:** `20251224240000_add_employee_snapshots.sql`

---

## 📦 Task 4.1: Create Payroll Service Layer

### LLM Agent Prompt

```markdown
TASK: Create Payroll Service Layer

CONTEXT:
Follow the existing service pattern from invoice_service.py.
The service layer handles business logic and orchestrates repository calls.

FILES TO CREATE:
1. backend/app/services/payroll/__init__.py
2. backend/app/services/payroll/employee_service.py
3. backend/app/services/payroll/payroll_service.py

REFERENCE:
- backend/app/services/firestore/invoice_service.py (pattern)
- backend/app/services/firestore/company_service.py (simpler example)

REQUIREMENTS FOR employee_service.py:

```python
"""
Employee service for payroll module.

Business logic layer that orchestrates employee operations.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.encryption import encrypt_sin, decrypt_sin, mask_sin
from app.repositories.payroll.employee_repository import EmployeeRepository
from app.models.payroll import (
    Employee,
    EmployeeCreate,
    EmployeeResponse,
    Province,
    PayPeriodFrequency
)

logger = logging.getLogger(__name__)


class EmployeeService:
    """
    Service for employee management.

    Handles:
    - SIN encryption/decryption
    - Business validation
    - Data transformation (API <-> DB)
    """

    def __init__(self, repository: EmployeeRepository | None = None):
        """
        Initialize service.

        Args:
            repository: Optional repository for dependency injection (testing)
        """
        self.repository = repository or EmployeeRepository()

    async def create_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_data: EmployeeCreate
    ) -> EmployeeResponse:
        """
        Create a new employee.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_data: Employee creation data (includes raw SIN)

        Returns:
            Created employee response (with masked SIN)

        Raises:
            ValueError: If validation fails
        """
        # Validate compensation - must have salary or hourly rate
        if not employee_data.annual_salary and not employee_data.hourly_rate:
            raise ValueError("Employee must have either annual_salary or hourly_rate")

        # Encrypt SIN before storage
        sin_encrypted = encrypt_sin(employee_data.sin)

        # Prepare data for repository (exclude raw SIN)
        db_data = employee_data.model_dump(exclude={"sin"})
        db_data["sin_encrypted"] = sin_encrypted

        # Create in database
        result = await self.repository.create_employee(
            user_id=user_id,
            ledger_id=ledger_id,
            data=db_data
        )

        if not result:
            raise ValueError("Failed to create employee")

        # Transform to response (mask SIN)
        return self._to_response(result, employee_data.sin)

    async def get_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID
    ) -> EmployeeResponse | None:
        """
        Get employee by ID.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID

        Returns:
            Employee response or None if not found
        """
        result = await self.repository.get_employee_by_id(
            user_id=user_id,
            ledger_id=ledger_id,
            employee_id=employee_id
        )

        if not result:
            return None

        # Decrypt SIN for masking
        sin_decrypted = decrypt_sin(result["sin_encrypted"])
        return self._to_response(result, sin_decrypted)

    async def list_employees(
        self,
        user_id: str,
        ledger_id: str,
        *,
        active_only: bool = True,
        province: Province | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[EmployeeResponse]:
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
            List of employee responses
        """
        results = await self.repository.list_employees(
            user_id=user_id,
            ledger_id=ledger_id,
            active_only=active_only,
            province=province.value if province else None,
            limit=limit,
            offset=offset
        )

        responses = []
        for result in results:
            sin_decrypted = decrypt_sin(result["sin_encrypted"])
            responses.append(self._to_response(result, sin_decrypted))

        return responses

    async def update_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID,
        update_data: dict[str, Any]
    ) -> EmployeeResponse | None:
        """
        Update employee.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            update_data: Fields to update

        Returns:
            Updated employee response or None
        """
        # Don't allow updating SIN through regular update
        if "sin" in update_data:
            raise ValueError("Cannot update SIN through this method")

        result = await self.repository.update_employee(
            user_id=user_id,
            ledger_id=ledger_id,
            employee_id=employee_id,
            data=update_data
        )

        if not result:
            return None

        sin_decrypted = decrypt_sin(result["sin_encrypted"])
        return self._to_response(result, sin_decrypted)

    async def terminate_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID,
        termination_date: date
    ) -> EmployeeResponse | None:
        """
        Terminate employee (soft delete).

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            termination_date: Last day of employment

        Returns:
            Updated employee response or None
        """
        result = await self.repository.terminate_employee(
            user_id=user_id,
            ledger_id=ledger_id,
            employee_id=employee_id,
            termination_date=termination_date
        )

        if not result:
            return None

        sin_decrypted = decrypt_sin(result["sin_encrypted"])
        return self._to_response(result, sin_decrypted)

    async def get_active_employee_count(
        self,
        user_id: str,
        ledger_id: str
    ) -> int:
        """Get count of active employees."""
        return await self.repository.get_employee_count(
            user_id=user_id,
            ledger_id=ledger_id,
            active_only=True
        )

    def _to_response(self, db_record: dict, sin: str) -> EmployeeResponse:
        """
        Transform database record to API response.

        Args:
            db_record: Database record
            sin: Decrypted SIN (will be masked)

        Returns:
            Employee response with masked SIN
        """
        return EmployeeResponse(
            id=UUID(db_record["id"]),
            first_name=db_record["first_name"],
            last_name=db_record["last_name"],
            sin_masked=mask_sin(sin),
            province_of_employment=Province(db_record["province_of_employment"]),
            pay_frequency=PayPeriodFrequency(db_record["pay_frequency"]),
            employment_type=db_record.get("employment_type", "full_time"),
            annual_salary=Decimal(db_record["annual_salary"]) if db_record.get("annual_salary") else None,
            hourly_rate=Decimal(db_record["hourly_rate"]) if db_record.get("hourly_rate") else None,
            federal_claim_amount=Decimal(db_record["federal_claim_amount"]),
            provincial_claim_amount=Decimal(db_record["provincial_claim_amount"]),
            is_cpp_exempt=db_record.get("is_cpp_exempt", False),
            is_ei_exempt=db_record.get("is_ei_exempt", False),
            hire_date=db_record["hire_date"],
            termination_date=db_record.get("termination_date"),
            vacation_balance=Decimal(db_record.get("vacation_balance", "0")),
            is_active=db_record.get("termination_date") is None
        )
```

ENCRYPTION HELPER (create if not exists):
```python
# backend/app/core/encryption.py

import os
from cryptography.fernet import Fernet

# Load key from environment or generate
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable required")

_fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_sin(sin: str) -> str:
    """Encrypt SIN for storage."""
    # Remove dashes before encryption
    clean_sin = sin.replace("-", "")
    return _fernet.encrypt(clean_sin.encode()).decode()


def decrypt_sin(encrypted: str) -> str:
    """Decrypt SIN from storage."""
    decrypted = _fernet.decrypt(encrypted.encode()).decode()
    # Return with dashes
    return f"{decrypted[:3]}-{decrypted[3:6]}-{decrypted[6:]}"


def mask_sin(sin: str) -> str:
    """Mask SIN for display (show last 3 digits only)."""
    clean = sin.replace("-", "")
    return f"***-***-{clean[-3:]}"
```

VALIDATION:
```python
# Test service instantiation
service = EmployeeService()
assert service.repository is not None
```
```

---

## 📦 Task 4.2: Create Payroll API Endpoints

### LLM Agent Prompt

```markdown
TASK: Create Payroll REST API

CONTEXT:
Follow the existing API patterns from invoices.py.
Use the require_ledger_access decorator for authorization.
Use camelCase for API field names (per project standards).

FILE TO CREATE:
backend/app/api/v1/payroll.py

REFERENCE:
- backend/app/api/v1/invoices.py (pattern to follow)
- backend/app/api/v1/company.py (simpler example)

REQUIREMENTS:

```python
"""
Payroll API endpoints.

Provides REST API for employee management, payroll calculation,
payroll runs, and paystub generation.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user_google_id
from app.core.firestore_manager import require_ledger_access
from app.models.payroll import (
    EmployeeCreate,
    EmployeeResponse,
    PayrollCalculationRequest,
    PayrollCalculationResult,
    PayrollRunCreate,
    PayrollRun,
    PayrollRunStatus,
    Province,
    PayPeriodFrequency,
)
from app.services.payroll.employee_service import EmployeeService
from app.services.payroll.payroll_service import PayrollService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payroll", tags=["payroll"])


# =============================================================================
# REQUEST/RESPONSE MODELS (camelCase per project standards)
# =============================================================================

class CreateEmployeeRequest(BaseModel):
    """Create employee request (camelCase fields)"""
    firstName: str
    lastName: str
    sin: str = Field(..., description="Social Insurance Number (XXX-XXX-XXX)")
    email: str | None = None
    provinceOfEmployment: Province
    payFrequency: PayPeriodFrequency
    annualSalary: Decimal | None = None
    hourlyRate: Decimal | None = None
    federalClaimAmount: Decimal
    provincialClaimAmount: Decimal
    isCppExempt: bool = False
    isEiExempt: bool = False
    rrspPerPeriod: Decimal = Decimal("0")
    unionDuesPerPeriod: Decimal = Decimal("0")
    hireDate: date

    def to_internal(self) -> EmployeeCreate:
        """Convert to internal model (snake_case)"""
        return EmployeeCreate(
            first_name=self.firstName,
            last_name=self.lastName,
            sin=self.sin,
            email=self.email,
            province_of_employment=self.provinceOfEmployment,
            pay_frequency=self.payFrequency,
            annual_salary=self.annualSalary,
            hourly_rate=self.hourlyRate,
            federal_claim_amount=self.federalClaimAmount,
            provincial_claim_amount=self.provincialClaimAmount,
            is_cpp_exempt=self.isCppExempt,
            is_ei_exempt=self.isEiExempt,
            rrsp_per_period=self.rrspPerPeriod,
            union_dues_per_period=self.unionDuesPerPeriod,
            hire_date=self.hireDate
        )


class EmployeeApiResponse(BaseModel):
    """Employee API response (camelCase fields)"""
    id: UUID
    firstName: str
    lastName: str
    sinMasked: str
    provinceOfEmployment: Province
    payFrequency: PayPeriodFrequency
    employmentType: str
    annualSalary: Decimal | None
    hourlyRate: Decimal | None
    federalClaimAmount: Decimal
    provincialClaimAmount: Decimal
    isCppExempt: bool
    isEiExempt: bool
    hireDate: date
    terminationDate: date | None
    vacationBalance: Decimal
    isActive: bool

    @classmethod
    def from_internal(cls, internal: EmployeeResponse) -> "EmployeeApiResponse":
        """Convert from internal model"""
        return cls(
            id=internal.id,
            firstName=internal.first_name,
            lastName=internal.last_name,
            sinMasked=internal.sin_masked,
            provinceOfEmployment=internal.province_of_employment,
            payFrequency=internal.pay_frequency,
            employmentType=internal.employment_type,
            annualSalary=internal.annual_salary,
            hourlyRate=internal.hourly_rate,
            federalClaimAmount=internal.federal_claim_amount,
            provincialClaimAmount=internal.provincial_claim_amount,
            isCppExempt=internal.is_cpp_exempt,
            isEiExempt=internal.is_ei_exempt,
            hireDate=internal.hire_date,
            terminationDate=internal.termination_date,
            vacationBalance=internal.vacation_balance,
            isActive=internal.is_active
        )


class UpdateEmployeeRequest(BaseModel):
    """Update employee request (partial update)"""
    firstName: str | None = None
    lastName: str | None = None
    email: str | None = None
    annualSalary: Decimal | None = None
    hourlyRate: Decimal | None = None
    federalClaimAmount: Decimal | None = None
    provincialClaimAmount: Decimal | None = None
    isCppExempt: bool | None = None
    isEiExempt: bool | None = None
    rrspPerPeriod: Decimal | None = None
    unionDuesPerPeriod: Decimal | None = None


class TerminateEmployeeRequest(BaseModel):
    """Terminate employee request"""
    terminationDate: date


# =============================================================================
# EMPLOYEE ENDPOINTS
# =============================================================================

@router.post(
    "/employees",
    response_model=EmployeeApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee"
)
@require_ledger_access("edit")
async def create_employee(
    ledger_id: str,
    request: CreateEmployeeRequest,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Create a new employee.

    Requires 'edit' access to the ledger.

    The SIN will be encrypted before storage and only the last 3 digits
    will be returned in responses.
    """
    service = EmployeeService()

    try:
        internal = request.to_internal()
        result = await service.create_employee(
            user_id=current_user_google_id,
            ledger_id=ledger_id,
            employee_data=internal
        )
        return EmployeeApiResponse.from_internal(result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/employees",
    response_model=list[EmployeeApiResponse],
    summary="List employees"
)
@require_ledger_access("view")
async def list_employees(
    ledger_id: str,
    current_user_google_id: str = Depends(get_current_user_google_id),
    activeOnly: Annotated[bool, Query(description="Only active employees")] = True,
    province: Annotated[Province | None, Query(description="Filter by province")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0
):
    """
    List all employees for a ledger.

    Requires 'view' access to the ledger.
    """
    service = EmployeeService()

    results = await service.list_employees(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        active_only=activeOnly,
        province=province,
        limit=limit,
        offset=offset
    )

    return [EmployeeApiResponse.from_internal(r) for r in results]


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeApiResponse,
    summary="Get employee"
)
@require_ledger_access("view")
async def get_employee(
    ledger_id: str,
    employee_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Get employee by ID.

    Requires 'view' access to the ledger.
    """
    service = EmployeeService()

    result = await service.get_employee(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        employee_id=employee_id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )

    return EmployeeApiResponse.from_internal(result)


@router.patch(
    "/employees/{employee_id}",
    response_model=EmployeeApiResponse,
    summary="Update employee"
)
@require_ledger_access("edit")
async def update_employee(
    ledger_id: str,
    employee_id: UUID,
    request: UpdateEmployeeRequest,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Update employee information.

    Requires 'edit' access to the ledger.
    Only provided fields will be updated.
    """
    service = EmployeeService()

    # Convert to snake_case and filter None values
    update_data = {}
    field_mapping = {
        "firstName": "first_name",
        "lastName": "last_name",
        "email": "email",
        "annualSalary": "annual_salary",
        "hourlyRate": "hourly_rate",
        "federalClaimAmount": "federal_claim_amount",
        "provincialClaimAmount": "provincial_claim_amount",
        "isCppExempt": "is_cpp_exempt",
        "isEiExempt": "is_ei_exempt",
        "rrspPerPeriod": "rrsp_per_period",
        "unionDuesPerPeriod": "union_dues_per_period"
    }

    for api_field, db_field in field_mapping.items():
        value = getattr(request, api_field, None)
        if value is not None:
            update_data[db_field] = value

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    result = await service.update_employee(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        employee_id=employee_id,
        update_data=update_data
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )

    return EmployeeApiResponse.from_internal(result)


@router.post(
    "/employees/{employee_id}/terminate",
    response_model=EmployeeApiResponse,
    summary="Terminate employee"
)
@require_ledger_access("edit")
async def terminate_employee(
    ledger_id: str,
    employee_id: UUID,
    request: TerminateEmployeeRequest,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Terminate an employee (soft delete).

    Requires 'edit' access to the ledger.
    Sets the termination date - employee data is preserved for historical records.
    """
    service = EmployeeService()

    result = await service.terminate_employee(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        employee_id=employee_id,
        termination_date=request.terminationDate
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )

    return EmployeeApiResponse.from_internal(result)


# =============================================================================
# PAYROLL CALCULATION ENDPOINTS
# =============================================================================

@router.post(
    "/calculate",
    response_model=PayrollCalculationResult,
    summary="Calculate payroll deductions"
)
@require_ledger_access("view")
async def calculate_payroll(
    ledger_id: str,
    request: PayrollCalculationRequest,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Calculate payroll for one pay period.

    This endpoint calculates CPP, EI, federal tax, and provincial tax
    based on the employee's gross pay and claim amounts.

    Requires 'view' access (calculation only, no data modification).
    """
    from app.services.payroll.payroll_engine import PayrollEngine

    engine = PayrollEngine()

    try:
        result = engine.calculate_payroll(request)
        return result
    except Exception as e:
        logger.error(f"Payroll calculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll calculation failed: {str(e)}"
        )


# =============================================================================
# PAYROLL RUN ENDPOINTS
# =============================================================================

@router.post(
    "/runs",
    response_model=PayrollRun,
    status_code=status.HTTP_201_CREATED,
    summary="Create payroll run"
)
@require_ledger_access("edit")
async def create_payroll_run(
    ledger_id: str,
    request: PayrollRunCreate,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Create a new payroll run.

    This will:
    1. Create a draft payroll run
    2. Include all active employees

    Use /runs/{run_id}/calculate to process the payroll.
    """
    service = PayrollService()

    result = await service.create_payroll_run(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        period_start=request.period_start,
        period_end=request.period_end,
        pay_date=request.pay_date,
        notes=request.notes
    )

    return result


@router.post(
    "/runs/{run_id}/calculate",
    response_model=PayrollRun,
    summary="Calculate payroll run"
)
@require_ledger_access("edit")
async def calculate_payroll_run(
    ledger_id: str,
    run_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Calculate payroll for all employees in a run.

    This will:
    1. Calculate deductions for each active employee
    2. Create payroll records
    3. Update run totals

    Run must be in 'draft' status.
    """
    service = PayrollService()

    result = await service.calculate_payroll_run(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        run_id=run_id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll run {run_id} not found"
        )

    return result


@router.post(
    "/runs/{run_id}/approve",
    response_model=PayrollRun,
    summary="Approve payroll run"
)
@require_ledger_access("edit")
async def approve_payroll_run(
    ledger_id: str,
    run_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Approve a payroll run.

    This will:
    1. Generate paystub PDFs for each employee
    2. Create Beancount transactions
    3. Update status to 'approved'

    Run must be in 'pending_approval' status.
    """
    service = PayrollService()

    result = await service.approve_payroll_run(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        run_id=run_id,
        approved_by=current_user_google_id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll run {run_id} not found"
        )

    return result


@router.get(
    "/runs",
    response_model=list[PayrollRun],
    summary="List payroll runs"
)
@require_ledger_access("view")
async def list_payroll_runs(
    ledger_id: str,
    current_user_google_id: str = Depends(get_current_user_google_id),
    status: Annotated[PayrollRunStatus | None, Query(description="Filter by status")] = None,
    year: Annotated[int | None, Query(description="Filter by year")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0
):
    """
    List payroll runs for a ledger.

    Requires 'view' access to the ledger.
    """
    service = PayrollService()

    return await service.list_payroll_runs(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        status=status,
        year=year,
        limit=limit,
        offset=offset
    )


@router.get(
    "/runs/{run_id}",
    response_model=PayrollRun,
    summary="Get payroll run"
)
@require_ledger_access("view")
async def get_payroll_run(
    ledger_id: str,
    run_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Get payroll run details.

    Requires 'view' access to the ledger.
    """
    service = PayrollService()

    result = await service.get_payroll_run(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        run_id=run_id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll run {run_id} not found"
        )

    return result


# =============================================================================
# DRAFT PAYROLL RUN MANAGEMENT ENDPOINTS (NEW)
# =============================================================================

@router.post(
    "/runs/create-or-get",
    response_model=CreateOrGetRunResponse,
    summary="Create or get a draft payroll run"
)
async def create_or_get_run(
    request: CreateOrGetRunRequest,
    current_user: CurrentUser,
):
    """
    Create a new draft payroll run or get existing one for a pay date.

    This endpoint:
    1. Checks if a payroll run already exists for this pay date
    2. If exists, returns the existing run
    3. If not, creates a new draft run with payroll records for all eligible employees

    The run is automatically populated with employees from pay groups that have
    this date as their next_pay_date.

    Request body:
    - payDate: Pay date in YYYY-MM-DD format

    Response:
    - run: PayrollRunResponse with run details
    - created: True if new run was created, False if existing
    - recordsCount: Number of payroll records created
    """
    pass


@router.post(
    "/runs/{run_id}/sync-employees",
    response_model=SyncEmployeesResponse,
    summary="Sync new employees to draft payroll run"
)
async def sync_employees(run_id: UUID, current_user: CurrentUser):
    """
    Sync new employees to a draft payroll run.

    When employees are added to pay groups after a payroll run is created,
    this endpoint will:
    1. Find pay groups for the run's pay_date
    2. Get active employees from those pay groups
    3. Create payroll_records for any employees not yet in the run
    4. Update the run's total_employees count

    Only works on runs in 'draft' status.

    Response:
    - addedCount: Number of new employees added
    - addedEmployees: List of {employeeId, employeeName}
    - run: Updated PayrollRunResponse
    """
    pass


@router.post(
    "/runs/{run_id}/employees",
    response_model=AddEmployeeResponse,
    summary="Add an employee to a draft payroll run"
)
async def add_employee_to_run(
    run_id: UUID,
    request: AddEmployeeRequest,
    current_user: CurrentUser,
):
    """
    Add a single employee to a draft payroll run.

    Creates a payroll record for the employee in the run.
    Only works on runs in 'draft' status.

    Request body:
    - employeeId: Employee ID to add

    Response:
    - employeeId: Added employee ID
    - employeeName: Added employee name
    """
    pass


@router.delete(
    "/runs/{run_id}/employees/{employee_id}",
    response_model=RemoveEmployeeResponse,
    summary="Remove an employee from a draft payroll run"
)
async def remove_employee_from_run(
    run_id: UUID,
    employee_id: str,
    current_user: CurrentUser,
):
    """
    Remove an employee from a draft payroll run.

    Deletes the payroll record for the employee.
    Only works on runs in 'draft' status.

    Response:
    - removed: True if successfully removed
    - employeeId: Removed employee ID
    """
    pass


@router.delete(
    "/runs/{run_id}",
    response_model=DeleteRunResponse,
    summary="Delete a draft payroll run"
)
async def delete_payroll_run(run_id: UUID, current_user: CurrentUser):
    """
    Delete a draft payroll run.

    Permanently deletes the run and all associated payroll records.
    Only works on runs in 'draft' status.

    Response:
    - deleted: True if successfully deleted
    - runId: Deleted run ID
    """
    pass


@router.post(
    "/runs/{run_id}/recalculate",
    response_model=PayrollRunResponse,
    summary="Recalculate payroll run"
)
async def recalculate_payroll_run(run_id: UUID, current_user: CurrentUser):
    """
    Recalculate all payroll deductions for a draft run.

    This will:
    1. Read input_data from all payroll_records
    2. Recalculate CPP, EI, federal tax, and provincial tax
    3. Update all payroll_records with new values
    4. Update payroll_runs summary totals
    5. Clear all is_modified flags

    Only works on runs in 'draft' status.
    """
    pass


@router.post(
    "/runs/{run_id}/finalize",
    response_model=PayrollRunResponse,
    summary="Finalize payroll run"
)
async def finalize_payroll_run(run_id: UUID, current_user: CurrentUser):
    """
    Finalize a draft payroll run.

    Transitions the run from 'draft' to 'pending_approval' status.
    After finalization, the run becomes read-only.

    Prerequisites:
    - Run must be in 'draft' status
    - No records can have is_modified = True (must recalculate first)
    """
    pass


# =============================================================================
# PAYSTUB ENDPOINTS
# =============================================================================

@router.get(
    "/paystubs/{employee_id}",
    summary="List employee paystubs"
)
@require_ledger_access("view")
async def list_employee_paystubs(
    ledger_id: str,
    employee_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id),
    year: Annotated[int | None, Query(description="Filter by year")] = None
):
    """
    List all paystubs for an employee.

    Requires 'view' access to the ledger.
    Returns pre-signed URLs for downloading PDFs.
    """
    service = PayrollService()

    return await service.list_employee_paystubs(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        employee_id=employee_id,
        year=year
    )


@router.get(
    "/paystubs/{employee_id}/{record_id}/download",
    summary="Download paystub"
)
@require_ledger_access("view")
async def download_paystub(
    ledger_id: str,
    employee_id: UUID,
    record_id: UUID,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Get pre-signed URL to download paystub PDF.

    Requires 'view' access to the ledger.
    URL expires in 15 minutes.
    """
    service = PayrollService()

    url = await service.get_paystub_download_url(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        employee_id=employee_id,
        record_id=record_id
    )

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paystub not found"
        )

    return {"downloadUrl": url, "expiresIn": 900}  # 15 minutes


# =============================================================================
# REMITTANCE ENDPOINTS
# =============================================================================

@router.get(
    "/remittances/summary",
    summary="Get remittance summary"
)
@require_ledger_access("view")
async def get_remittance_summary(
    ledger_id: str,
    current_user_google_id: str = Depends(get_current_user_google_id),
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)")
):
    """
    Get employer remittance summary for a month.

    Returns total amounts to remit to CRA:
    - Total CPP employer + employee
    - Total EI employer + employee
    - Total federal tax withheld
    - Total provincial tax withheld

    Requires 'view' access to the ledger.
    """
    service = PayrollService()

    return await service.get_remittance_summary(
        user_id=current_user_google_id,
        ledger_id=ledger_id,
        year=year,
        month=month
    )


# =============================================================================
# STATS ENDPOINT
# =============================================================================

@router.get(
    "/stats",
    summary="Get payroll statistics"
)
@require_ledger_access("view")
async def get_payroll_stats(
    ledger_id: str,
    current_user_google_id: str = Depends(get_current_user_google_id)
):
    """
    Get payroll statistics for dashboard.

    Returns:
    - Active employee count
    - Pending payroll runs
    - YTD totals
    """
    employee_service = EmployeeService()
    payroll_service = PayrollService()

    employee_count = await employee_service.get_active_employee_count(
        user_id=current_user_google_id,
        ledger_id=ledger_id
    )

    # TODO: Add more stats

    return {
        "activeEmployees": employee_count,
        "pendingRuns": 0,
        "ytdGross": "0.00",
        "ytdNetPay": "0.00"
    }
```

REGISTER ROUTER:
Add to `backend/app/api/v1/__init__.py`:
```python
from .payroll import router as payroll_router

# In api_router.include_router section:
api_router.include_router(payroll_router)
```

VALIDATION:
```bash
# Test endpoints
curl -X GET "http://localhost:8000/api/v1/payroll/employees?ledger_id=test" \
  -H "Authorization: Bearer <token>"
```
```

---

## 📦 Task 4.3: Frontend Employee Management (Svelte 5)

### LLM Agent Prompt

```markdown
TASK: Create Employee Management UI with Svelte 5

CONTEXT:
Use Svelte 5 Runes syntax ($state, $effect, $derived).
Follow existing component patterns from the invoices module.

FILES TO CREATE:
1. frontend/src/routes/(app)/payroll/+page.svelte (dashboard)
2. frontend/src/routes/(app)/payroll/employees/+page.svelte
3. frontend/src/lib/types/payroll.ts
4. frontend/src/lib/api/payroll.ts

REFERENCE:
- frontend/src/routes/(app)/invoices/+page.svelte (pattern)
- frontend/src/lib/api/invoices.ts (API client pattern)

REQUIREMENTS FOR employees/+page.svelte:

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import type { Employee } from '$lib/types/payroll';
  import { payrollApi } from '$lib/api/payroll';

  // Svelte 5 Runes
  let employees = $state<Employee[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let showAddModal = $state(false);

  // Form state
  let newEmployee = $state({
    firstName: '',
    lastName: '',
    sin: '',
    email: '',
    provinceOfEmployment: 'ON' as const,
    payFrequency: 'bi_weekly' as const,
    annualSalary: '',
    federalClaimAmount: '16129.00',
    provincialClaimAmount: '12747.00',
    hireDate: new Date().toISOString().split('T')[0]
  });

  // Derived state
  let activeEmployees = $derived(employees.filter(e => e.isActive));
  let employeeCount = $derived(activeEmployees.length);

  // Get ledger_id from URL or store
  let ledgerId = $derived($page.url.searchParams.get('ledger_id') || '');

  // Load employees on mount
  $effect(() => {
    if (ledgerId) {
      loadEmployees();
    }
  });

  async function loadEmployees() {
    loading = true;
    error = null;

    try {
      employees = await payrollApi.listEmployees(ledgerId);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load employees';
      console.error('Failed to load employees:', e);
    } finally {
      loading = false;
    }
  }

  async function addEmployee() {
    try {
      const created = await payrollApi.createEmployee(ledgerId, {
        firstName: newEmployee.firstName,
        lastName: newEmployee.lastName,
        sin: newEmployee.sin,
        email: newEmployee.email || undefined,
        provinceOfEmployment: newEmployee.provinceOfEmployment,
        payFrequency: newEmployee.payFrequency,
        annualSalary: newEmployee.annualSalary ? parseFloat(newEmployee.annualSalary) : undefined,
        federalClaimAmount: parseFloat(newEmployee.federalClaimAmount),
        provincialClaimAmount: parseFloat(newEmployee.provincialClaimAmount),
        hireDate: newEmployee.hireDate
      });

      employees = [...employees, created];
      showAddModal = false;
      resetForm();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to add employee';
    }
  }

  function resetForm() {
    newEmployee = {
      firstName: '',
      lastName: '',
      sin: '',
      email: '',
      provinceOfEmployment: 'ON',
      payFrequency: 'bi_weekly',
      annualSalary: '',
      federalClaimAmount: '16129.00',
      provincialClaimAmount: '12747.00',
      hireDate: new Date().toISOString().split('T')[0]
    };
  }

  const provinces = [
    { code: 'AB', name: 'Alberta' },
    { code: 'BC', name: 'British Columbia' },
    { code: 'MB', name: 'Manitoba' },
    { code: 'NB', name: 'New Brunswick' },
    { code: 'NL', name: 'Newfoundland and Labrador' },
    { code: 'NS', name: 'Nova Scotia' },
    { code: 'NT', name: 'Northwest Territories' },
    { code: 'NU', name: 'Nunavut' },
    { code: 'ON', name: 'Ontario' },
    { code: 'PE', name: 'Prince Edward Island' },
    { code: 'SK', name: 'Saskatchewan' },
    { code: 'YT', name: 'Yukon' }
  ];

  const payFrequencies = [
    { value: 'weekly', label: 'Weekly (52 pay periods)' },
    { value: 'bi_weekly', label: 'Bi-weekly (26 pay periods)' },
    { value: 'semi_monthly', label: 'Semi-monthly (24 pay periods)' },
    { value: 'monthly', label: 'Monthly (12 pay periods)' }
  ];
</script>

<div class="container mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">Employees</h1>
      <p class="text-sm text-gray-500">{employeeCount} active employee{employeeCount !== 1 ? 's' : ''}</p>
    </div>
    <button
      onclick={() => showAddModal = true}
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
    >
      + Add Employee
    </button>
  </div>

  <!-- Error message -->
  {#if error}
    <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
      {error}
    </div>
  {/if}

  <!-- Loading state -->
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    </div>
  {:else if employees.length === 0}
    <!-- Empty state -->
    <div class="text-center py-12 bg-gray-50 rounded-lg">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No employees</h3>
      <p class="mt-1 text-sm text-gray-500">Get started by adding your first employee.</p>
      <div class="mt-6">
        <button
          onclick={() => showAddModal = true}
          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          + Add Employee
        </button>
      </div>
    </div>
  {:else}
    <!-- Employee table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Employee
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              SIN
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Province
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Pay Frequency
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each employees as employee}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="h-10 w-10 flex-shrink-0">
                    <div class="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <span class="text-primary-700 font-medium">
                        {employee.firstName[0]}{employee.lastName[0]}
                      </span>
                    </div>
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                      {employee.firstName} {employee.lastName}
                    </div>
                    <div class="text-sm text-gray-500">
                      Hired: {new Date(employee.hireDate).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {employee.sinMasked}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {employee.provinceOfEmployment}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {employee.payFrequency.replace('_', '-')}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                {#if employee.isActive}
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                {:else}
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                    Terminated
                  </span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <a href="/payroll/employees/{employee.id}?ledger_id={ledgerId}" class="text-primary-600 hover:text-primary-900 mr-4">
                  Edit
                </a>
                <a href="/payroll/paystubs?employee_id={employee.id}&ledger_id={ledgerId}" class="text-gray-600 hover:text-gray-900">
                  Paystubs
                </a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Add Employee Modal -->
{#if showAddModal}
  <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div
        class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        onclick={() => showAddModal = false}
      ></div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
        <form onsubmit={(e) => { e.preventDefault(); addEmployee(); }}>
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Add New Employee</h3>

            <div class="grid grid-cols-2 gap-4">
              <!-- First Name -->
              <div>
                <label class="block text-sm font-medium text-gray-700">First Name</label>
                <input
                  type="text"
                  bind:value={newEmployee.firstName}
                  required
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>

              <!-- Last Name -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Last Name</label>
                <input
                  type="text"
                  bind:value={newEmployee.lastName}
                  required
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>

            <!-- SIN -->
            <div class="mt-4">
              <label class="block text-sm font-medium text-gray-700">SIN (Social Insurance Number)</label>
              <input
                type="text"
                bind:value={newEmployee.sin}
                pattern="[0-9]{3}-[0-9]{3}-[0-9]{3}"
                placeholder="XXX-XXX-XXX"
                required
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
              <p class="mt-1 text-xs text-gray-500">Will be encrypted and stored securely</p>
            </div>

            <!-- Email -->
            <div class="mt-4">
              <label class="block text-sm font-medium text-gray-700">Email (optional)</label>
              <input
                type="email"
                bind:value={newEmployee.email}
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div class="grid grid-cols-2 gap-4 mt-4">
              <!-- Province -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Province of Employment</label>
                <select
                  bind:value={newEmployee.provinceOfEmployment}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  {#each provinces as p}
                    <option value={p.code}>{p.name}</option>
                  {/each}
                </select>
              </div>

              <!-- Pay Frequency -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Pay Frequency</label>
                <select
                  bind:value={newEmployee.payFrequency}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  {#each payFrequencies as pf}
                    <option value={pf.value}>{pf.label}</option>
                  {/each}
                </select>
              </div>
            </div>

            <!-- Annual Salary -->
            <div class="mt-4">
              <label class="block text-sm font-medium text-gray-700">Annual Salary</label>
              <div class="mt-1 relative rounded-md shadow-sm">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span class="text-gray-500 sm:text-sm">$</span>
                </div>
                <input
                  type="number"
                  step="0.01"
                  bind:value={newEmployee.annualSalary}
                  placeholder="60000.00"
                  class="pl-7 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mt-4">
              <!-- Federal Claim -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Federal Claim (TD1)</label>
                <div class="mt-1 relative rounded-md shadow-sm">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <span class="text-gray-500 sm:text-sm">$</span>
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    bind:value={newEmployee.federalClaimAmount}
                    required
                    class="pl-7 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <!-- Provincial Claim -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Provincial Claim</label>
                <div class="mt-1 relative rounded-md shadow-sm">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <span class="text-gray-500 sm:text-sm">$</span>
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    bind:value={newEmployee.provincialClaimAmount}
                    required
                    class="pl-7 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>

            <!-- Hire Date -->
            <div class="mt-4">
              <label class="block text-sm font-medium text-gray-700">Hire Date</label>
              <input
                type="date"
                bind:value={newEmployee.hireDate}
                required
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Add Employee
            </button>
            <button
              type="button"
              onclick={() => showAddModal = false}
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}
```

API CLIENT (frontend/src/lib/api/payroll.ts):
```typescript
import { apiClient } from './client';
import type { Employee, PayrollRun, PayrollCalculationResult } from '$lib/types/payroll';

export const payrollApi = {
  // Employees
  async listEmployees(ledgerId: string): Promise<Employee[]> {
    return apiClient.get(`/payroll/employees?ledger_id=${ledgerId}`);
  },

  async createEmployee(ledgerId: string, data: CreateEmployeeRequest): Promise<Employee> {
    return apiClient.post(`/payroll/employees?ledger_id=${ledgerId}`, data);
  },

  async getEmployee(ledgerId: string, employeeId: string): Promise<Employee> {
    return apiClient.get(`/payroll/employees/${employeeId}?ledger_id=${ledgerId}`);
  },

  // Payroll Runs
  async listPayrollRuns(ledgerId: string): Promise<PayrollRun[]> {
    return apiClient.get(`/payroll/runs?ledger_id=${ledgerId}`);
  },

  async createPayrollRun(ledgerId: string, data: CreatePayrollRunRequest): Promise<PayrollRun> {
    return apiClient.post(`/payroll/runs?ledger_id=${ledgerId}`, data);
  },

  // Calculation
  async calculatePayroll(ledgerId: string, data: CalculatePayrollRequest): Promise<PayrollCalculationResult> {
    return apiClient.post(`/payroll/calculate?ledger_id=${ledgerId}`, data);
  }
};

interface CreateEmployeeRequest {
  firstName: string;
  lastName: string;
  sin: string;
  email?: string;
  provinceOfEmployment: string;
  payFrequency: string;
  annualSalary?: number;
  hourlyRate?: number;
  federalClaimAmount: number;
  provincialClaimAmount: number;
  hireDate: string;
}

interface CreatePayrollRunRequest {
  periodStart: string;
  periodEnd: string;
  payDate: string;
  notes?: string;
}

interface CalculatePayrollRequest {
  employeeId: string;
  province: string;
  payFrequency: string;
  grossPay: number;
  federalClaimAmount: number;
  provincialClaimAmount: number;
}
```
```

---

## 📦 Task 4.4: Beancount Integration

### LLM Agent Prompt

```markdown
TASK: Integrate Payroll with Beancount Ledger

CONTEXT:
Use the existing BeancountService pattern for ledger integration.
Follow the accounting-standards skill for account naming.

FILE TO CREATE:
backend/app/services/payroll/beancount_integration.py

REFERENCE:
- backend/app/services/beancount/service.py (existing integration)
- .claude/skills/accounting-standards/SKILL.md (account naming)

REQUIREMENTS:

```python
"""
Payroll Beancount integration.

Generates Beancount transactions for payroll entries following
Canadian accounting standards and CRA requirements.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from app.models.payroll import PayrollRecord, Employee

logger = logging.getLogger(__name__)


class PayrollBeancountIntegration:
    """
    Generate Beancount transactions for payroll.

    Account structure (following accounting-standards skill):

    Expenses:
    - Expenses:Payroll:Salaries:Gross        (Employee gross pay)
    - Expenses:Payroll:Benefits:CPP          (Employer CPP contribution)
    - Expenses:Payroll:Benefits:EI           (Employer EI contribution)

    Liabilities (amounts to remit):
    - Liabilities:Payroll:CPP                (Employee + Employer CPP)
    - Liabilities:Payroll:EI                 (Employee + Employer EI)
    - Liabilities:Payroll:Tax:Federal        (Federal tax withheld)
    - Liabilities:Payroll:Tax:Provincial     (Provincial tax withheld)
    - Liabilities:Payroll:Deductions:RRSP    (RRSP contributions)
    - Liabilities:Payroll:Deductions:Union   (Union dues)

    Assets:
    - Assets:Bank:Operating                  (Net pay disbursement)
    """

    def __init__(self, currency: str = "CAD"):
        """
        Initialize integration.

        Args:
            currency: Ledger currency (default CAD)
        """
        self.currency = currency

    def generate_payroll_transaction(
        self,
        employee: Employee,
        record: PayrollRecord,
        pay_date: date,
        bank_account: str = "Assets:Bank:Operating"
    ) -> str:
        """
        Generate Beancount transaction for an employee pay record.

        Args:
            employee: Employee information
            record: Payroll calculation record
            pay_date: Date of payment
            bank_account: Bank account for net pay

        Returns:
            Beancount transaction string
        """
        employee_name = f"{employee.first_name} {employee.last_name}"
        lines = []

        # Transaction header with metadata
        lines.append(f'{pay_date} * "Payroll - {employee_name}"')
        lines.append(f'  employee_id: "{employee.id}"')
        lines.append(f'  payroll_record_id: "{record.id}"')

        # Gross salary expense
        lines.append(
            f'  Expenses:Payroll:Salaries:Gross  '
            f'{record.total_gross:.2f} {self.currency}'
        )

        # Employee deductions (credit to liabilities)
        if record.cpp_employee > 0:
            cpp_total = record.cpp_employee + record.cpp_additional
            lines.append(
                f'  Liabilities:Payroll:CPP  '
                f'-{cpp_total:.2f} {self.currency}'
            )

        if record.ei_employee > 0:
            lines.append(
                f'  Liabilities:Payroll:EI  '
                f'-{record.ei_employee:.2f} {self.currency}'
            )

        if record.federal_tax > 0:
            lines.append(
                f'  Liabilities:Payroll:Tax:Federal  '
                f'-{record.federal_tax:.2f} {self.currency}'
            )

        if record.provincial_tax > 0:
            lines.append(
                f'  Liabilities:Payroll:Tax:Provincial  '
                f'-{record.provincial_tax:.2f} {self.currency}'
            )

        if record.rrsp > 0:
            lines.append(
                f'  Liabilities:Payroll:Deductions:RRSP  '
                f'-{record.rrsp:.2f} {self.currency}'
            )

        if record.union_dues > 0:
            lines.append(
                f'  Liabilities:Payroll:Deductions:Union  '
                f'-{record.union_dues:.2f} {self.currency}'
            )

        # Net pay from bank
        lines.append(
            f'  {bank_account}  '
            f'-{record.net_pay:.2f} {self.currency}'
        )

        return '\n'.join(lines)

    def generate_employer_costs_transaction(
        self,
        pay_date: date,
        total_cpp_employer: Decimal,
        total_ei_employer: Decimal,
        payroll_run_id: str | None = None
    ) -> str:
        """
        Generate transaction for employer payroll costs.

        This creates a separate transaction for employer contributions
        to CPP and EI (matching employee deductions).

        Args:
            pay_date: Date of payment
            total_cpp_employer: Total employer CPP contribution
            total_ei_employer: Total employer EI contribution
            payroll_run_id: Optional payroll run ID for metadata

        Returns:
            Beancount transaction string
        """
        lines = []

        lines.append(f'{pay_date} * "Payroll - Employer Contributions"')
        if payroll_run_id:
            lines.append(f'  payroll_run_id: "{payroll_run_id}"')

        # Employer CPP expense
        if total_cpp_employer > 0:
            lines.append(
                f'  Expenses:Payroll:Benefits:CPP  '
                f'{total_cpp_employer:.2f} {self.currency}'
            )
            lines.append(
                f'  Liabilities:Payroll:CPP  '
                f'-{total_cpp_employer:.2f} {self.currency}'
            )

        # Employer EI expense (1.4x employee)
        if total_ei_employer > 0:
            lines.append(
                f'  Expenses:Payroll:Benefits:EI  '
                f'{total_ei_employer:.2f} {self.currency}'
            )
            lines.append(
                f'  Liabilities:Payroll:EI  '
                f'-{total_ei_employer:.2f} {self.currency}'
            )

        return '\n'.join(lines)

    def generate_remittance_transaction(
        self,
        pay_date: date,
        cpp_total: Decimal,
        ei_total: Decimal,
        federal_tax: Decimal,
        provincial_tax: Decimal,
        bank_account: str = "Assets:Bank:Operating"
    ) -> str:
        """
        Generate transaction for CRA remittance payment.

        This records the payment of withheld amounts to CRA.

        Args:
            pay_date: Date of remittance
            cpp_total: Total CPP (employee + employer)
            ei_total: Total EI (employee + employer)
            federal_tax: Total federal tax withheld
            provincial_tax: Total provincial tax withheld
            bank_account: Bank account for payment

        Returns:
            Beancount transaction string
        """
        lines = []
        total = cpp_total + ei_total + federal_tax + provincial_tax

        lines.append(f'{pay_date} * "CRA Remittance - Payroll Deductions"')

        # Clear liabilities
        if cpp_total > 0:
            lines.append(
                f'  Liabilities:Payroll:CPP  '
                f'{cpp_total:.2f} {self.currency}'
            )

        if ei_total > 0:
            lines.append(
                f'  Liabilities:Payroll:EI  '
                f'{ei_total:.2f} {self.currency}'
            )

        if federal_tax > 0:
            lines.append(
                f'  Liabilities:Payroll:Tax:Federal  '
                f'{federal_tax:.2f} {self.currency}'
            )

        if provincial_tax > 0:
            lines.append(
                f'  Liabilities:Payroll:Tax:Provincial  '
                f'{provincial_tax:.2f} {self.currency}'
            )

        # Payment from bank
        lines.append(
            f'  {bank_account}  '
            f'-{total:.2f} {self.currency}'
        )

        return '\n'.join(lines)

    def generate_account_definitions(self) -> str:
        """
        Generate account open directives for payroll accounts.

        Returns:
            Beancount account definitions
        """
        accounts = [
            # Expense accounts
            "Expenses:Payroll:Salaries:Gross",
            "Expenses:Payroll:Benefits:CPP",
            "Expenses:Payroll:Benefits:EI",
            # Liability accounts
            "Liabilities:Payroll:CPP",
            "Liabilities:Payroll:EI",
            "Liabilities:Payroll:Tax:Federal",
            "Liabilities:Payroll:Tax:Provincial",
            "Liabilities:Payroll:Deductions:RRSP",
            "Liabilities:Payroll:Deductions:Union",
        ]

        lines = ["; Payroll accounts", ""]
        for account in accounts:
            lines.append(f"2020-01-01 open {account}  {self.currency}")

        return '\n'.join(lines)
```

USAGE IN PAYROLL SERVICE:
```python
# In payroll_service.py
from app.services.payroll.beancount_integration import PayrollBeancountIntegration
from app.services.beancount.service import BeancountService

async def approve_payroll_run(self, ...):
    # Generate transactions
    bc_integration = PayrollBeancountIntegration()
    beancount_service = BeancountService()

    transactions = []
    for record in records:
        txn = bc_integration.generate_payroll_transaction(
            employee=employee,
            record=record,
            pay_date=run.pay_date
        )
        transactions.append(txn)

    # Add employer costs
    employer_txn = bc_integration.generate_employer_costs_transaction(
        pay_date=run.pay_date,
        total_cpp_employer=run.total_cpp_employer,
        total_ei_employer=run.total_ei_employer,
        payroll_run_id=str(run.id)
    )
    transactions.append(employer_txn)

    # Append to ledger
    for txn in transactions:
        await beancount_service.append_transaction(
            user_id=user_id,
            ledger_id=ledger_id,
            transaction=txn
        )
```
```

---

## ✅ Phase 4 Validation

- [ ] Employee service created with SIN encryption
- [ ] All API endpoints respond correctly
- [ ] Employee CRUD operations work
- [ ] Payroll calculation endpoint accurate
- [ ] Frontend displays employees (Svelte 5 Runes)
- [ ] Can add/edit employees via UI
- [ ] Beancount transactions formatted correctly
- [ ] Transactions use proper account naming
- [ ] Payroll run workflow works (draft → calculate → approve)

---

**Next**: [Phase 5: Testing & Validation](./05_phase5_testing.md)
