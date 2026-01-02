"""
Employee Portal API Endpoints

Provides endpoints for employees to access their own payroll data.
Uses email matching to identify the current employee.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, cast

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.core.supabase_client import get_supabase_client
from app.services.payroll_run.gross_calculator import GrossCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employee-portal", tags=["Employee Portal"])


# =============================================================================
# Response Models
# =============================================================================


class PaystubEarning(BaseModel):
    """Earnings line item on paystub."""

    type: str
    hours: float | None = None
    amount: float


class PaystubDeduction(BaseModel):
    """Deduction line item on paystub."""

    type: str
    amount: float


class PaystubYTD(BaseModel):
    """Year-to-date totals on paystub."""

    grossEarnings: float
    cppPaid: float
    eiPaid: float
    taxPaid: float


class EmployeePortalProfile(BaseModel):
    """Current employee's profile information."""

    id: str
    firstName: str
    lastName: str
    email: str
    provinceOfEmployment: str
    payFrequency: str
    hireDate: str | None = None
    vacationBalance: float
    sickDaysRemaining: float


class EmployeePaystub(BaseModel):
    """Paystub summary for list view."""

    id: str
    payDate: str
    payPeriodStart: str
    payPeriodEnd: str
    grossPay: float
    totalDeductions: float
    netPay: float


class EmployeePaystubDetail(EmployeePaystub):
    """Detailed paystub for single view."""

    companyName: str
    employeeName: str
    earnings: list[PaystubEarning]
    deductions: list[PaystubDeduction]
    ytd: PaystubYTD
    # Sick Leave fields
    sickHoursTaken: float = 0.0
    sickPayPaid: float = 0.0
    sickBalanceHours: float = 0.0


class EmployeePaystubListResponse(BaseModel):
    """Response for paystub list endpoint."""

    paystubs: list[EmployeePaystub]
    ytdSummary: PaystubYTD


class LeaveHistoryEntry(BaseModel):
    """Leave usage history entry."""

    date: str
    endDate: str | None = None
    type: str  # 'vacation' or 'sick'
    hours: float
    balanceAfterHours: float
    balanceAfterDollars: float | None = None


class EmployeeLeaveBalanceResponse(BaseModel):
    """Detailed leave balance response."""

    # Vacation
    vacationHours: float
    vacationDollars: float
    vacationAccrualRate: float
    vacationYtdAccrued: float
    vacationYtdUsed: float

    # Sick Leave
    sickHoursRemaining: float
    sickHoursAllowance: float
    sickHoursUsedThisYear: float

    # History
    leaveHistory: list[LeaveHistoryEntry] = Field(default_factory=list)


# =============================================================================
# Helper Functions
# =============================================================================


async def get_employee_by_user_email(current_user: CurrentUser) -> dict[str, Any] | None:
    """Find employee record matching the current user's email."""
    if not current_user.email:
        return None

    supabase = get_supabase_client()

    result = (
        supabase.table("employees")
        .select("*")
        .eq("email", current_user.email)
        .limit(1)
        .execute()
    )

    if result.data:
        return cast(dict[str, Any], result.data[0])
    return None


# =============================================================================
# API Endpoints
# =============================================================================


@router.get(
    "/me",
    response_model=EmployeePortalProfile,
    summary="Get current employee profile",
    description="Get the current employee's profile based on authenticated user email.",
)
async def get_current_employee(current_user: CurrentUser) -> EmployeePortalProfile:
    """Get the current employee's profile."""
    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    # Get sick leave balance
    sick_days_remaining = 0.0
    try:
        from app.services.payroll.sick_leave_service import SickLeaveService

        service = SickLeaveService()
        hire_date = (
            date.fromisoformat(employee["hire_date"])
            if employee.get("hire_date")
            else date.today()
        )
        balance = service.create_new_year_balance(
            employee_id=employee["id"],
            year=date.today().year,
            province_code=employee.get("province_of_employment", "ON"),
            hire_date=hire_date,
        )
        sick_days_remaining = float(balance.paid_days_remaining)
    except Exception:
        logger.exception("Error calculating sick leave balance")

    return EmployeePortalProfile(
        id=employee["id"],
        firstName=employee.get("first_name", ""),
        lastName=employee.get("last_name", ""),
        email=employee.get("email", ""),
        provinceOfEmployment=employee.get("province_of_employment", ""),
        payFrequency=employee.get("pay_frequency", ""),
        hireDate=employee.get("hire_date"),
        vacationBalance=float(employee.get("vacation_balance") or 0),
        sickDaysRemaining=sick_days_remaining,
    )


@router.get(
    "/paystubs",
    response_model=EmployeePaystubListResponse,
    summary="Get my paystubs",
    description="Get the current employee's paystubs for a given year.",
)
async def get_my_paystubs(
    current_user: CurrentUser,
    year: int = 2025,
    limit: int = 20,
) -> EmployeePaystubListResponse:
    """Get paystubs for the current employee."""
    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Filter by year at database level using date range
    year_start = f"{year}-01-01"
    year_end = f"{year + 1}-01-01"

    # Query payroll records for this employee with approved runs only
    result = (
        supabase.table("payroll_records")
        .select(
            """
            id,
            total_gross,
            total_deductions,
            net_pay,
            ytd_gross,
            ytd_cpp,
            ytd_ei,
            ytd_federal_tax,
            ytd_provincial_tax,
            payroll_runs!inner (
                pay_date,
                period_start,
                period_end,
                status
            )
        """
        )
        .eq("employee_id", employee["id"])
        .eq("payroll_runs.status", "approved")
        .gte("payroll_runs.pay_date", year_start)
        .lt("payroll_runs.pay_date", year_end)
        .order("payroll_runs.pay_date", desc=True)
        .limit(limit)
        .execute()
    )

    paystubs: list[EmployeePaystub] = []
    ytd_summary = PaystubYTD(grossEarnings=0, cppPaid=0, eiPaid=0, taxPaid=0)

    for record in result.data or []:
        run = record.get("payroll_runs", {})
        paystubs.append(
            EmployeePaystub(
                id=record["id"],
                payDate=run.get("pay_date", ""),
                payPeriodStart=run.get("period_start", ""),
                payPeriodEnd=run.get("period_end", ""),
                grossPay=float(record.get("total_gross") or 0),
                totalDeductions=float(record.get("total_deductions") or 0),
                netPay=float(record.get("net_pay") or 0),
            )
        )

    # Get YTD from the most recent record of the selected year
    if paystubs and result.data:
        latest_record = result.data[0]
        ytd_summary = PaystubYTD(
            grossEarnings=float(latest_record.get("ytd_gross") or 0),
            cppPaid=float(latest_record.get("ytd_cpp") or 0),
            eiPaid=float(latest_record.get("ytd_ei") or 0),
            taxPaid=float(latest_record.get("ytd_federal_tax") or 0)
            + float(latest_record.get("ytd_provincial_tax") or 0),
        )

    return EmployeePaystubListResponse(paystubs=paystubs, ytdSummary=ytd_summary)


@router.get(
    "/paystubs/{record_id}",
    response_model=EmployeePaystubDetail,
    summary="Get paystub detail",
    description="Get detailed paystub for a specific payroll record.",
)
async def get_paystub_detail(
    record_id: str,
    current_user: CurrentUser,
) -> EmployeePaystubDetail:
    """Get detailed paystub for a specific record."""
    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Query the specific payroll record (only approved paystubs)
    result = (
        supabase.table("payroll_records")
        .select(
            """
            *,
            payroll_runs!inner (
                pay_date,
                period_start,
                period_end,
                status
            )
        """
        )
        .eq("id", record_id)
        .eq("employee_id", employee["id"])
        .eq("payroll_runs.status", "approved")
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paystub not found or not yet approved",
        )

    record = result.data
    run = record.get("payroll_runs", {})

    # Build earnings list
    earnings: list[PaystubEarning] = []

    regular_hours = 80.0  # Default, could be from input_data
    input_data = record.get("input_data") or {}
    if input_data.get("regularHours"):
        regular_hours = float(input_data["regularHours"])

    gross_regular = float(record.get("gross_regular") or 0)
    if gross_regular > 0:
        earnings.append(
            PaystubEarning(type="Regular Pay", hours=regular_hours, amount=gross_regular)
        )

    gross_overtime = float(record.get("gross_overtime") or 0)
    overtime_hours = float(input_data.get("overtimeHours") or 0)
    if gross_overtime > 0:
        earnings.append(
            PaystubEarning(type="Overtime", hours=overtime_hours, amount=gross_overtime)
        )

    vacation_pay = float(record.get("vacation_pay_paid") or 0)
    if vacation_pay > 0:
        earnings.append(PaystubEarning(type="Vacation Pay", amount=vacation_pay))

    # Sick pay (new)
    sick_pay = float(record.get("sick_pay_paid") or 0)
    sick_hours = float(record.get("sick_hours_taken") or 0)
    if sick_pay > 0:
        earnings.append(
            PaystubEarning(type="Sick Pay", hours=sick_hours, amount=sick_pay)
        )

    # Holiday pay (regular + premium combined)
    holiday_pay = float(record.get("holiday_pay") or 0)
    holiday_premium_pay = float(record.get("holiday_premium_pay") or 0)
    total_holiday_pay = holiday_pay + holiday_premium_pay
    if total_holiday_pay > 0:
        earnings.append(PaystubEarning(type="Holiday Pay", amount=total_holiday_pay))

    # Build deductions list
    deductions: list[PaystubDeduction] = [
        PaystubDeduction(type="CPP", amount=float(record.get("cpp_employee") or 0)),
        PaystubDeduction(type="EI", amount=float(record.get("ei_employee") or 0)),
        PaystubDeduction(
            type="Federal Tax", amount=float(record.get("federal_tax") or 0)
        ),
        PaystubDeduction(
            type="Provincial Tax", amount=float(record.get("provincial_tax") or 0)
        ),
    ]

    rrsp = float(record.get("rrsp") or 0)
    if rrsp > 0:
        deductions.append(PaystubDeduction(type="RRSP", amount=rrsp))

    union_dues = float(record.get("union_dues") or 0)
    if union_dues > 0:
        deductions.append(PaystubDeduction(type="Union Dues", amount=union_dues))

    # YTD summary
    ytd = PaystubYTD(
        grossEarnings=float(record.get("ytd_gross") or 0),
        cppPaid=float(record.get("ytd_cpp") or 0),
        eiPaid=float(record.get("ytd_ei") or 0),
        taxPaid=float(record.get("ytd_federal_tax") or 0)
        + float(record.get("ytd_provincial_tax") or 0),
    )

    # Get company name from database
    company_name = "Unknown Company"
    company_id = employee.get("company_id")
    if company_id:
        company_result = supabase.table("companies").select("company_name").eq("id", company_id).execute()
        if company_result.data:
            company_name = company_result.data[0].get("company_name", "Unknown Company")

    # Sick leave balance (from employee record)
    sick_balance_hours = float(employee.get("sick_balance") or 0) * 8

    return EmployeePaystubDetail(
        id=record["id"],
        payDate=run.get("pay_date", ""),
        payPeriodStart=run.get("period_start", ""),
        payPeriodEnd=run.get("period_end", ""),
        grossPay=float(record.get("total_gross") or 0),
        totalDeductions=float(record.get("total_deductions") or 0),
        netPay=float(record.get("net_pay") or 0),
        companyName=company_name,
        employeeName=f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        earnings=earnings,
        deductions=deductions,
        ytd=ytd,
        sickHoursTaken=sick_hours,
        sickPayPaid=sick_pay,
        sickBalanceHours=sick_balance_hours,
    )


@router.get(
    "/leave-balance",
    response_model=EmployeeLeaveBalanceResponse,
    summary="Get my leave balance",
    description="Get the current employee's vacation and sick leave balances.",
)
async def get_my_leave_balance(
    current_user: CurrentUser,
    year: int = 2025,
) -> EmployeeLeaveBalanceResponse:
    """Get detailed leave balance for the current employee."""
    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Get vacation config from employee
    vacation_config = employee.get("vacation_config") or {}
    vacation_rate = float(vacation_config.get("vacation_rate", 0.04))
    vacation_balance_dollars = float(employee.get("vacation_balance") or 0)

    # Calculate hourly rate - use actual rate or derive from salary
    hourly_rate = float(employee.get("hourly_rate") or 0)
    if hourly_rate == 0:
        # For salaried employees, calculate effective hourly rate
        hourly_rate = float(GrossCalculator.calculate_hourly_rate(employee))

    # Estimate vacation hours from dollars
    vacation_hours = vacation_balance_dollars / hourly_rate if hourly_rate > 0 else 0

    # Get sick leave balance and config
    sick_days_remaining = 0.0
    sick_days_allowance = 0.0

    try:
        from app.services.payroll.sick_leave_service import SickLeaveService

        service = SickLeaveService()
        province_code = employee.get("province_of_employment", "ON")

        # Get config for allowance
        config = service.get_config(province_code)
        if config:
            sick_days_allowance = float(config.paid_days_per_year)

        # Get balance
        hire_date = (
            date.fromisoformat(employee["hire_date"])
            if employee.get("hire_date")
            else date.today()
        )
        balance = service.create_new_year_balance(
            employee_id=employee["id"],
            year=year,
            province_code=province_code,
            hire_date=hire_date,
        )
        sick_days_remaining = float(balance.paid_days_remaining)
    except Exception:
        logger.exception("Error calculating sick leave balance")

    # Convert sick days to hours (8 hours per day)
    sick_hours_remaining = sick_days_remaining * 8
    sick_hours_allowance = sick_days_allowance * 8

    # Query vacation/sick pay usage from payroll records for history
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"

    records_result = (
        supabase.table("payroll_records")
        .select(
            """
            vacation_pay_paid,
            sick_pay_paid,
            sick_hours_taken,
            payroll_runs!inner (
                pay_date,
                period_start,
                period_end,
                status
            )
        """
        )
        .eq("employee_id", employee["id"])
        .in_("payroll_runs.status", ["approved", "paid"])
        .gte("payroll_runs.pay_date", year_start)
        .lte("payroll_runs.pay_date", year_end)
        .order("payroll_runs.pay_date", desc=True)
        .execute()
    )

    # Calculate YTD used (in hours)
    vacation_ytd_used_hours = 0.0
    sick_ytd_used_hours = 0.0
    leave_history: list[LeaveHistoryEntry] = []

    for record in records_result.data or []:
        run = record.get("payroll_runs", {})
        pay_date = run.get("pay_date", "")

        vacation_hours_taken = float(record.get("vacation_hours_taken") or 0)
        sick_hours_taken = float(record.get("sick_hours_taken") or 0)

        if vacation_hours_taken > 0:
            vacation_ytd_used_hours += vacation_hours_taken
            leave_history.append(
                LeaveHistoryEntry(
                    date=pay_date,
                    type="vacation",
                    hours=vacation_hours_taken,
                    balanceAfterHours=0,  # Would need running balance tracking
                    balanceAfterDollars=0,
                )
            )

        if sick_hours_taken > 0:
            sick_ytd_used_hours += sick_hours_taken
            leave_history.append(
                LeaveHistoryEntry(
                    date=pay_date,
                    type="sick",
                    hours=sick_hours_taken,
                    balanceAfterHours=0,
                )
            )

    # Calculate vacation YTD accrued from gross earnings (for this year only)
    year_end_next = f"{year + 1}-01-01"
    gross_result = (
        supabase.table("payroll_records")
        .select("gross_regular, gross_overtime, payroll_runs!inner(status, pay_date)")
        .eq("employee_id", employee["id"])
        .in_("payroll_runs.status", ["approved", "paid"])
        .gte("payroll_runs.pay_date", year_start)
        .lt("payroll_runs.pay_date", year_end_next)
        .execute()
    )

    total_gross = sum(
        float(r.get("gross_regular") or 0) + float(r.get("gross_overtime") or 0)
        for r in gross_result.data or []
    )
    # Calculate accrued in dollars, then convert to hours
    vacation_ytd_accrued_dollars = total_gross * vacation_rate
    vacation_ytd_accrued_hours = (
        vacation_ytd_accrued_dollars / hourly_rate if hourly_rate > 0 else 0
    )

    return EmployeeLeaveBalanceResponse(
        vacationHours=round(vacation_hours, 2),
        vacationDollars=round(vacation_balance_dollars, 2),
        vacationAccrualRate=vacation_rate * 100,  # Convert to percentage
        vacationYtdAccrued=round(vacation_ytd_accrued_hours, 2),
        vacationYtdUsed=round(vacation_ytd_used_hours, 2),
        sickHoursRemaining=round(sick_hours_remaining, 2),
        sickHoursAllowance=round(sick_hours_allowance, 2),
        sickHoursUsedThisYear=round(sick_ytd_used_hours, 2),
        leaveHistory=leave_history,
    )


# =============================================================================
# T4 Tax Documents
# =============================================================================


class TaxDocument(BaseModel):
    """Tax document available for download."""

    id: str
    type: str = "T4"
    year: int
    generatedAt: str
    downloadUrl: str = ""  # Not used, download via API


class T4ListResponse(BaseModel):
    """Response for T4 list endpoint."""

    taxDocuments: list[TaxDocument]


@router.get(
    "/t4",
    response_model=T4ListResponse,
    summary="Get my T4 documents",
    description="Get the current employee's T4 tax documents.",
)
async def get_my_t4_documents(current_user: CurrentUser) -> T4ListResponse:
    """Get T4 documents for the current employee."""
    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Query T4 slips for this employee
    result = (
        supabase.table("t4_slips")
        .select("id, tax_year, pdf_generated_at, status")
        .eq("employee_id", employee["id"])
        .in_("status", ["generated", "filed", "amended"])
        .order("tax_year", desc=True)
        .execute()
    )

    documents: list[TaxDocument] = []
    for row in result.data or []:
        if row.get("pdf_generated_at"):
            documents.append(
                TaxDocument(
                    id=row["id"],
                    type="T4",
                    year=row["tax_year"],
                    generatedAt=row["pdf_generated_at"],
                )
            )

    return T4ListResponse(taxDocuments=documents)


@router.get(
    "/t4/{tax_year}/download",
    summary="Download my T4 slip PDF",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file for download",
        }
    },
)
async def download_my_t4(
    tax_year: int,
    current_user: CurrentUser,
) -> Any:
    """Download T4 slip PDF for the current employee."""
    from fastapi.responses import Response

    from app.services.t4 import T4PDFGenerator, get_t4_storage

    employee = await get_employee_by_user_email(current_user)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Get the T4 slip for this employee and year
    result = (
        supabase.table("t4_slips")
        .select("id, pdf_storage_key, slip_data, status")
        .eq("employee_id", employee["id"])
        .eq("tax_year", tax_year)
        .in_("status", ["generated", "filed", "amended"])
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"T4 not found for tax year {tax_year}",
        )

    slip_record = result.data
    pdf_bytes: bytes | None = None

    # Try to get from storage first
    storage_key = slip_record.get("pdf_storage_key")
    if storage_key:
        try:
            storage = get_t4_storage()
            pdf_bytes = await storage.get_file_content(storage_key)
        except Exception:
            logger.warning(f"Failed to get T4 from storage: {storage_key}")

    # If no storage or failed, generate on-the-fly
    if not pdf_bytes:
        slip_data = slip_record.get("slip_data")
        if not slip_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="T4 data not available",
            )

        try:
            from app.models.t4 import T4SlipData

            slip = T4SlipData.model_validate(slip_data)
            pdf_generator = T4PDFGenerator()
            pdf_bytes = pdf_generator.generate_t4_slip_pdf(slip)
        except Exception as e:
            logger.error(f"Failed to generate T4 PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate T4 PDF",
            )

    employee_name = f"{employee.get('last_name', '')}_{employee.get('first_name', '')}"
    filename = f"T4_{tax_year}_{employee_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
