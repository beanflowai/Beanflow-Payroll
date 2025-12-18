---
name: backend-development
description: Backend development core guide for Beanflow-Payroll - Python/FastAPI code style with type safety, camelCase field naming standard, quality checks using ruff/mypy, and common development patterns
owner: Backend Team
last_updated: 2025-12-18
triggers:
  - Python code standards
  - FastAPI development
  - type safety
  - Backend development
  - Python coding
related_skills:
  - core-architecture
  - workflow-policies
  - payroll-domain
agent_hints:
  token_budget_hint: "Core backend skill - load with payroll-domain for payroll-specific logic"
  write_scope: ["writes-backend"]
  validation_commands:
    - "cd backend && uv run ruff check ."
    - "cd backend && uv run mypy ."
  plan_shape: ["Implement changes", "Run tests/lint/type checks", "Verify code quality"]
  approval_required_if: ["API contract changes (Rule-09)"]
---

# Quick Reference Card
- When to use: Writing/reviewing backend code, designing APIs, Backend development standards
- 3-step approach:
  1) Enable strict type annotations + MyPy pass
  2) Follow camelCase data field naming standard
  3) Run formatting/Lint/type check/tests via scripts
- How to verify: Quality check scripts exit code 0; key interfaces have type annotations

---

# Backend Development Core Guide

## Code Style Standards

### [Style-00: Language Usage Standards]

#### Comment and Identifier Standards

- **Code identifiers**: **Must** use English (variable names, function names, class names, constants, etc.)
- **Comments and docstrings**: Prefer English, but Chinese comments are allowed
- **Log messages**: **Must** use English (logger.info, logger.error, print outputs)
- **User messages**: **Must** use English (API responses, error messages)

#### Example

```python
# Correct: English identifiers + English logs, Chinese comments allowed
import logging
logger = logging.getLogger(__name__)

async def get_employee_payroll(
    employee_id: str,
    pay_period: str
) -> dict[str, Any]:
    """Get employee payroll data with proper type hints."""
    # Get payroll data for the employee
    payroll_data = await fetch_payroll(employee_id, pay_period)

    logger.info("Employee payroll retrieved", extra={
        "employee_id": employee_id,
        "pay_period": pay_period
    })

    return {
        "employeeId": employee_id,
        "grossPay": payroll_data.gross_pay,
        "netPay": payroll_data.net_pay
    }

# Wrong: Chinese identifiers
async def get_employee_payroll(employee_id: str):
    logger.info("Employee data retrieved")  # English log required
    return {"employeeId": employee_id}
```

---

### [Style-01: Python Type Safety Requirements]

#### Mandatory Requirements

- **Must**: All new functions must have explicit type annotations, including return types
- **Prohibited**: Using unparameterized generic `dict` in new code
- **Must**: Use `dict[str, Any]` instead of bare `dict` in new code
- **Validation**: MyPy strict mode must pass without errors

#### Example

```python
# Correct: Complete type annotations
from typing import Any

async def calculate_gross_pay(
    hours_worked: float,
    hourly_rate: float,
    overtime_hours: float = 0.0
) -> dict[str, Any]:
    """Calculate gross pay with proper type hints."""
    regular_pay = hours_worked * hourly_rate
    overtime_pay = overtime_hours * hourly_rate * 1.5
    return {
        "regularPay": regular_pay,
        "overtimePay": overtime_pay,
        "grossPay": regular_pay + overtime_pay
    }

# Wrong: Missing type annotations
async def calculate_gross_pay(hours_worked, hourly_rate, overtime_hours=0.0):
    regular_pay = hours_worked * hourly_rate
    return {"regularPay": regular_pay}

# Wrong: Using bare dict
def parse_payroll_data(data: str) -> dict:
    return json.loads(data)

# Correct: Using parameterized dict
def parse_payroll_data(data: str) -> dict[str, Any]:
    return json.loads(data)
```

---

### [Style-02: Field Naming Standard - camelCase]

#### Mandatory Requirements

- **Must**: All data fields (Supabase storage, API responses, internal passing) use **camelCase** naming
- **Must**: Python code identifiers (function names, variable names, class names) follow PEP 8 snake_case
- **Prohibited**: Creating snake_case data fields in new code (like `employee_id`, `pay_date`)

#### Naming Reference

| Data Field Type | Wrong (snake_case) | Correct (camelCase) |
|----------------|-------------------|---------------------|
| **Employee** | `employee_id` | `employeeId` |
| | `first_name` | `firstName` |
| | `pay_rate` | `payRate` |
| | `hire_date` | `hireDate` |
| **Payroll** | `gross_pay` | `grossPay` |
| | `net_pay` | `netPay` |
| | `pay_date` | `payDate` |
| | `pay_period_start` | `payPeriodStart` |
| **Tax** | `federal_tax` | `federalTax` |
| | `provincial_tax` | `provincialTax` |
| | `cpp_contribution` | `cppContribution` |
| | `ei_premium` | `eiPremium` |
| **Metadata** | `created_at` | `createdAt` |
| | `updated_at` | `updatedAt` |
| | `company_id` | `companyId` |

#### Example

```python
# Correct: API response uses camelCase
payroll_response = {
    "employeeId": employee_id,           # camelCase
    "payDate": pay_date,                 # camelCase
    "grossPay": gross_pay,               # camelCase
    "deductions": {
        "federalTax": federal_tax,       # camelCase
        "provincialTax": provincial_tax, # camelCase
        "cppContribution": cpp,          # camelCase
        "eiPremium": ei,                 # camelCase
    },
    "netPay": net_pay,                   # camelCase
    "createdAt": now,                    # camelCase
}

# Correct: Python function names use snake_case
async def calculate_payroll_deductions(employee_data: dict[str, Any]) -> dict[str, Any]:
    # Function name: snake_case
    # Data fields: camelCase
    gross_pay = employee_data.get("grossPay")
    pay_date = employee_data.get("payDate")
    return {"netPay": gross_pay - total_deductions}

# Wrong: API response uses snake_case
payroll_response = {
    "employee_id": employee_id,    # Should be employeeId
    "pay_date": pay_date,          # Should be payDate
    "gross_pay": gross_pay,        # Should be grossPay
}
```

#### Pydantic Model Handling

```python
from pydantic import BaseModel

# Correct: Request model uses camelCase fields
class PayrollRunRequest(BaseModel):
    companyId: str       # noqa: N815 - camelCase data field
    payGroupId: str      # noqa: N815
    payDate: str         # noqa: N815
    payPeriodStart: str  # noqa: N815
    payPeriodEnd: str    # noqa: N815

# Correct: Response model also uses camelCase
class EmployeePayrollResponse(BaseModel):
    employeeId: str
    grossPay: float
    netPay: float
    deductions: dict[str, float]
    createdAt: str
```

**Note**: `# noqa: N815` suppresses Ruff warnings for camelCase field names

---

## Quality Check Commands

### Required Validation

```bash
cd backend

# Code formatting check
uv run ruff format --check .

# Linting
uv run ruff check .

# Type checking
uv run mypy .

# Run tests
uv run pytest
```

**Requirement**: Must complete with exit code 0.

### Individual Tool Commands (for local debugging)

```bash
cd backend

# Auto-format code
uv run ruff format .

# Linting with auto-fix
uv run ruff check . --fix

# Type checking
uv run mypy .

# Run tests with coverage
uv run pytest --cov=app
```

---

## Backend Development Workflow

### 1. Environment Setup

```bash
cd backend
uv sync  # Install/update dependencies
```

### 2. Development Process

```python
# Creating new API endpoint example
from fastapi import APIRouter, Depends
from app.services.payroll_service import PayrollService
from app.models.payroll import PayrollRunRequest, PayrollRunResponse

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])

@router.post("/run", response_model=PayrollRunResponse)
async def create_payroll_run(
    request: PayrollRunRequest,
    service: PayrollService = Depends(get_payroll_service)
) -> PayrollRunResponse:
    """Create a new payroll run."""
    logger.info("Creating payroll run", extra={
        "company_id": request.companyId,
        "pay_date": request.payDate
    })

    result = await service.create_payroll_run(request)

    logger.info("Payroll run created", extra={"run_id": result.id})
    return PayrollRunResponse.from_domain(result)
```

### 3. Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/services/test_payroll_service.py

# With coverage report
uv run pytest --cov=app --cov-report=html
```

---

## Common Patterns

### FastAPI Dependency Injection

```python
from fastapi import Depends
from app.core.dependencies import get_current_user, get_payroll_service

@router.get("/employees/{employee_id}/payroll")
async def get_employee_payroll(
    employee_id: str,
    company_id: str,
    current_user: User = Depends(get_current_user),
    service: PayrollService = Depends(get_payroll_service)
) -> PayrollResponse:
    """Get payroll for specific employee."""
    payroll = await service.get_employee_payroll(company_id, employee_id)
    return PayrollResponse.from_domain(payroll)
```

---

### Pydantic Model Validation

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date

class EmployeePayInput(BaseModel):
    """Employee pay input model."""

    employeeId: str
    hoursWorked: float = Field(..., ge=0, le=168)
    overtimeHours: float = Field(default=0, ge=0)
    payDate: date

    @field_validator("hoursWorked")
    @classmethod
    def validate_hours(cls, v: float) -> float:
        """Validate hours worked is reasonable."""
        if v < 0 or v > 168:
            raise ValueError("Hours worked must be between 0 and 168")
        return v
```

---

### Supabase Integration

```python
from supabase import create_client, Client

async def get_employees_by_pay_group(
    supabase: Client,
    company_id: str,
    pay_group_id: str
) -> list[dict[str, Any]]:
    """Get all employees in a pay group."""
    response = supabase.table("employees") \
        .select("*") \
        .eq("companyId", company_id) \
        .eq("payGroupId", pay_group_id) \
        .eq("isActive", True) \
        .execute()

    return response.data
```

---

## Violation Checklist

Before submitting, check:

- [ ] All new functions have type annotations?
- [ ] Data fields use camelCase (not snake_case)?
- [ ] Quality check commands pass (exit code 0)?
- [ ] Tests cover new functionality?
- [ ] Code identifiers use English?
- [ ] Log messages use English?
- [ ] Using logger instead of print()?
- [ ] I/O operations are async?
- [ ] Business logic in Service layer, not API layer?

---

## Related Resources

- **Core Architecture**: See `core-architecture` skill
- **Workflow Policies**: See `workflow-policies` skill
- **Payroll Domain**: See `payroll-domain` skill
- **Frontend Development**: See `frontend-development` skill
