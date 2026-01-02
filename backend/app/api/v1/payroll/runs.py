"""
Payroll Run Management API Endpoints

Provides endpoints for managing payroll runs (draft state editing, finalization, approval).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.services.payroll_run_service import get_payroll_run_service

from ._helpers import get_user_company_id
from ._models import (
    AddEmployeeRequest,
    AddEmployeeResponse,
    ApprovePayrollRunResponse,
    CreateOrGetRunRequest,
    CreateOrGetRunResponse,
    DeleteRunResponse,
    ListPayrollRunsResponse,
    PayrollRecordResponse,
    PayrollRunResponse,
    RemoveEmployeeResponse,
    SyncEmployeesResponse,
    UpdatePayrollRecordRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/runs",
    response_model=ListPayrollRunsResponse,
    summary="List payroll runs",
    description="List payroll runs with optional filtering and pagination.",
)
async def list_payroll_runs(
    current_user: CurrentUser,
    run_status: str | None = Query(None, alias="run_status", description="Filter by status"),
    exclude_status: str | None = Query(None, description="Exclude runs with this status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> ListPayrollRunsResponse:
    """
    List payroll runs for the current user's company.

    Supports filtering by status and pagination.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.list_runs(
            run_status=run_status,
            exclude_status=exclude_status,
            limit=limit,
            offset=offset,
        )

        runs = []
        for run_data in result["runs"]:
            runs.append(PayrollRunResponse(
                id=run_data["id"],
                pay_date=run_data["pay_date"],
                status=run_data["status"],
                total_employees=run_data.get("total_employees", 0),
                total_gross=float(run_data.get("total_gross", 0)),
                total_cpp_employee=float(run_data.get("total_cpp_employee", 0)),
                total_cpp_employer=float(run_data.get("total_cpp_employer", 0)),
                total_ei_employee=float(run_data.get("total_ei_employee", 0)),
                total_ei_employer=float(run_data.get("total_ei_employer", 0)),
                total_federal_tax=float(run_data.get("total_federal_tax", 0)),
                total_provincial_tax=float(run_data.get("total_provincial_tax", 0)),
                total_net_pay=float(run_data.get("total_net_pay", 0)),
                total_employer_cost=float(run_data.get("total_employer_cost", 0)),
            ))

        return ListPayrollRunsResponse(runs=runs, total=result["total"])

    except ValueError as e:
        logger.error(f"List runs error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error listing payroll runs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error listing payroll runs",
        )


@router.patch(
    "/runs/{run_id}/records/{record_id}",
    response_model=PayrollRecordResponse,
    summary="Update a payroll record",
    description="Update input data for a payroll record in draft status.",
)
async def update_payroll_record(
    run_id: UUID,
    record_id: UUID,
    request: UpdatePayrollRecordRequest,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> PayrollRecordResponse:
    """
    Update a payroll record's input data while in draft status.

    This allows editing:
    - Regular hours (hourly employees only)
    - Overtime hours
    - Leave entries (vacation, sick)
    - Holiday work entries
    - One-time adjustments (bonus, deduction, reimbursement)
    - Manual override values

    The record will be marked as modified, requiring recalculation.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)

        # Build input_data from request
        input_data: dict[str, Any] = {}
        if request.regularHours is not None:
            input_data["regularHours"] = request.regularHours
        if request.overtimeHours is not None:
            input_data["overtimeHours"] = request.overtimeHours
        if request.leaveEntries is not None:
            input_data["leaveEntries"] = [
                {"type": e.type, "hours": e.hours} for e in request.leaveEntries
            ]
        if request.holidayWorkEntries is not None:
            input_data["holidayWorkEntries"] = [
                {
                    "holidayDate": e.holidayDate,
                    "holidayName": e.holidayName,
                    "hoursWorked": e.hoursWorked,
                }
                for e in request.holidayWorkEntries
            ]
        if request.adjustments is not None:
            input_data["adjustments"] = [
                {
                    "type": a.type,
                    "amount": a.amount,
                    "description": a.description,
                    "taxable": a.taxable,
                }
                for a in request.adjustments
            ]
        if request.overrides is not None:
            input_data["overrides"] = {
                "regularPay": request.overrides.regularPay,
                "overtimePay": request.overrides.overtimePay,
                "holidayPay": request.overrides.holidayPay,
            }
        if request.holidayPayExempt is not None:
            input_data["holidayPayExempt"] = request.holidayPayExempt

        result = await service.update_record(run_id, record_id, input_data)

        return PayrollRecordResponse(
            id=result["id"],
            employee_id=result["employee_id"],
            input_data=result.get("input_data"),
            is_modified=result.get("is_modified", False),
        )

    except ValueError as e:
        logger.error(f"Update record error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error updating payroll record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error updating payroll record",
        )


@router.post(
    "/runs/{run_id}/recalculate",
    response_model=PayrollRunResponse,
    summary="Recalculate payroll run",
    description="Recalculate all records in a draft payroll run.",
)
async def recalculate_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> PayrollRunResponse:
    """
    Recalculate all payroll deductions for a draft run.

    This:
    1. Reads input_data from all payroll_records
    2. Recalculates CPP, EI, federal tax, and provincial tax
    3. Updates all payroll_records with new values
    4. Updates payroll_runs summary totals
    5. Clears all is_modified flags

    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.recalculate_run(run_id)

        return PayrollRunResponse(
            id=result["id"],
            pay_date=result["pay_date"],
            status=result["status"],
            total_employees=result.get("total_employees", 0),
            total_gross=float(result.get("total_gross", 0)),
            total_cpp_employee=float(result.get("total_cpp_employee", 0)),
            total_cpp_employer=float(result.get("total_cpp_employer", 0)),
            total_ei_employee=float(result.get("total_ei_employee", 0)),
            total_ei_employer=float(result.get("total_ei_employer", 0)),
            total_federal_tax=float(result.get("total_federal_tax", 0)),
            total_provincial_tax=float(result.get("total_provincial_tax", 0)),
            total_net_pay=float(result.get("total_net_pay", 0)),
            total_employer_cost=float(result.get("total_employer_cost", 0)),
        )

    except ValueError as e:
        logger.error(f"Recalculate error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error recalculating payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error recalculating payroll run",
        )


@router.post(
    "/runs/{run_id}/sync-employees",
    response_model=SyncEmployeesResponse,
    summary="Sync new employees to draft payroll run",
    description="Add any new employees from pay groups to an existing draft payroll run.",
)
async def sync_employees(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> SyncEmployeesResponse:
    """
    Sync new employees to a draft payroll run.

    When employees are added to pay groups after a payroll run is created,
    this endpoint will:
    1. Find pay groups for the run's pay_date
    2. Get active employees from those pay groups
    3. Create payroll_records for any employees not yet in the run
    4. Update the run's total_employees count

    Only works on runs in 'draft' status. Non-draft runs return empty result.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.sync_employees(run_id)

        run_data = result["run"]
        return SyncEmployeesResponse(
            added_count=result["added_count"],
            added_employees=result["added_employees"],
            run=PayrollRunResponse(
                id=run_data["id"],
                pay_date=run_data["pay_date"],
                status=run_data["status"],
                total_employees=run_data.get("total_employees", 0),
                total_gross=float(run_data.get("total_gross", 0)),
                total_cpp_employee=float(run_data.get("total_cpp_employee", 0)),
                total_cpp_employer=float(run_data.get("total_cpp_employer", 0)),
                total_ei_employee=float(run_data.get("total_ei_employee", 0)),
                total_ei_employer=float(run_data.get("total_ei_employer", 0)),
                total_federal_tax=float(run_data.get("total_federal_tax", 0)),
                total_provincial_tax=float(run_data.get("total_provincial_tax", 0)),
                total_net_pay=float(run_data.get("total_net_pay", 0)),
                total_employer_cost=float(run_data.get("total_employer_cost", 0)),
            ),
        )

    except ValueError as e:
        logger.error(f"Sync employees error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error syncing employees")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error syncing employees",
        )


@router.post(
    "/runs/create-or-get",
    response_model=CreateOrGetRunResponse,
    summary="Create or get a draft payroll run",
    description="Create a new draft payroll run or return existing one for a period end.",
)
async def create_or_get_run(
    request: CreateOrGetRunRequest,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> CreateOrGetRunResponse:
    """
    Create a new draft payroll run or get existing one for a period end.

    This endpoint:
    1. Checks if a payroll run already exists for this period end
    2. If exists, returns the existing run
    3. If not, creates a new draft run with payroll records for all eligible employees

    The run is automatically populated with employees from pay groups that have
    this date as their next_period_end.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.create_or_get_run_by_period_end(request.periodEnd)

        run_data = result["run"]
        return CreateOrGetRunResponse(
            run=PayrollRunResponse(
                id=run_data["id"],
                pay_date=run_data["pay_date"],
                status=run_data["status"],
                total_employees=run_data.get("total_employees", 0),
                total_gross=float(run_data.get("total_gross", 0)),
                total_cpp_employee=float(run_data.get("total_cpp_employee", 0)),
                total_cpp_employer=float(run_data.get("total_cpp_employer", 0)),
                total_ei_employee=float(run_data.get("total_ei_employee", 0)),
                total_ei_employer=float(run_data.get("total_ei_employer", 0)),
                total_federal_tax=float(run_data.get("total_federal_tax", 0)),
                total_provincial_tax=float(run_data.get("total_provincial_tax", 0)),
                total_net_pay=float(run_data.get("total_net_pay", 0)),
                total_employer_cost=float(run_data.get("total_employer_cost", 0)),
            ),
            created=result["created"],
            records_count=result["records_count"],
        )

    except ValueError as e:
        logger.error(f"Create or get run error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error creating/getting payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating/getting payroll run",
        )


@router.post(
    "/runs/{run_id}/employees",
    response_model=AddEmployeeResponse,
    summary="Add an employee to a draft payroll run",
    description="Add a single employee to a draft payroll run.",
)
async def add_employee_to_run(
    run_id: UUID,
    request: AddEmployeeRequest,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> AddEmployeeResponse:
    """
    Add an employee to a draft payroll run.

    This creates a payroll record for the employee in the run.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.add_employee_to_run(run_id, request.employeeId)

        return AddEmployeeResponse(
            employee_id=result["employee_id"],
            employee_name=result["employee_name"],
        )

    except ValueError as e:
        logger.error(f"Add employee error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error adding employee to payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error adding employee to payroll run",
        )


@router.delete(
    "/runs/{run_id}/employees/{employee_id}",
    response_model=RemoveEmployeeResponse,
    summary="Remove an employee from a draft payroll run",
    description="Remove a single employee from a draft payroll run.",
)
async def remove_employee_from_run(
    run_id: UUID,
    employee_id: str,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> RemoveEmployeeResponse:
    """
    Remove an employee from a draft payroll run.

    This deletes the payroll record for the employee.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.remove_employee_from_run(run_id, employee_id)

        return RemoveEmployeeResponse(
            removed=result["removed"],
            employee_id=result["employee_id"],
        )

    except ValueError as e:
        logger.error(f"Remove employee error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error removing employee from payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error removing employee from payroll run",
        )


@router.delete(
    "/runs/{run_id}",
    response_model=DeleteRunResponse,
    summary="Delete a draft payroll run",
    description="Delete a draft payroll run and all its records.",
)
async def delete_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> DeleteRunResponse:
    """
    Delete a draft payroll run.

    This permanently deletes the run and all associated payroll records.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.delete_run(run_id)

        return DeleteRunResponse(
            deleted=result["deleted"],
            run_id=result["run_id"],
        )

    except ValueError as e:
        logger.error(f"Delete run error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error deleting payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error deleting payroll run",
        )


@router.post(
    "/runs/{run_id}/finalize",
    response_model=PayrollRunResponse,
    summary="Finalize payroll run",
    description="Transition payroll run from draft to pending_approval.",
)
async def finalize_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> PayrollRunResponse:
    """
    Finalize a draft payroll run.

    This transitions the run from 'draft' to 'pending_approval' status.
    After finalization, the run becomes read-only.

    Prerequisites:
    - Run must be in 'draft' status
    - No records can have is_modified = True (must recalculate first)
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.finalize_run(run_id)

        return PayrollRunResponse(
            id=result["id"],
            pay_date=result["pay_date"],
            status=result["status"],
            total_employees=result.get("total_employees", 0),
            total_gross=float(result.get("total_gross", 0)),
            total_cpp_employee=float(result.get("total_cpp_employee", 0)),
            total_cpp_employer=float(result.get("total_cpp_employer", 0)),
            total_ei_employee=float(result.get("total_ei_employee", 0)),
            total_ei_employer=float(result.get("total_ei_employer", 0)),
            total_federal_tax=float(result.get("total_federal_tax", 0)),
            total_provincial_tax=float(result.get("total_provincial_tax", 0)),
            total_net_pay=float(result.get("total_net_pay", 0)),
            total_employer_cost=float(result.get("total_employer_cost", 0)),
        )

    except ValueError as e:
        logger.error(f"Finalize error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error finalizing payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error finalizing payroll run",
        )


@router.post(
    "/runs/{run_id}/approve",
    response_model=ApprovePayrollRunResponse,
    summary="Approve payroll run",
    description="Approve a pending_approval payroll run, generate paystubs, and advance next_pay_date.",
)
async def approve_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> ApprovePayrollRunResponse:
    """
    Approve a pending_approval payroll run.

    This:
    1. Verifies run is in pending_approval status
    2. Generates paystub PDFs for all records
    3. Updates status to approved
    4. Advances next_pay_date for all affected pay groups

    Prerequisites:
    - Run must be in 'pending_approval' status
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.approve_run(run_id, approved_by=current_user.id)

        return ApprovePayrollRunResponse(
            id=result["id"],
            payDate=result["pay_date"],
            status=result["status"],
            totalEmployees=result.get("total_employees", 0),
            totalGross=float(result.get("total_gross", 0)),
            totalNetPay=float(result.get("total_net_pay", 0)),
            paystubsGenerated=result.get("paystubs_generated", 0),
            paystubErrors=result.get("paystub_errors"),
        )

    except ValueError as e:
        logger.error(f"Approve error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error approving payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error approving payroll run",
        )
