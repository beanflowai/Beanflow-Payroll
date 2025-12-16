# Phase 7 (continued): Garnishments and Court-Ordered Deductions

## Overview

Garnishments are **court-ordered** or **government-mandated deductions** from an employee's wages to pay debts. Employers are legally obligated to comply with garnishment orders and remit the deducted amounts to the appropriate creditor or government agency.

### Legal Requirements

- **Mandatory Compliance**: Employers **must** comply with valid garnishment orders
- **Priority Order**: Multiple garnishments have a legal priority order (child support > CRA RTP > creditor garnishments)
- **Exemption Amounts**: Provincial laws protect a portion of employee wages from garnishment
- **Remittance**: Deducted amounts must be remitted to the creditor/agency within specified timeframes
- **Penalties**: Failure to comply can result in employer liability for the full debt

### Types of Garnishments

1. **Child Support / Family Support Orders** (highest priority)
2. **CRA Requirement to Pay (RTP)** - tax debts
3. **Student Loan Garnishments** - federal/provincial student loans
4. **Creditor Garnishments** - court judgments for unpaid debts
5. **Pension Diversion Orders** - division of pension benefits

### Official References

- **Federal Garnishment Exemptions**: Family Orders and Agreements Enforcement Assistance Act
- **CRA RTP**: https://www.canada.ca/en/revenue-agency/services/about-canada-revenue-agency-cra/when-you-money-collections-cra/collection-actions/garnishment.html
- **Provincial Exemptions**: Varies by province (Employment Standards Act, Creditors Relief Act, etc.)

---

## 1. Data Model

### 1.1 Garnishment Types and Priority

```python
from enum import Enum
from decimal import Decimal
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator

class GarnishmentType(str, Enum):
    """
    Types of garnishments with legal priority

    Priority order (1 = highest):
    1. Child/Family Support
    2. CRA Requirement to Pay (RTP)
    3. Student Loan Garnishment
    4. Creditor Garnishment
    """
    CHILD_SUPPORT = "child_support"
    FAMILY_SUPPORT = "family_support"
    CRA_RTP = "cra_rtp"
    STUDENT_LOAN_FEDERAL = "student_loan_federal"
    STUDENT_LOAN_PROVINCIAL = "student_loan_provincial"
    CREDITOR_GARNISHMENT = "creditor_garnishment"
    PENSION_DIVERSION = "pension_diversion"

    @classmethod
    def get_priority(cls, garnishment_type: str) -> int:
        """
        Get priority order for garnishment type (1 = highest priority)
        """
        priority_map = {
            cls.CHILD_SUPPORT: 1,
            cls.FAMILY_SUPPORT: 1,
            cls.CRA_RTP: 2,
            cls.STUDENT_LOAN_FEDERAL: 3,
            cls.STUDENT_LOAN_PROVINCIAL: 3,
            cls.CREDITOR_GARNISHMENT: 4,
            cls.PENSION_DIVERSION: 5
        }
        return priority_map.get(garnishment_type, 99)


class GarnishmentStatus(str, Enum):
    """Status of garnishment order"""
    ACTIVE = "active"
    SUSPENDED = "suspended"  # Temporarily paused by court order
    COMPLETED = "completed"  # Debt fully paid
    CANCELLED = "cancelled"  # Order cancelled by court


class Garnishment(BaseModel):
    """
    Garnishment or court-ordered deduction

    Represents a legal order to deduct money from employee's wages
    """
    garnishment_id: str = Field(default_factory=lambda: f"garn_{date.today().isoformat()}")
    employee_id: str

    # Garnishment Details
    garnishment_type: GarnishmentType
    description: str = Field(..., max_length=255)

    # Order Information
    court_order_number: Optional[str] = Field(None, max_length=50)
    issuing_authority: str = Field(..., max_length=100)  # Court name, CRA, etc.
    order_date: date
    effective_date: date
    end_date: Optional[date] = Field(None, description="Date garnishment should end (if known)")

    # Deduction Amount
    deduction_type: str = Field(
        ...,
        regex="^(fixed_amount|percentage_gross|percentage_net)$",
        description="How deduction is calculated"
    )
    deduction_amount: Optional[Decimal] = Field(
        None,
        decimal_places=2,
        description="Fixed amount per pay period (if deduction_type=fixed_amount)"
    )
    deduction_percentage: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Percentage to deduct (if deduction_type=percentage_*)"
    )

    # Total Debt (if applicable)
    total_debt_amount: Optional[Decimal] = Field(
        None,
        decimal_places=2,
        description="Total amount owed (for tracking progress)"
    )
    amount_deducted_to_date: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Running total of deductions"
    )

    # Exemption Rules (Provincial)
    exempt_amount: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Amount of wages exempt from garnishment (provincial law)"
    )

    # Remittance Information
    remit_to_name: str = Field(..., max_length=100)
    remit_to_address_line1: str = Field(..., max_length=100)
    remit_to_address_line2: Optional[str] = Field(None, max_length=100)
    remit_to_city: str
    remit_to_province: str = Field(..., regex=r"^[A-Z]{2}$")
    remit_to_postal_code: str = Field(..., regex=r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$")
    remittance_reference: Optional[str] = Field(None, max_length=50)

    # Status
    status: GarnishmentStatus = Field(default=GarnishmentStatus.ACTIVE)

    # Priority (auto-calculated based on type)
    @property
    def priority(self) -> int:
        return GarnishmentType.get_priority(self.garnishment_type)

    @validator("deduction_amount")
    def validate_deduction_amount(cls, v, values):
        """Ensure deduction_amount is provided if deduction_type is fixed_amount"""
        deduction_type = values.get("deduction_type")
        if deduction_type == "fixed_amount" and (v is None or v <= Decimal("0")):
            raise ValueError("deduction_amount must be > 0 for fixed_amount deduction_type")
        return v

    @validator("deduction_percentage")
    def validate_deduction_percentage(cls, v, values):
        """Ensure deduction_percentage is provided if deduction_type is percentage_*"""
        deduction_type = values.get("deduction_type")
        if deduction_type in ["percentage_gross", "percentage_net"]:
            if v is None or v <= Decimal("0"):
                raise ValueError("deduction_percentage must be > 0 for percentage deduction_type")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "garnishment_id": "garn_2025-01-15",
                "employee_id": "emp_001",
                "garnishment_type": "child_support",
                "description": "Child Support Order - Family Court",
                "court_order_number": "FC-2024-12345",
                "issuing_authority": "Ontario Superior Court of Justice",
                "order_date": "2024-12-01",
                "effective_date": "2025-01-01",
                "deduction_type": "fixed_amount",
                "deduction_amount": "500.00",
                "total_debt_amount": None,  # Ongoing support
                "exempt_amount": "0.00",  # Child support not subject to exemption
                "remit_to_name": "Family Responsibility Office",
                "remit_to_address_line1": "PO Box 200, Station A",
                "remit_to_city": "Toronto",
                "remit_to_province": "ON",
                "remit_to_postal_code": "M5W1X8",
                "remittance_reference": "FRO-12345678",
                "status": "active"
            }
        }
```

---

## 2. Provincial Exemption Rules

### 2.1 Exemption Amount by Province

```python
from decimal import Decimal

class ProvincialGarnishmentExemptions:
    """
    Provincial garnishment exemption rules

    Most provinces protect a portion of wages from creditor garnishments
    (does NOT apply to child support or CRA RTP)
    """

    @staticmethod
    def get_exemption_amount(
        province: str,
        gross_pay: Decimal,
        garnishment_type: GarnishmentType
    ) -> Decimal:
        """
        Calculate exempt amount based on provincial rules

        Args:
            province: Province code (e.g., "ON", "BC")
            gross_pay: Gross pay for the period
            garnishment_type: Type of garnishment

        Returns:
            Exempt amount (portion of wages protected from garnishment)
        """
        # Child support and CRA RTP have no exemptions
        if garnishment_type in [GarnishmentType.CHILD_SUPPORT, GarnishmentType.FAMILY_SUPPORT]:
            return Decimal("0")

        if garnishment_type == GarnishmentType.CRA_RTP:
            # CRA RTP has its own calculation (not covered here)
            return Decimal("0")

        # Provincial exemptions for creditor garnishments
        if province == "ON":
            # Ontario: 80% of gross wages are exempt
            return (gross_pay * Decimal("0.80")).quantize(Decimal("0.01"))

        elif province == "BC":
            # BC: $500/month + 70% of income over $500
            # For simplicity, approximate based on gross pay
            monthly_gross = gross_pay * Decimal("2.17")  # Approximate bi-weekly to monthly
            if monthly_gross <= Decimal("500"):
                return gross_pay  # Full exemption
            else:
                exempt_monthly = Decimal("500") + (monthly_gross - Decimal("500")) * Decimal("0.70")
                return (exempt_monthly / Decimal("2.17")).quantize(Decimal("0.01"))

        elif province == "AB":
            # Alberta: Greater of $800/month or 50% of net income
            # Simplified: use 50% of gross as approximation
            return (gross_pay * Decimal("0.50")).quantize(Decimal("0.01"))

        elif province == "SK":
            # Saskatchewan: Varies by judgment type, typically 60-70% exempt
            return (gross_pay * Decimal("0.65")).quantize(Decimal("0.01"))

        elif province == "MB":
            # Manitoba: 70% of net wages exempt
            # Approximation: 60% of gross
            return (gross_pay * Decimal("0.60")).quantize(Decimal("0.01"))

        elif province in ["NS", "NB", "PE", "NL"]:
            # Atlantic provinces: Typically 70-80% exempt
            return (gross_pay * Decimal("0.75")).quantize(Decimal("0.01"))

        elif province in ["YT", "NT", "NU"]:
            # Territories: Similar to BC/AB
            return (gross_pay * Decimal("0.60")).quantize(Decimal("0.01"))

        else:
            # Default: 70% exempt
            return (gross_pay * Decimal("0.70")).quantize(Decimal("0.01"))

    @staticmethod
    def calculate_maximum_garnishment(
        province: str,
        gross_pay: Decimal,
        garnishment_type: GarnishmentType
    ) -> Decimal:
        """
        Calculate maximum amount that can be garnished

        Returns:
            Maximum garnishment amount for this pay period
        """
        exempt = ProvincialGarnishmentExemptions.get_exemption_amount(
            province, gross_pay, garnishment_type
        )
        max_garnishment = gross_pay - exempt
        return max(Decimal("0"), max_garnishment)
```

---

## 3. Garnishment Calculation Service

### 3.1 Calculate Deductions with Priority

```python
from typing import List, Dict
from decimal import Decimal

class GarnishmentCalculationService:
    """
    Calculate garnishment deductions with priority order and exemption rules
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def calculate_garnishment_deductions(
        self,
        ledger_id: str,
        employee_id: str,
        gross_pay: Decimal,
        net_pay_before_garnishments: Decimal,
        province: str
    ) -> Dict[str, any]:
        """
        Calculate all garnishment deductions for an employee

        Args:
            ledger_id: Ledger identifier
            employee_id: Employee identifier
            gross_pay: Gross pay for the period
            net_pay_before_garnishments: Net pay before garnishments
            province: Province of employment

        Returns:
            Dictionary with garnishment details and total deduction
        """
        # Fetch active garnishments for employee
        garnishments = await self.firestore.get_active_garnishments(ledger_id, employee_id)

        if not garnishments:
            return {
                "total_garnishment": Decimal("0"),
                "garnishments_applied": [],
                "net_pay_after_garnishments": net_pay_before_garnishments
            }

        # Sort garnishments by priority (child support first, creditors last)
        garnishments.sort(key=lambda g: g.priority)

        # Calculate deductions
        garnishments_applied = []
        total_deducted = Decimal("0")
        remaining_gross = gross_pay
        remaining_net = net_pay_before_garnishments

        for garnishment in garnishments:
            # Calculate deduction for this garnishment
            deduction = self._calculate_single_garnishment(
                garnishment=garnishment,
                gross_pay=gross_pay,
                net_pay=net_pay_before_garnishments,
                remaining_gross=remaining_gross,
                remaining_net=remaining_net,
                province=province
            )

            if deduction > Decimal("0"):
                garnishments_applied.append({
                    "garnishment_id": garnishment.garnishment_id,
                    "type": garnishment.garnishment_type,
                    "description": garnishment.description,
                    "priority": garnishment.priority,
                    "deduction": float(deduction)
                })

                total_deducted += deduction
                remaining_net -= deduction

                # Update garnishment amount_deducted_to_date
                await self._update_garnishment_progress(
                    ledger_id, garnishment.garnishment_id, deduction
                )

            # Stop if no net pay remaining
            if remaining_net <= Decimal("0"):
                break

        net_pay_after_garnishments = net_pay_before_garnishments - total_deducted

        return {
            "total_garnishment": total_deducted,
            "garnishments_applied": garnishments_applied,
            "net_pay_after_garnishments": net_pay_after_garnishments
        }

    def _calculate_single_garnishment(
        self,
        garnishment: Garnishment,
        gross_pay: Decimal,
        net_pay: Decimal,
        remaining_gross: Decimal,
        remaining_net: Decimal,
        province: str
    ) -> Decimal:
        """
        Calculate deduction for a single garnishment

        Args:
            garnishment: Garnishment order
            gross_pay: Original gross pay
            net_pay: Original net pay (before garnishments)
            remaining_gross: Gross pay available for garnishment
            remaining_net: Net pay available for garnishment
            province: Province code

        Returns:
            Deduction amount for this garnishment
        """
        # Calculate base deduction
        if garnishment.deduction_type == "fixed_amount":
            deduction = garnishment.deduction_amount

        elif garnishment.deduction_type == "percentage_gross":
            deduction = (gross_pay * garnishment.deduction_percentage / Decimal("100")).quantize(Decimal("0.01"))

        elif garnishment.deduction_type == "percentage_net":
            deduction = (net_pay * garnishment.deduction_percentage / Decimal("100")).quantize(Decimal("0.01"))

        else:
            raise ValueError(f"Unknown deduction type: {garnishment.deduction_type}")

        # Apply exemption rules (for creditor garnishments only)
        max_garnishment = ProvincialGarnishmentExemptions.calculate_maximum_garnishment(
            province=province,
            gross_pay=gross_pay,
            garnishment_type=garnishment.garnishment_type
        )

        # Limit to maximum garnishment
        deduction = min(deduction, max_garnishment)

        # Limit to remaining net pay
        deduction = min(deduction, remaining_net)

        # Ensure non-negative
        deduction = max(Decimal("0"), deduction)

        # If total debt is known, don't exceed remaining debt
        if garnishment.total_debt_amount:
            remaining_debt = garnishment.total_debt_amount - garnishment.amount_deducted_to_date
            deduction = min(deduction, remaining_debt)

        return deduction.quantize(Decimal("0.01"))

    async def _update_garnishment_progress(
        self,
        ledger_id: str,
        garnishment_id: str,
        deduction: Decimal
    ):
        """Update garnishment amount_deducted_to_date"""
        garnishment = await self.firestore.get_garnishment(ledger_id, garnishment_id)

        garnishment.amount_deducted_to_date += deduction

        # Check if debt is fully paid
        if garnishment.total_debt_amount:
            if garnishment.amount_deducted_to_date >= garnishment.total_debt_amount:
                garnishment.status = GarnishmentStatus.COMPLETED

        await self.firestore.update_garnishment(ledger_id, garnishment_id, garnishment)
```

---

## 4. Garnishment Remittance Tracking

### 4.1 Remittance Data Model

```python
from datetime import date
from typing import List
from decimal import Decimal
from pydantic import BaseModel

class GarnishmentRemittance(BaseModel):
    """
    Track garnishment remittances to creditors/agencies

    Similar to payroll remittance, but for garnishments
    """
    remittance_id: str
    ledger_id: str
    garnishment_id: str
    employee_id: str

    # Period covered
    period_start_date: date
    period_end_date: date

    # Deductions included
    total_amount: Decimal = Field(..., decimal_places=2)
    deduction_count: int = Field(..., ge=1)

    # Remittance details
    remit_to_name: str
    remit_to_address: str
    remittance_reference: Optional[str]

    # Payment tracking
    paid: bool = False
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_confirmation: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "remittance_id": "grem_2025-01-31",
                "ledger_id": "ledger_12345",
                "garnishment_id": "garn_2025-01-15",
                "employee_id": "emp_001",
                "period_start_date": "2025-01-01",
                "period_end_date": "2025-01-31",
                "total_amount": "1000.00",
                "deduction_count": 2,
                "remit_to_name": "Family Responsibility Office",
                "remit_to_address": "PO Box 200, Station A, Toronto ON M5W1X8",
                "remittance_reference": "FRO-12345678",
                "paid": False
            }
        }


class GarnishmentRemittanceService:
    """
    Track and manage garnishment remittances
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def generate_monthly_remittances(
        self,
        ledger_id: str,
        month: int,
        year: int
    ) -> List[GarnishmentRemittance]:
        """
        Generate monthly remittance records for all garnishments

        Groups deductions by garnishment and creates remittance records

        Args:
            ledger_id: Ledger identifier
            month: Month (1-12)
            year: Year

        Returns:
            List of GarnishmentRemittance records
        """
        # Fetch all payroll records for the month
        start_date = date(year, month, 1)
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        payroll_records = await self.firestore.get_payroll_records(
            ledger_id=ledger_id,
            start_date=start_date,
            end_date=end_date
        )

        # Group garnishment deductions by garnishment_id
        garnishment_totals = {}

        for record in payroll_records:
            if hasattr(record, "garnishment_deductions") and record.garnishment_deductions:
                for deduction in record.garnishment_deductions:
                    garn_id = deduction["garnishment_id"]

                    if garn_id not in garnishment_totals:
                        garnishment_totals[garn_id] = {
                            "employee_id": record.employee_id,
                            "total_amount": Decimal("0"),
                            "deduction_count": 0
                        }

                    garnishment_totals[garn_id]["total_amount"] += Decimal(str(deduction["amount"]))
                    garnishment_totals[garn_id]["deduction_count"] += 1

        # Create remittance records
        remittances = []

        for garn_id, data in garnishment_totals.items():
            garnishment = await self.firestore.get_garnishment(ledger_id, garn_id)

            remittance = GarnishmentRemittance(
                remittance_id=f"grem_{year}-{month:02d}_{garn_id}",
                ledger_id=ledger_id,
                garnishment_id=garn_id,
                employee_id=data["employee_id"],
                period_start_date=start_date,
                period_end_date=end_date,
                total_amount=data["total_amount"],
                deduction_count=data["deduction_count"],
                remit_to_name=garnishment.remit_to_name,
                remit_to_address=f"{garnishment.remit_to_address_line1}, {garnishment.remit_to_city} {garnishment.remit_to_province} {garnishment.remit_to_postal_code}",
                remittance_reference=garnishment.remittance_reference
            )

            remittances.append(remittance)

        return remittances
```

---

## 5. Beancount Integration

```python
class BeancountGarnishmentService:
    """
    Track garnishment deductions and remittances in Beancount
    """

    def __init__(self, beancount_service):
        self.beancount = beancount_service

    async def record_garnishment_deduction(
        self,
        ledger_id: str,
        payroll_date: date,
        employee_name: str,
        garnishment: Garnishment,
        deduction_amount: Decimal
    ) -> str:
        """
        Record garnishment deduction in Beancount (part of payroll entry)

        Args:
            ledger_id: Ledger identifier
            payroll_date: Payroll date
            employee_name: Employee name
            garnishment: Garnishment order
            deduction_amount: Deduction amount

        Returns:
            Transaction ID
        """
        description = f"Garnishment Deduction - {garnishment.description}"

        entry_lines = [
            f"{payroll_date} * \"Payroll\" \"{description}\"",
            f"  Liabilities:Garnishment:{garnishment.garnishment_type}  {deduction_amount:.2f} CAD",
            f"  ; Employee: {employee_name}",
            f"  ; Garnishment ID: {garnishment.garnishment_id}"
        ]

        entry_text = "\n".join(entry_lines)

        transaction_id = await self.beancount.append_transaction(ledger_id, entry_text)

        return transaction_id

    async def record_garnishment_remittance(
        self,
        ledger_id: str,
        remittance: GarnishmentRemittance,
        payment_date: date
    ) -> str:
        """
        Record garnishment remittance payment in Beancount

        Args:
            ledger_id: Ledger identifier
            remittance: GarnishmentRemittance
            payment_date: Payment date

        Returns:
            Transaction ID
        """
        garnishment = await self.beancount.firestore.get_garnishment(
            ledger_id, remittance.garnishment_id
        )

        description = f"Garnishment Remittance - {remittance.remit_to_name}"

        entry_lines = [
            f"{payment_date} * \"Garnishment Remittance\" \"{description}\"",
            f"  Liabilities:Garnishment:{garnishment.garnishment_type}  -{remittance.total_amount:.2f} CAD",
            f"  Assets:Bank:Chequing  -{remittance.total_amount:.2f} CAD",
            f"  ; Reference: {remittance.remittance_reference or 'N/A'}",
            f"  ; Period: {remittance.period_start_date} to {remittance.period_end_date}"
        ]

        entry_text = "\n".join(entry_lines)

        transaction_id = await self.beancount.append_transaction(ledger_id, entry_text)

        return transaction_id
```

---

## 6. API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List

router = APIRouter(prefix="/api/v1/garnishments", tags=["garnishments"])

@router.post("/create/{ledger_id}/{employee_id}")
async def create_garnishment(
    ledger_id: str,
    employee_id: str,
    garnishment: Garnishment,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Create a new garnishment order for an employee

    Requires uploading court order document
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate employee exists
    employee = await firestore_service.get_employee(ledger_id, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Save garnishment
    garnishment_id = await firestore_service.create_garnishment(ledger_id, garnishment)

    return {
        "message": "Garnishment created successfully",
        "garnishment_id": garnishment_id
    }


@router.get("/list/{ledger_id}")
async def list_garnishments(
    ledger_id: str,
    employee_id: Optional[str] = None,
    status: Optional[GarnishmentStatus] = None,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    List all garnishments (optionally filtered by employee or status)
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    garnishments = await firestore_service.get_garnishments(
        ledger_id=ledger_id,
        employee_id=employee_id,
        status=status
    )

    return {
        "total": len(garnishments),
        "garnishments": [g.dict() for g in garnishments]
    }


@router.put("/update-status/{ledger_id}/{garnishment_id}")
async def update_garnishment_status(
    ledger_id: str,
    garnishment_id: str,
    new_status: GarnishmentStatus,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Update garnishment status (e.g., suspend, cancel, complete)
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    garnishment = await firestore_service.get_garnishment(ledger_id, garnishment_id)
    if not garnishment:
        raise HTTPException(status_code=404, detail="Garnishment not found")

    garnishment.status = new_status
    await firestore_service.update_garnishment(ledger_id, garnishment_id, garnishment)

    return {
        "message": f"Garnishment status updated to {new_status}",
        "garnishment_id": garnishment_id
    }


@router.get("/remittances/{ledger_id}/{year}/{month}")
async def get_monthly_remittances(
    ledger_id: str,
    year: int,
    month: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Get garnishment remittances for a specific month
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    remittance_service = GarnishmentRemittanceService(firestore_service)
    remittances = await remittance_service.generate_monthly_remittances(
        ledger_id=ledger_id,
        month=month,
        year=year
    )

    return {
        "year": year,
        "month": month,
        "total_remittances": len(remittances),
        "remittances": [r.dict() for r in remittances]
    }


@router.post("/record-remittance-payment/{ledger_id}/{remittance_id}")
async def record_remittance_payment(
    ledger_id: str,
    remittance_id: str,
    payment_date: date,
    payment_method: str,
    confirmation_number: Optional[str] = None,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Record garnishment remittance payment
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    remittance = await firestore_service.get_garnishment_remittance(ledger_id, remittance_id)
    if not remittance:
        raise HTTPException(status_code=404, detail="Remittance not found")

    # Update remittance
    remittance.paid = True
    remittance.payment_date = payment_date
    remittance.payment_method = payment_method
    remittance.payment_confirmation = confirmation_number

    await firestore_service.update_garnishment_remittance(ledger_id, remittance_id, remittance)

    # Record in Beancount
    beancount_service = BeancountGarnishmentService(get_beancount_service())
    transaction_id = await beancount_service.record_garnishment_remittance(
        ledger_id=ledger_id,
        remittance=remittance,
        payment_date=payment_date
    )

    return {
        "message": "Remittance payment recorded successfully",
        "remittance_id": remittance_id,
        "beancount_transaction_id": transaction_id
    }
```

---

## 7. Testing

```python
import pytest
from decimal import Decimal
from datetime import date

def test_garnishment_priority():
    """Test garnishment priority order"""
    assert GarnishmentType.get_priority(GarnishmentType.CHILD_SUPPORT) == 1
    assert GarnishmentType.get_priority(GarnishmentType.CRA_RTP) == 2
    assert GarnishmentType.get_priority(GarnishmentType.CREDITOR_GARNISHMENT) == 4


def test_ontario_exemption():
    """Test Ontario 80% exemption"""
    gross = Decimal("2000.00")
    exempt = ProvincialGarnishmentExemptions.get_exemption_amount(
        province="ON",
        gross_pay=gross,
        garnishment_type=GarnishmentType.CREDITOR_GARNISHMENT
    )

    assert exempt == Decimal("1600.00")  # 80% of $2000

    max_garn = ProvincialGarnishmentExemptions.calculate_maximum_garnishment(
        province="ON",
        gross_pay=gross,
        garnishment_type=GarnishmentType.CREDITOR_GARNISHMENT
    )

    assert max_garn == Decimal("400.00")  # 20% of $2000


def test_child_support_no_exemption():
    """Test child support has no exemption"""
    gross = Decimal("2000.00")
    exempt = ProvincialGarnishmentExemptions.get_exemption_amount(
        province="ON",
        gross_pay=gross,
        garnishment_type=GarnishmentType.CHILD_SUPPORT
    )

    assert exempt == Decimal("0.00")  # No exemption for child support


def test_garnishment_validation():
    """Test garnishment data validation"""
    # Fixed amount garnishment
    garn = Garnishment(
        employee_id="emp_001",
        garnishment_type=GarnishmentType.CHILD_SUPPORT,
        description="Child Support",
        issuing_authority="Family Court",
        order_date=date(2024, 1, 1),
        effective_date=date(2024, 2, 1),
        deduction_type="fixed_amount",
        deduction_amount=Decimal("500.00"),
        remit_to_name="FRO",
        remit_to_address_line1="PO Box 200",
        remit_to_city="Toronto",
        remit_to_province="ON",
        remit_to_postal_code="M5W1X8"
    )

    assert garn.priority == 1
    assert garn.status == GarnishmentStatus.ACTIVE

    # Missing deduction_amount should raise error
    with pytest.raises(ValueError, match="deduction_amount must be > 0"):
        Garnishment(
            employee_id="emp_001",
            garnishment_type=GarnishmentType.CHILD_SUPPORT,
            description="Child Support",
            issuing_authority="Family Court",
            order_date=date(2024, 1, 1),
            effective_date=date(2024, 2, 1),
            deduction_type="fixed_amount",
            deduction_amount=None,  # Missing!
            remit_to_name="FRO",
            remit_to_address_line1="PO Box 200",
            remit_to_city="Toronto",
            remit_to_province="ON",
            remit_to_postal_code="M5W1X8"
        )
```

---

## 8. Implementation Checklist

- [ ] **Data Models**
  - [ ] Implement `GarnishmentType` enum with priority
  - [ ] Implement `Garnishment` model with validation
  - [ ] Implement `GarnishmentRemittance` model
  - [ ] Test data validation

- [ ] **Provincial Exemptions**
  - [ ] Implement exemption calculation for all provinces
  - [ ] Test exemption rules
  - [ ] Document provincial differences

- [ ] **Calculation Service**
  - [ ] Implement garnishment calculation with priority
  - [ ] Handle multiple simultaneous garnishments
  - [ ] Apply exemption rules
  - [ ] Test edge cases (insufficient net pay, debt completion)

- [ ] **Remittance Tracking**
  - [ ] Implement monthly remittance generation
  - [ ] Track garnishment progress
  - [ ] Auto-complete when debt paid

- [ ] **Beancount Integration**
  - [ ] Record garnishment deductions
  - [ ] Record remittance payments
  - [ ] Test double-entry accuracy

- [ ] **API Endpoints**
  - [ ] Implement garnishment CRUD endpoints
  - [ ] Implement remittance endpoints
  - [ ] Add authorization checks

- [ ] **Testing**
  - [ ] Unit tests for all services
  - [ ] Integration tests
  - [ ] Test with multiple simultaneous garnishments

---

**Document Version**: 1.0
**Created**: 2025-10-09
**For**: Beancount-LLM Canadian Payroll System - Phase 7 Implementation (Garnishments)
