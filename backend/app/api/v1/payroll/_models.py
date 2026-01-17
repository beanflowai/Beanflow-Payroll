"""
Pydantic request/response models for payroll API endpoints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.payroll import PayFrequency, Province

# =============================================================================
# Calculation Models
# =============================================================================


class EmployeeCalculationRequest(BaseModel):
    """Single employee calculation request."""

    employee_id: str
    province: Province
    pay_frequency: PayFrequency

    # Earnings
    gross_regular: Decimal = Field(..., description="Regular gross pay")
    gross_overtime: Decimal = Field(default=Decimal("0"), description="Overtime pay")
    holiday_pay: Decimal = Field(default=Decimal("0"), description="Holiday pay")
    holiday_premium_pay: Decimal = Field(
        default=Decimal("0"), description="Holiday premium pay (1.5x or 2x)"
    )
    vacation_pay: Decimal = Field(default=Decimal("0"), description="Vacation pay")
    other_earnings: Decimal = Field(default=Decimal("0"), description="Other earnings")
    bonus_earnings: Decimal = Field(default=Decimal("0"), description="Bonus/lump-sum earnings taxed using bonus method")

    # TD1 Claims
    federal_claim_amount: Decimal = Field(
        default=Decimal("16129"), description="Federal TD1 claim amount"
    )
    provincial_claim_amount: Decimal = Field(
        default=Decimal("12747"), description="Provincial TD1 claim amount"
    )

    # Pre-tax Deductions
    rrsp_per_period: Decimal = Field(default=Decimal("0"), description="RRSP deduction")
    union_dues_per_period: Decimal = Field(
        default=Decimal("0"), description="Union dues"
    )

    # Post-tax Deductions
    garnishments: Decimal = Field(default=Decimal("0"), description="Court-ordered garnishments")
    other_deductions: Decimal = Field(
        default=Decimal("0"), description="Other post-tax deductions"
    )

    # YTD Values
    ytd_gross: Decimal = Field(
        default=Decimal("0"), description="Year-to-date gross earnings"
    )
    ytd_pensionable_earnings: Decimal = Field(
        default=Decimal("0"), description="Year-to-date pensionable earnings"
    )
    ytd_insurable_earnings: Decimal = Field(
        default=Decimal("0"), description="Year-to-date insurable earnings"
    )
    ytd_cpp_base: Decimal = Field(
        default=Decimal("0"), description="Year-to-date base CPP contributions"
    )
    ytd_cpp_additional: Decimal = Field(
        default=Decimal("0"), description="Year-to-date CPP2 contributions"
    )
    ytd_ei: Decimal = Field(
        default=Decimal("0"), description="Year-to-date EI premiums"
    )

    # Exemptions
    is_cpp_exempt: bool = Field(default=False, description="CPP exemption status")
    is_ei_exempt: bool = Field(default=False, description="EI exemption status")
    cpp2_exempt: bool = Field(
        default=False, description="CPP2 exemption (CPT30 on file)"
    )


class CalculationResponse(BaseModel):
    """Single employee calculation response."""

    employee_id: str
    province: str

    # Earnings
    gross_regular: Decimal
    gross_overtime: Decimal
    holiday_pay: Decimal
    holiday_premium_pay: Decimal
    vacation_pay: Decimal
    other_earnings: Decimal
    bonus_earnings: Decimal
    total_gross: Decimal

    # Employee Deductions
    cpp_base: Decimal
    cpp_additional: Decimal
    cpp_total: Decimal
    ei_employee: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    rrsp: Decimal
    union_dues: Decimal
    garnishments: Decimal
    other_deductions: Decimal
    total_employee_deductions: Decimal

    # Employer Costs
    cpp_employer: Decimal
    ei_employer: Decimal
    total_employer_costs: Decimal

    # Net Pay
    net_pay: Decimal

    # Updated YTD
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal

    # Calculation Details (optional, for debugging)
    calculation_details: dict[str, Any] | None = None


class BatchCalculationRequest(BaseModel):
    """Batch calculation request for multiple employees."""

    employees: list[EmployeeCalculationRequest]
    include_details: bool = Field(
        default=False, description="Include calculation details in response"
    )


class BatchCalculationResponse(BaseModel):
    """Batch calculation response."""

    results: list[CalculationResponse]
    summary: dict[str, Any]


class PayrollRunCalculationRequest(BaseModel):
    """Request to calculate a complete payroll run."""

    pay_date: str = Field(..., description="Pay date in YYYY-MM-DD format")
    include_details: bool = Field(
        default=False, description="Include calculation details"
    )


class PayrollRunCalculationResponse(BaseModel):
    """Response from payroll run calculation."""

    pay_date: str
    total_employees: int
    total_gross: Decimal
    total_cpp_employee: Decimal
    total_cpp_employer: Decimal
    total_ei_employee: Decimal
    total_ei_employer: Decimal
    total_federal_tax: Decimal
    total_provincial_tax: Decimal
    total_deductions: Decimal
    total_net_pay: Decimal
    total_employer_cost: Decimal
    records: list[CalculationResponse]


# =============================================================================
# Config Models
# =============================================================================


class BPADefaultsResponse(BaseModel):
    """Response for BPA defaults endpoint."""

    year: int
    edition: str = Field(description="'jan' or 'jul' based on pay_date")
    federalBPA: float = Field(description="Federal Basic Personal Amount")
    provincialBPA: float = Field(description="Provincial Basic Personal Amount")
    province: str


# =============================================================================
# Payroll Run Models
# =============================================================================


class LeaveEntryInput(BaseModel):
    """Leave entry input for payroll record update."""

    type: str = Field(..., description="Leave type: 'vacation' or 'sick'")
    hours: float = Field(..., description="Hours of leave taken")


class HolidayWorkInput(BaseModel):
    """Holiday work entry input for payroll record update."""

    holidayDate: str = Field(..., description="Holiday date in YYYY-MM-DD format")
    holidayName: str = Field(..., description="Name of the holiday")
    hoursWorked: float = Field(..., description="Hours worked on the holiday")


class AdjustmentInput(BaseModel):
    """Adjustment input for payroll record update."""

    type: str = Field(
        ..., description="Adjustment type: 'bonus', 'deduction', 'reimbursement', etc."
    )
    amount: float = Field(..., description="Adjustment amount")
    description: str = Field(default="", description="Description of the adjustment")
    taxable: bool = Field(default=True, description="Whether the adjustment is taxable")


class PayrollOverrides(BaseModel):
    """Override values for automatic calculations."""

    regularPay: float | None = Field(default=None, description="Override regular pay")
    overtimePay: float | None = Field(default=None, description="Override overtime pay")
    holidayPay: float | None = Field(default=None, description="Override holiday pay")


class UpdatePayrollRecordRequest(BaseModel):
    """Request to update a payroll record's input data."""

    regularHours: float | None = Field(default=None, description="Regular hours worked")
    overtimeHours: float | None = Field(
        default=None, description="Overtime hours worked"
    )
    leaveEntries: list[LeaveEntryInput] | None = Field(
        default=None, description="Leave entries"
    )
    holidayWorkEntries: list[HolidayWorkInput] | None = Field(
        default=None, description="Holiday work entries"
    )
    adjustments: list[AdjustmentInput] | None = Field(
        default=None, description="One-time adjustments"
    )
    overrides: PayrollOverrides | None = Field(
        default=None, description="Manual override values"
    )
    holidayPayExempt: bool | None = Field(
        default=None,
        description="If true, employee is exempt from regular holiday pay (HR manual override)",
    )


class PayrollRecordResponse(BaseModel):
    """Response from payroll record update."""

    id: str
    employeeId: str = Field(alias="employee_id")
    inputData: dict[str, Any] | None = Field(alias="input_data")
    isModified: bool = Field(alias="is_modified")

    model_config = {"populate_by_name": True}


class PayrollRunResponse(BaseModel):
    """Response from payroll run operations."""

    id: str
    payDate: str = Field(alias="pay_date")
    status: str
    totalEmployees: int = Field(alias="total_employees")
    totalGross: float = Field(alias="total_gross")
    totalCppEmployee: float = Field(alias="total_cpp_employee")
    totalCppEmployer: float = Field(alias="total_cpp_employer")
    totalEiEmployee: float = Field(alias="total_ei_employee")
    totalEiEmployer: float = Field(alias="total_ei_employer")
    totalFederalTax: float = Field(alias="total_federal_tax")
    totalProvincialTax: float = Field(alias="total_provincial_tax")
    totalNetPay: float = Field(alias="total_net_pay")
    totalEmployerCost: float = Field(alias="total_employer_cost")

    model_config = {"populate_by_name": True}


class ListPayrollRunsResponse(BaseModel):
    """Response for listing payroll runs."""

    runs: list[PayrollRunResponse]
    total: int


class SyncEmployeesResponse(BaseModel):
    """Response from sync employees operation."""

    addedCount: int = Field(alias="added_count")
    addedEmployees: list[dict[str, str]] = Field(alias="added_employees")
    run: PayrollRunResponse

    model_config = {"populate_by_name": True}


class CreateOrGetRunRequest(BaseModel):
    """Request to create or get a draft payroll run."""

    periodEnd: str = Field(..., description="Period end date in YYYY-MM-DD format")
    payDate: str | None = Field(
        default=None,
        description="Optional pay date in YYYY-MM-DD format. If not provided, calculated from period_end + province delay",
    )


class CreateOrGetRunResponse(BaseModel):
    """Response from create or get payroll run operation."""

    run: PayrollRunResponse
    created: bool = Field(description="True if a new run was created, False if existing")
    recordsCount: int = Field(alias="records_count", description="Number of records created")

    model_config = {"populate_by_name": True}


class AddEmployeeRequest(BaseModel):
    """Request to add an employee to a payroll run."""

    employeeId: str = Field(..., description="Employee ID to add")


class AddEmployeeResponse(BaseModel):
    """Response from adding an employee to a payroll run."""

    employeeId: str = Field(alias="employee_id")
    employeeName: str = Field(alias="employee_name")

    model_config = {"populate_by_name": True}


class RemoveEmployeeResponse(BaseModel):
    """Response from removing an employee from a payroll run."""

    removed: bool
    employeeId: str = Field(alias="employee_id")

    model_config = {"populate_by_name": True}


class DeleteRunResponse(BaseModel):
    """Response from deleting a payroll run."""

    deleted: bool
    runId: str = Field(alias="run_id")

    model_config = {"populate_by_name": True}


class ApprovePayrollRunResponse(BaseModel):
    """Response from approving a payroll run"""

    id: str
    pay_date: str = Field(alias="payDate")
    status: str
    total_employees: int = Field(alias="totalEmployees")
    total_gross: float = Field(alias="totalGross")
    total_net_pay: float = Field(alias="totalNetPay")
    paystubs_generated: int = Field(alias="paystubsGenerated")
    paystub_errors: list[str] | None = Field(default=None, alias="paystubErrors")

    model_config = {"populate_by_name": True}


class UpdatePayDateRequest(BaseModel):
    """Request to update the pay date of a payroll run."""

    payDate: str = Field(..., description="New pay date in YYYY-MM-DD format")


class UpdatePayDateResponse(BaseModel):
    """Response from updating pay date."""

    id: str
    payDate: str = Field(alias="pay_date")
    status: str
    totalEmployees: int = Field(alias="total_employees")
    totalGross: float = Field(alias="total_gross")
    totalNetPay: float = Field(alias="total_net_pay")
    needsRecalculation: bool = Field(alias="needs_recalculation", default=False)

    model_config = {"populate_by_name": True}


# =============================================================================
# Paystub Models
# =============================================================================


class SendPaystubsResponse(BaseModel):
    """Response from sending paystubs"""

    sent: int = Field(..., description="Number of paystubs sent")
    errors: list[str] | None = Field(default=None, description="List of send errors")


class PaystubUrlResponse(BaseModel):
    """Response for paystub download URL."""

    storageKey: str = Field(..., description="Storage key in DO Spaces")
    downloadUrl: str = Field(..., description="Presigned download URL")
    expiresIn: int = Field(default=900, description="URL expiration in seconds")

    model_config = {"populate_by_name": True}


# =============================================================================
# Sick Leave Models
# =============================================================================


class SickLeaveConfigResponse(BaseModel):
    """Sick leave configuration for a province."""

    provinceCode: str = Field(alias="province_code")
    paidDaysPerYear: int = Field(alias="paid_days_per_year")
    unpaidDaysPerYear: int = Field(alias="unpaid_days_per_year")
    waitingPeriodDays: int = Field(alias="waiting_period_days")
    allowsCarryover: bool = Field(alias="allows_carryover")
    maxCarryoverDays: int = Field(alias="max_carryover_days")
    accrualMethod: str = Field(alias="accrual_method")
    initialDaysAfterQualifying: int = Field(alias="initial_days_after_qualifying")
    daysPerMonthAfterInitial: int = Field(alias="days_per_month_after_initial")
    notes: str | None = None

    model_config = {"populate_by_name": True}


class SickLeaveBalanceResponse(BaseModel):
    """Employee sick leave balance."""

    employeeId: str = Field(alias="employee_id")
    year: int
    paidDaysEntitled: float = Field(alias="paid_days_entitled")
    unpaidDaysEntitled: float = Field(alias="unpaid_days_entitled")
    paidDaysUsed: float = Field(alias="paid_days_used")
    unpaidDaysUsed: float = Field(alias="unpaid_days_used")
    paidDaysRemaining: float = Field(alias="paid_days_remaining")
    unpaidDaysRemaining: float = Field(alias="unpaid_days_remaining")
    carriedOverDays: float = Field(alias="carried_over_days")
    isEligible: bool = Field(alias="is_eligible")
    eligibilityDate: str | None = Field(default=None, alias="eligibility_date")

    model_config = {"populate_by_name": True}
