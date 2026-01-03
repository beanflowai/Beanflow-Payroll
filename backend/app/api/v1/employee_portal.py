"""
Employee Portal API Endpoints

Provides endpoints for employees to access their own payroll data.
Uses email matching to identify the current employee.

NOTE: Simple queries (profile, paystub list, t4 list) are handled via
direct Supabase access on the frontend. This API only handles:
- Complex calculations (YTD, leave balance)
- PDF generation (paystub, T4)
- Operations requiring business logic
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.core.config import get_config
from app.core.supabase_client import get_supabase_admin_client, get_supabase_client
from app.services.payroll.tax_tables import get_federal_config, get_province_config
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


class EmployeeAddress(BaseModel):
    """Employee address."""

    street: str
    city: str
    province: str
    postalCode: str


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    name: str
    relationship: str
    phone: str


class FullProfileResponse(BaseModel):
    """Full employee profile with decrypted SIN for self-service."""

    id: str
    firstName: str
    lastName: str
    email: str
    phone: str | None = None
    address: EmployeeAddress
    emergencyContact: EmergencyContact | None = None
    sin: str  # Decrypted SIN for employee to verify
    federalAdditionalClaims: float
    provincialAdditionalClaims: float
    bankName: str
    transitNumber: str
    institutionNumber: str
    accountNumber: str  # Masked
    hireDate: str
    jobTitle: str | None = None
    provinceOfEmployment: str


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


async def get_employee_by_user_email(
    current_user: CurrentUser,
    company_id: str | None = None,
) -> dict[str, Any] | None:
    """Find employee record matching the current user's email.

    Args:
        current_user: The authenticated user
        company_id: Optional company ID to scope the search. If provided, only
                   returns the employee record for that specific company.

    Returns:
        Employee record dict or None if not found
    """
    if not current_user.email:
        return None

    supabase = get_supabase_client()

    query = (
        supabase.table("employees")
        .select("*")
        .eq("email", current_user.email)
        .not_.is_("portal_invited_at", "null")  # Must have been invited
    )

    # If company_id is provided, scope to that company
    if company_id:
        query = query.eq("company_id", company_id)
    else:
        # If no company_id, prioritize the most recently invited company
        query = query.order("portal_invited_at", desc=True)

    result = query.limit(1).execute()

    if result.data:
        return cast(dict[str, Any], result.data[0])
    return None


# =============================================================================
# API Endpoints
# =============================================================================


# =============================================================================
# Public Company Lookup (No Auth Required)
# =============================================================================


class CompanyPublicInfo(BaseModel):
    """Public company information for portal login page."""

    id: str
    companyName: str
    slug: str
    logoUrl: str | None = None


@router.get(
    "/company/by-slug/{slug}",
    response_model=CompanyPublicInfo,
    summary="Get company info by slug",
    description="Public endpoint to get company information for portal login page.",
)
async def get_company_by_slug(slug: str) -> CompanyPublicInfo:
    """Get public company information by URL slug.

    This is a public endpoint (no auth required) used by the portal login page
    to display company name/logo before user authenticates.

    Uses public_company_portal_info view which has anon access granted,
    avoiding direct access to companies table which may have RLS restrictions.
    """
    from app.core.supabase_client import SupabaseClient

    # Use the base client (not authenticated) since this is a public endpoint
    # The view public_company_portal_info has GRANT SELECT to anon
    supabase = SupabaseClient.get_client()

    result = (
        supabase.table("public_company_portal_info")
        .select("id, company_name, slug, logo_url")
        .eq("slug", slug)
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company portal not found",
        )

    company = result.data
    return CompanyPublicInfo(
        id=company["id"],
        companyName=company["company_name"],
        slug=company["slug"],
        logoUrl=company.get("logo_url"),
    )


# NOTE: GET /paystubs list endpoint removed - use direct Supabase query:
# supabase.from('payroll_records').select('*, payroll_runs!inner(*)').eq('employee_id', empId)


@router.get(
    "/profile",
    response_model=FullProfileResponse,
    summary="Get my full profile",
    description="Get the current employee's full profile including decrypted SIN.",
)
async def get_my_profile(
    current_user: CurrentUser,
    company_id: str | None = None,
) -> FullProfileResponse:
    """Get the current employee's full profile with decrypted SIN.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
                   Required when employee has records in multiple companies.
    """
    from app.core.security import decrypt_sin

    employee = await get_employee_by_user_email(current_user, company_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Get tax claims for current year
    current_year = date.today().year
    tax_claims: dict[str, Any] = {}
    try:
        tax_claims_result = (
            supabase.table("employee_tax_claims")
            .select("federal_additional_claims, provincial_additional_claims")
            .eq("employee_id", employee["id"])
            .eq("tax_year", current_year)
            .maybe_single()
            .execute()
        )
        if tax_claims_result and tax_claims_result.data:
            tax_claims = tax_claims_result.data
    except Exception as e:
        logger.warning(f"Failed to fetch tax claims: {e}")

    # Decrypt SIN
    sin_encrypted = employee.get("sin_encrypted") or ""
    sin_decrypted = ""
    if sin_encrypted:
        try:
            decrypted = decrypt_sin(sin_encrypted)
            if decrypted:
                # Format as XXX-XXX-XXX
                clean_sin = decrypted.replace("-", "").replace(" ", "")
                if len(clean_sin) == 9:
                    sin_decrypted = f"{clean_sin[:3]}-{clean_sin[3:6]}-{clean_sin[6:]}"
                else:
                    sin_decrypted = decrypted
            else:
                # Decryption returned None/empty - show placeholder
                sin_decrypted = "***-***-*** (unavailable)"
                logger.warning(f"SIN decryption returned empty for employee {employee['id']}")
        except Exception as e:
            # Decryption failed - show placeholder
            sin_decrypted = "***-***-*** (unavailable)"
            logger.error(f"Failed to decrypt SIN for employee {employee['id']}: {e}")

    # Mask bank account number
    bank_account = employee.get("bank_account") or ""
    masked_account = "****" + bank_account[-4:] if len(bank_account) >= 4 else "****"

    # Build emergency contact if exists
    emergency_contact = None
    if employee.get("emergency_contact_name"):
        emergency_contact = EmergencyContact(
            name=employee.get("emergency_contact_name") or "",
            relationship=employee.get("emergency_contact_relationship") or "",
            phone=employee.get("emergency_contact_phone") or "",
        )

    return FullProfileResponse(
        id=employee["id"],
        firstName=employee.get("first_name") or "",
        lastName=employee.get("last_name") or "",
        email=employee.get("email") or "",
        phone=employee.get("phone"),
        address=EmployeeAddress(
            street=employee.get("address_street") or "",
            city=employee.get("address_city") or "",
            province=employee.get("address_province") or "",
            postalCode=employee.get("address_postal_code") or "",
        ),
        emergencyContact=emergency_contact,
        sin=sin_decrypted,
        federalAdditionalClaims=float(tax_claims.get("federal_additional_claims") or 0),
        provincialAdditionalClaims=float(tax_claims.get("provincial_additional_claims") or 0),
        bankName=employee.get("bank_name") or "",
        transitNumber=employee.get("bank_transit") or "",
        institutionNumber=employee.get("bank_institution") or "",
        accountNumber=masked_account,
        hireDate=employee.get("hire_date") or "",
        jobTitle=employee.get("job_title"),
        provinceOfEmployment=employee.get("province_of_employment") or "",
    )


@router.get(
    "/paystubs/{record_id}",
    response_model=EmployeePaystubDetail,
    summary="Get paystub detail",
    description="Get detailed paystub for a specific payroll record.",
)
async def get_paystub_detail(
    record_id: str,
    current_user: CurrentUser,
    company_id: str | None = None,
) -> EmployeePaystubDetail:
    """Get detailed paystub for a specific record.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
    """
    employee = await get_employee_by_user_email(current_user, company_id)

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
    company_id: str | None = None,
) -> EmployeeLeaveBalanceResponse:
    """Get detailed leave balance for the current employee.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
    """
    employee = await get_employee_by_user_email(current_user, company_id)

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
            vacation_hours_taken,
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
        .execute()
    )

    # Sort records by pay_date descending (PostgREST doesn't support ordering by nested fields)
    records_data = sorted(
        records_result.data or [],
        key=lambda r: r.get("payroll_runs", {}).get("pay_date", ""),
        reverse=True,
    )

    # Calculate YTD used (in hours)
    vacation_ytd_used_hours = 0.0
    sick_ytd_used_hours = 0.0
    leave_history: list[LeaveHistoryEntry] = []

    for record in records_data:
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


# =============================================================================
# Profile Change Request Models
# =============================================================================


class ProfileChangeRequestResponse(BaseModel):
    """Profile change request for employer review."""

    id: str
    employeeId: str
    employeeName: str
    changeType: str
    status: str
    currentValues: dict[str, Any]
    requestedValues: dict[str, Any]
    submittedAt: str
    attachments: list[str] | None = None
    reviewedAt: str | None = None
    reviewedBy: str | None = None
    rejectionReason: str | None = None


class ProfileChangeListResponse(BaseModel):
    """List of pending profile change requests."""

    items: list[ProfileChangeRequestResponse]
    total: int


class PersonalInfoUpdateRequest(BaseModel):
    """Request to update personal information (auto-approved)."""

    phone: str | None = None
    addressStreet: str | None = None
    addressCity: str | None = None
    addressProvince: str | None = None
    addressPostalCode: str | None = None
    emergencyName: str | None = None
    emergencyRelationship: str | None = None
    emergencyPhone: str | None = None


class PersonalInfoUpdateResponse(BaseModel):
    """Response for personal info update."""

    success: bool
    message: str


class TaxInfoChangeRequest(BaseModel):
    """Request to change tax information (requires approval)."""

    federalAdditionalClaims: float | None = None
    provincialAdditionalClaims: float | None = None


class PortalInviteRequest(BaseModel):
    """Request to invite employee to portal."""

    sendEmail: bool = True


class PortalInviteResponse(BaseModel):
    """Response for portal invitation."""

    success: bool
    message: str
    portalStatus: str


class ChangeRequestActionRequest(BaseModel):
    """Request to approve or reject a change request."""

    rejectionReason: str | None = None


# NOTE: GET /t4 list endpoint removed - use direct Supabase query:
# supabase.from('t4_slips').select('*').eq('employee_id', empId).in('status', ['generated', 'filed', 'amended'])


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
    company_id: str | None = None,
) -> Any:
    """Download T4 slip PDF for the current employee.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
    """
    from fastapi.responses import Response

    from app.services.t4 import T4PDFGenerator, get_t4_storage

    employee = await get_employee_by_user_email(current_user, company_id)

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


# =============================================================================
# Employee Self-Service Endpoints
# =============================================================================


@router.put(
    "/profile/personal",
    response_model=PersonalInfoUpdateResponse,
    summary="Update personal information",
    description="Update employee's personal info (auto-approved, no employer review needed).",
)
async def update_personal_info(
    request: PersonalInfoUpdateRequest,
    current_user: CurrentUser,
    company_id: str | None = None,
) -> PersonalInfoUpdateResponse:
    """Update employee's personal information directly.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
    """
    employee = await get_employee_by_user_email(current_user, company_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Build update data (only include non-None fields)
    update_data: dict[str, Any] = {}

    if request.phone is not None:
        update_data["phone"] = request.phone
    if request.addressStreet is not None:
        update_data["address_street"] = request.addressStreet
    if request.addressCity is not None:
        update_data["address_city"] = request.addressCity
    if request.addressProvince is not None:
        update_data["address_province"] = request.addressProvince
    if request.addressPostalCode is not None:
        update_data["address_postal_code"] = request.addressPostalCode
    if request.emergencyName is not None:
        update_data["emergency_contact_name"] = request.emergencyName
    if request.emergencyRelationship is not None:
        update_data["emergency_contact_relationship"] = request.emergencyRelationship
    if request.emergencyPhone is not None:
        update_data["emergency_contact_phone"] = request.emergencyPhone

    if not update_data:
        return PersonalInfoUpdateResponse(
            success=True,
            message="No changes to update",
        )

    try:
        supabase.table("employees").update(update_data).eq("id", employee["id"]).execute()
        return PersonalInfoUpdateResponse(
            success=True,
            message="Personal information updated successfully",
        )
    except Exception as e:
        logger.error(f"Failed to update personal info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update personal information",
        )


@router.put(
    "/profile/tax",
    response_model=ProfileChangeRequestResponse,
    summary="Submit tax info change request",
    description="Submit a tax information change request (requires employer approval).",
)
async def submit_tax_change_request(
    request: TaxInfoChangeRequest,
    current_user: CurrentUser,
    company_id: str | None = None,
) -> ProfileChangeRequestResponse:
    """Submit a tax info change request for employer approval.

    Args:
        company_id: Optional company ID to scope the request to a specific company.
    """
    employee = await get_employee_by_user_email(current_user, company_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No employee record found for email: {current_user.email}",
        )

    supabase = get_supabase_client()

    # Get current tax claims for this year
    current_year = date.today().year
    tax_claims_result = (
        supabase.table("employee_tax_claims")
        .select("*")
        .eq("employee_id", employee["id"])
        .eq("tax_year", current_year)
        .maybe_single()
        .execute()
    )

    current_values = {
        "federalAdditionalClaims": 0.0,
        "provincialAdditionalClaims": 0.0,
    }

    if tax_claims_result.data:
        current_values = {
            "federalAdditionalClaims": float(
                tax_claims_result.data.get("federal_additional_claims") or 0
            ),
            "provincialAdditionalClaims": float(
                tax_claims_result.data.get("provincial_additional_claims") or 0
            ),
        }

    requested_values = {
        "federalAdditionalClaims": request.federalAdditionalClaims
        if request.federalAdditionalClaims is not None
        else current_values["federalAdditionalClaims"],
        "provincialAdditionalClaims": request.provincialAdditionalClaims
        if request.provincialAdditionalClaims is not None
        else current_values["provincialAdditionalClaims"],
    }

    # Create change request
    change_request = {
        "employee_id": employee["id"],
        "company_id": employee.get("company_id"),
        "user_id": employee.get("user_id"),
        "change_type": "tax_info",
        "status": "pending",
        "current_values": current_values,
        "requested_values": requested_values,
    }

    try:
        result = supabase.table("profile_change_requests").insert(change_request).execute()
        created = result.data[0]

        return ProfileChangeRequestResponse(
            id=created["id"],
            employeeId=employee["id"],
            employeeName=f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            changeType="tax_info",
            status="pending",
            currentValues=current_values,
            requestedValues=requested_values,
            submittedAt=created.get("submitted_at", ""),
        )
    except Exception as e:
        logger.error(f"Failed to create change request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit change request",
        )


# =============================================================================
# Employer Management Endpoints
# =============================================================================

# Create a separate router for employer-side portal management
employer_router = APIRouter(tags=["Employee Portal Management"])


@employer_router.post(
    "/employees/{employee_id}/portal/invite",
    response_model=PortalInviteResponse,
    summary="Invite employee to portal",
    description="Send portal invitation to an employee.",
)
async def invite_to_portal(
    employee_id: str,
    request: PortalInviteRequest,
    current_user: CurrentUser,
) -> PortalInviteResponse:
    """Invite an employee to access the employee portal."""
    supabase = get_supabase_client()

    # Verify employee belongs to current user and get company info
    employee_result = (
        supabase.table("employees")
        .select("id, email, first_name, last_name, portal_status, user_id, company_id")
        .eq("id", employee_id)
        .eq("user_id", current_user.id)
        .maybe_single()
        .execute()
    )

    if not employee_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    employee = employee_result.data

    # Get company slug for portal URL
    company_slug = "default"
    company_id = employee.get("company_id")
    if company_id:
        company_result = (
            supabase.table("companies")
            .select("slug")
            .eq("id", company_id)
            .maybe_single()
            .execute()
        )
        if company_result.data:
            company_slug = company_result.data.get("slug") or "default"

    # Check if already active
    if employee.get("portal_status") == "active":
        return PortalInviteResponse(
            success=True,
            message="Employee already has active portal access",
            portalStatus="active",
        )

    # Create/invite Auth user if sendEmail is True
    if request.sendEmail:
        admin_client = get_supabase_admin_client()
        if not admin_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin client not configured. Please set SUPABASE_SERVICE_ROLE_KEY.",
            )

        # Get frontend URL for redirect with company slug
        config = get_config()
        employee_portal_url = f"{config.frontend_url}/employee/{company_slug}/auth"

        try:
            # Try to invite new user by email - creates Auth user and sends invitation
            admin_client.auth.admin.invite_user_by_email(
                employee["email"],
                options={"redirect_to": employee_portal_url},
            )
            logger.info(f"Auth user invited: {employee['email']} with redirect to {employee_portal_url}")
        except Exception as invite_error:
            # Check if user already exists (common case)
            error_msg = str(invite_error).lower()
            if "already" in error_msg or "exists" in error_msg or "registered" in error_msg:
                logger.info(f"Auth user already exists for: {employee['email']}, sending custom invite email")
                # User exists - send custom invite email via Resend (only login link, no OTP)
                try:
                    from app.services.email_service import get_email_service

                    email_service = get_email_service()
                    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
                    await email_service.send_employee_portal_invite_email(
                        to_email=employee["email"],
                        employee_name=employee_name or "Employee",
                        company_slug=company_slug,
                    )
                    logger.info(f"Custom invite email sent to: {employee['email']}")
                except Exception as email_error:
                    logger.error(f"Failed to send custom invite email: {email_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to send invitation email: {email_error}",
                    )
            else:
                logger.error(f"Failed to invite auth user: {invite_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send invitation email: {invite_error}",
                )

    # Update portal status
    update_data = {
        "portal_status": "invited",
        "portal_invited_at": datetime.now().isoformat(),
    }

    try:
        supabase.table("employees").update(update_data).eq("id", employee_id).execute()

        message = "Portal invitation sent" if request.sendEmail else "Portal status updated to invited"

        return PortalInviteResponse(
            success=True,
            message=message,
            portalStatus="invited",
        )
    except Exception as e:
        logger.error(f"Failed to update portal status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite employee to portal",
        )


@employer_router.get(
    "/profile-changes",
    response_model=ProfileChangeListResponse,
    summary="Get pending profile changes",
    description="Get all pending profile change requests for employer review.",
)
async def get_pending_profile_changes(
    current_user: CurrentUser,
    status: str = "pending",
) -> ProfileChangeListResponse:
    """Get pending profile change requests for employer review."""
    supabase = get_supabase_client()

    query = (
        supabase.table("profile_change_requests")
        .select(
            """
            *,
            employees!inner (
                first_name,
                last_name
            )
        """
        )
        .eq("user_id", current_user.id)
    )

    if status:
        query = query.eq("status", status)

    result = query.order("submitted_at", desc=True).execute()

    items: list[ProfileChangeRequestResponse] = []
    for row in result.data or []:
        emp = row.get("employees", {})
        items.append(
            ProfileChangeRequestResponse(
                id=row["id"],
                employeeId=row["employee_id"],
                employeeName=f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                changeType=row["change_type"],
                status=row["status"],
                currentValues=row.get("current_values") or {},
                requestedValues=row.get("requested_values") or {},
                submittedAt=row.get("submitted_at", ""),
                attachments=row.get("attachments"),
                reviewedAt=row.get("reviewed_at"),
                reviewedBy=row.get("reviewed_by"),
                rejectionReason=row.get("rejection_reason"),
            )
        )

    return ProfileChangeListResponse(items=items, total=len(items))


@employer_router.put(
    "/profile-changes/{change_id}/approve",
    response_model=ProfileChangeRequestResponse,
    summary="Approve profile change",
    description="Approve a profile change request and apply changes.",
)
async def approve_profile_change(
    change_id: str,
    current_user: CurrentUser,
) -> ProfileChangeRequestResponse:
    """Approve a profile change request and apply changes to employee record."""
    supabase = get_supabase_client()

    # Get the change request
    result = (
        supabase.table("profile_change_requests")
        .select(
            """
            *,
            employees!inner (
                first_name,
                last_name
            )
        """
        )
        .eq("id", change_id)
        .eq("user_id", current_user.id)
        .eq("status", "pending")
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found or already processed",
        )

    change_request = result.data
    employee = change_request.get("employees", {})
    requested_values = change_request.get("requested_values") or {}

    try:
        # Apply changes based on change type
        if change_request["change_type"] == "tax_info":
            # Update employee_tax_claims table
            current_year = date.today().year

            # Get employee's province for BPA lookup
            employee_data = (
                supabase.table("employees")
                .select("province_of_employment")
                .eq("id", change_request["employee_id"])
                .single()
                .execute()
            )
            province = employee_data.data.get("province_of_employment", "ON")

            # Get BPA values from tax configuration
            try:
                federal_config = get_federal_config(current_year, None)
                province_config = get_province_config(province, current_year, None)
                federal_bpa = float(federal_config["bpaf"])
                provincial_bpa = float(province_config["bpa"])
            except Exception as bpa_error:
                logger.warning(f"Failed to get BPA from tax config: {bpa_error}, using fallback")
                # Fallback to default values if tax config not available
                federal_bpa = 16129.0  # 2025 federal BPA
                provincial_bpa = 12000.0  # Conservative default

            tax_update = {
                "federal_bpa": federal_bpa,
                "provincial_bpa": provincial_bpa,
                "federal_additional_claims": requested_values.get("federalAdditionalClaims", 0),
                "provincial_additional_claims": requested_values.get(
                    "provincialAdditionalClaims", 0
                ),
            }

            # Upsert tax claims
            supabase.table("employee_tax_claims").upsert(
                {
                    "employee_id": change_request["employee_id"],
                    "company_id": change_request["company_id"],
                    "user_id": current_user.id,
                    "tax_year": current_year,
                    **tax_update,
                },
                on_conflict="employee_id,tax_year",
            ).execute()

        # Mark change request as approved
        supabase.table("profile_change_requests").update(
            {
                "status": "approved",
                "reviewed_at": datetime.now().isoformat(),
                "reviewed_by": current_user.id,
            }
        ).eq("id", change_id).execute()

        return ProfileChangeRequestResponse(
            id=change_request["id"],
            employeeId=change_request["employee_id"],
            employeeName=f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            changeType=change_request["change_type"],
            status="approved",
            currentValues=change_request.get("current_values") or {},
            requestedValues=requested_values,
            submittedAt=change_request.get("submitted_at", ""),
            reviewedAt=datetime.now().isoformat(),
            reviewedBy=current_user.id,
        )
    except Exception as e:
        logger.error(f"Failed to approve change request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve change request",
        )


@employer_router.put(
    "/profile-changes/{change_id}/reject",
    response_model=ProfileChangeRequestResponse,
    summary="Reject profile change",
    description="Reject a profile change request with reason.",
)
async def reject_profile_change(
    change_id: str,
    request: ChangeRequestActionRequest,
    current_user: CurrentUser,
) -> ProfileChangeRequestResponse:
    """Reject a profile change request."""
    supabase = get_supabase_client()

    # Get the change request
    result = (
        supabase.table("profile_change_requests")
        .select(
            """
            *,
            employees!inner (
                first_name,
                last_name
            )
        """
        )
        .eq("id", change_id)
        .eq("user_id", current_user.id)
        .eq("status", "pending")
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found or already processed",
        )

    change_request = result.data
    employee = change_request.get("employees", {})

    try:
        supabase.table("profile_change_requests").update(
            {
                "status": "rejected",
                "reviewed_at": datetime.now().isoformat(),
                "reviewed_by": current_user.id,
                "rejection_reason": request.rejectionReason,
            }
        ).eq("id", change_id).execute()

        return ProfileChangeRequestResponse(
            id=change_request["id"],
            employeeId=change_request["employee_id"],
            employeeName=f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            changeType=change_request["change_type"],
            status="rejected",
            currentValues=change_request.get("current_values") or {},
            requestedValues=change_request.get("requested_values") or {},
            submittedAt=change_request.get("submitted_at", ""),
            reviewedAt=datetime.now().isoformat(),
            reviewedBy=current_user.id,
            rejectionReason=request.rejectionReason,
        )
    except Exception as e:
        logger.error(f"Failed to reject change request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject change request",
        )
