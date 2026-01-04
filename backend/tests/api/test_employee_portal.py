"""
Tests for Employee Portal API Endpoints.

Tests the employee portal API endpoints for accessing employee payroll data.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.employee_portal import (
    ChangeRequestActionRequest,
    CompanyPublicInfo,
    EmergencyContact,
    EmployeeAddress,
    EmployeeLeaveBalanceResponse,
    EmployeePaystubDetail,
    FullProfileResponse,
    LeaveHistoryEntry,
    PaystubDeduction,
    PaystubEarning,
    PaystubYTD,
    PersonalInfoUpdateRequest,
    PersonalInfoUpdateResponse,
    PortalInviteRequest,
    PortalInviteResponse,
    ProfileChangeListResponse,
    ProfileChangeRequestResponse,
    TaxInfoChangeRequest,
    get_employee_by_user_email,
)


class MockCurrentUser:
    """Mock current user for testing."""

    def __init__(self, user_id: str = "user-123", email: str = "test@example.com"):
        self.id = user_id
        self.email = email


# =============================================================================
# Response Model Tests
# =============================================================================


class TestPaystubEarning:
    """Tests for PaystubEarning model."""

    def test_creates_with_hours(self):
        """Test creation with hours."""
        earning = PaystubEarning(type="Regular Pay", hours=80.0, amount=3200.0)
        assert earning.type == "Regular Pay"
        assert earning.hours == 80.0
        assert earning.amount == 3200.0

    def test_creates_without_hours(self):
        """Test creation without hours."""
        earning = PaystubEarning(type="Vacation Pay", amount=500.0)
        assert earning.type == "Vacation Pay"
        assert earning.hours is None
        assert earning.amount == 500.0


class TestPaystubDeduction:
    """Tests for PaystubDeduction model."""

    def test_creates_deduction(self):
        """Test creation of deduction."""
        deduction = PaystubDeduction(type="CPP", amount=150.0)
        assert deduction.type == "CPP"
        assert deduction.amount == 150.0


class TestPaystubYTD:
    """Tests for PaystubYTD model."""

    def test_creates_ytd(self):
        """Test creation of YTD summary."""
        ytd = PaystubYTD(
            grossEarnings=50000.0,
            cppPaid=2500.0,
            eiPaid=1200.0,
            taxPaid=10000.0,
        )
        assert ytd.grossEarnings == 50000.0
        assert ytd.cppPaid == 2500.0
        assert ytd.eiPaid == 1200.0
        assert ytd.taxPaid == 10000.0


class TestEmployeeAddress:
    """Tests for EmployeeAddress model."""

    def test_creates_address(self):
        """Test creation of address."""
        address = EmployeeAddress(
            street="123 Main St",
            city="Toronto",
            province="ON",
            postalCode="M5V 2H1",
        )
        assert address.street == "123 Main St"
        assert address.city == "Toronto"
        assert address.province == "ON"
        assert address.postalCode == "M5V 2H1"


class TestEmergencyContact:
    """Tests for EmergencyContact model."""

    def test_creates_emergency_contact(self):
        """Test creation of emergency contact."""
        contact = EmergencyContact(
            name="Jane Doe",
            relationship="Spouse",
            phone="416-555-0123",
        )
        assert contact.name == "Jane Doe"
        assert contact.relationship == "Spouse"
        assert contact.phone == "416-555-0123"


class TestLeaveHistoryEntry:
    """Tests for LeaveHistoryEntry model."""

    def test_creates_vacation_entry(self):
        """Test creation of vacation leave entry."""
        entry = LeaveHistoryEntry(
            date="2025-01-15",
            type="vacation",
            hours=8.0,
            balanceAfterHours=72.0,
            balanceAfterDollars=2880.0,
        )
        assert entry.type == "vacation"
        assert entry.hours == 8.0
        assert entry.balanceAfterHours == 72.0

    def test_creates_sick_entry(self):
        """Test creation of sick leave entry."""
        entry = LeaveHistoryEntry(
            date="2025-01-10",
            type="sick",
            hours=8.0,
            balanceAfterHours=32.0,
        )
        assert entry.type == "sick"


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestGetEmployeeByUserEmail:
    """Tests for get_employee_by_user_email helper."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_email(self):
        """Test returns None when user has no email."""
        user = MockCurrentUser(email=None)
        result = await get_employee_by_user_email(user)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_empty_email(self):
        """Test returns None when user has empty email."""
        user = MockCurrentUser(email="")
        result = await get_employee_by_user_email(user)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_employee_by_email(self):
        """Test returns employee record matching email."""
        user = MockCurrentUser(email="john@example.com")

        # Build the mock chain properly
        mock_execute = MagicMock()
        mock_execute.data = [{"id": "emp-123", "email": "john@example.com"}]

        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_execute

        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit

        mock_is_ = MagicMock()
        mock_is_.order.return_value = mock_order

        mock_not_ = MagicMock()
        mock_not_.is_.return_value = mock_is_

        mock_eq = MagicMock()
        mock_eq.not_ = mock_not_

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await get_employee_by_user_email(user)

        assert result is not None
        assert result["id"] == "emp-123"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Test returns None when no employee found."""
        user = MockCurrentUser(email="unknown@example.com")

        # Build the mock chain properly
        mock_execute = MagicMock()
        mock_execute.data = []

        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_execute

        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit

        mock_is_ = MagicMock()
        mock_is_.order.return_value = mock_order

        mock_not_ = MagicMock()
        mock_not_.is_.return_value = mock_is_

        mock_eq = MagicMock()
        mock_eq.not_ = mock_not_

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await get_employee_by_user_email(user)

        assert result is None

    @pytest.mark.asyncio
    async def test_scopes_by_company_id(self):
        """Test scopes query by company_id when provided."""
        user = MockCurrentUser(email="john@example.com")

        # Build the mock chain properly for company_id case
        mock_execute = MagicMock()
        mock_execute.data = [{"id": "emp-123", "email": "john@example.com"}]

        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_execute

        mock_eq_company = MagicMock()
        mock_eq_company.limit.return_value = mock_limit

        mock_is_ = MagicMock()
        mock_is_.eq.return_value = mock_eq_company

        mock_not_ = MagicMock()
        mock_not_.is_.return_value = mock_is_

        mock_eq = MagicMock()
        mock_eq.not_ = mock_not_

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await get_employee_by_user_email(user, company_id="comp-123")

        # Verify eq was called with company_id
        mock_is_.eq.assert_called_once_with("company_id", "comp-123")
        assert result is not None


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestGetCompanyBySlug:
    """Tests for get_company_by_slug endpoint."""

    @pytest.mark.asyncio
    async def test_returns_company_info(self):
        """Test returns company info by slug."""
        from app.api.v1.employee_portal import get_company_by_slug

        # Build proper mock chain
        mock_execute = MagicMock()
        mock_execute.data = {
            "id": "comp-123",
            "company_name": "Acme Corp",
            "slug": "acme",
            "logo_url": "https://example.com/logo.png",
        }

        mock_maybe_single = MagicMock()
        mock_maybe_single.execute.return_value = mock_execute

        mock_eq = MagicMock()
        mock_eq.maybe_single.return_value = mock_maybe_single

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with patch(
            "app.core.supabase_client.SupabaseClient.get_client",
            return_value=mock_supabase,
        ):
            result = await get_company_by_slug("acme")

        assert result.id == "comp-123"
        assert result.companyName == "Acme Corp"
        assert result.slug == "acme"
        assert result.logoUrl == "https://example.com/logo.png"

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        """Test raises 404 when company not found."""
        from app.api.v1.employee_portal import get_company_by_slug

        # Build proper mock chain
        mock_execute = MagicMock()
        mock_execute.data = None

        mock_maybe_single = MagicMock()
        mock_maybe_single.execute.return_value = mock_execute

        mock_eq = MagicMock()
        mock_eq.maybe_single.return_value = mock_maybe_single

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with patch(
            "app.core.supabase_client.SupabaseClient.get_client",
            return_value=mock_supabase,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_company_by_slug("nonexistent")

        assert exc_info.value.status_code == 404
        assert "Company portal not found" in str(exc_info.value.detail)


class TestGetMyProfile:
    """Tests for get_my_profile endpoint."""

    @pytest.fixture
    def mock_employee(self) -> dict[str, Any]:
        """Create a mock employee record."""
        return {
            "id": "emp-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "416-555-0123",
            "address_street": "123 Main St",
            "address_city": "Toronto",
            "address_province": "ON",
            "address_postal_code": "M5V 2H1",
            "sin_encrypted": "encrypted_sin_value",
            "bank_name": "Royal Bank",
            "bank_transit": "12345",
            "bank_institution": "003",
            "bank_account": "12345678",
            "hire_date": "2024-01-15",
            "job_title": "Developer",
            "province_of_employment": "ON",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_phone": "416-555-9999",
            "company_id": "comp-123",
        }

    @pytest.mark.asyncio
    async def test_raises_404_when_no_employee(self):
        """Test raises 404 when no employee found."""
        from app.api.v1.employee_portal import get_my_profile

        user = MockCurrentUser()

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_my_profile(user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_full_profile(self, mock_employee):
        """Test returns full profile response."""
        from app.api.v1.employee_portal import get_my_profile

        user = MockCurrentUser()

        # Build proper mock chain for tax claims query
        mock_tax_execute = MagicMock()
        mock_tax_execute.data = {
            "federal_additional_claims": 1000.0,
            "provincial_additional_claims": 500.0,
        }

        mock_maybe_single = MagicMock()
        mock_maybe_single.execute.return_value = mock_tax_execute

        mock_eq2 = MagicMock()
        mock_eq2.maybe_single.return_value = mock_maybe_single

        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1

        mock_table = MagicMock()
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
            patch(
                "app.core.security.decrypt_sin",
                return_value="123456789",
            ),
        ):
            result = await get_my_profile(user)

        assert result.id == "emp-123"
        assert result.firstName == "John"
        assert result.lastName == "Doe"
        assert result.sin == "123-456-789"
        assert result.accountNumber == "****5678"
        assert result.emergencyContact is not None
        assert result.emergencyContact.name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_handles_missing_sin(self, mock_employee):
        """Test handles missing SIN gracefully."""
        from app.api.v1.employee_portal import get_my_profile

        user = MockCurrentUser()
        mock_employee["sin_encrypted"] = ""

        mock_supabase = MagicMock()
        mock_tax_claims_result = MagicMock()
        mock_tax_claims_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_tax_claims_result

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            result = await get_my_profile(user)

        assert result.sin == ""

    @pytest.mark.asyncio
    async def test_handles_sin_decryption_failure(self, mock_employee):
        """Test handles SIN decryption failure."""
        from app.api.v1.employee_portal import get_my_profile

        user = MockCurrentUser()

        mock_supabase = MagicMock()
        mock_tax_claims_result = MagicMock()
        mock_tax_claims_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_tax_claims_result

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
            patch(
                "app.core.security.decrypt_sin",
                side_effect=Exception("Decryption error"),
            ),
        ):
            result = await get_my_profile(user)

        assert "unavailable" in result.sin


class TestGetPaystubDetail:
    """Tests for get_paystub_detail endpoint."""

    @pytest.fixture
    def mock_employee(self) -> dict[str, Any]:
        """Create a mock employee record."""
        return {
            "id": "emp-123",
            "first_name": "John",
            "last_name": "Doe",
            "company_id": "comp-123",
            "sick_balance": 5.0,
        }

    @pytest.fixture
    def mock_payroll_record(self) -> dict[str, Any]:
        """Create a mock payroll record."""
        return {
            "id": "record-123",
            "gross_regular": 3200.0,
            "gross_overtime": 0.0,
            "vacation_pay_paid": 200.0,
            "sick_pay_paid": 0.0,
            "sick_hours_taken": 0.0,
            "holiday_pay": 0.0,
            "holiday_premium_pay": 0.0,
            "cpp_employee": 150.0,
            "ei_employee": 80.0,
            "federal_tax": 400.0,
            "provincial_tax": 200.0,
            "rrsp": 100.0,
            "union_dues": 0.0,
            "total_gross": 3400.0,
            "total_deductions": 930.0,
            "net_pay": 2470.0,
            "ytd_gross": 15000.0,
            "ytd_cpp": 700.0,
            "ytd_ei": 400.0,
            "ytd_federal_tax": 2000.0,
            "ytd_provincial_tax": 1000.0,
            "input_data": {"regularHours": 80},
            "payroll_runs": {
                "pay_date": "2025-01-15",
                "period_start": "2025-01-01",
                "period_end": "2025-01-14",
                "status": "approved",
            },
        }

    @pytest.mark.asyncio
    async def test_raises_404_when_no_employee(self):
        """Test raises 404 when no employee found."""
        from app.api.v1.employee_portal import get_paystub_detail

        user = MockCurrentUser()

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_paystub_detail("record-123", user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_when_record_not_found(self, mock_employee):
        """Test raises 404 when payroll record not found."""
        from app.api.v1.employee_portal import get_paystub_detail

        user = MockCurrentUser()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_result

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_paystub_detail("record-123", user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_paystub_detail(self, mock_employee, mock_payroll_record):
        """Test returns detailed paystub."""
        from app.api.v1.employee_portal import get_paystub_detail

        user = MockCurrentUser()

        mock_supabase = MagicMock()

        # Mock payroll record query
        mock_record_result = MagicMock()
        mock_record_result.data = mock_payroll_record

        # Mock company query
        mock_company_result = MagicMock()
        mock_company_result.data = [{"company_name": "Acme Corp"}]

        def table_side_effect(table_name):
            mock = MagicMock()
            if table_name == "payroll_records":
                mock.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_record_result
            elif table_name == "companies":
                mock.select.return_value.eq.return_value.execute.return_value = mock_company_result
            return mock

        mock_supabase.table.side_effect = table_side_effect

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            result = await get_paystub_detail("record-123", user)

        assert result.id == "record-123"
        assert result.grossPay == 3400.0
        assert result.netPay == 2470.0
        assert result.companyName == "Acme Corp"
        assert len(result.earnings) >= 2  # Regular + Vacation
        assert len(result.deductions) >= 4  # CPP, EI, Fed Tax, Prov Tax


class TestGetMyLeaveBalance:
    """Tests for get_my_leave_balance endpoint."""

    @pytest.fixture
    def mock_employee(self) -> dict[str, Any]:
        """Create a mock employee record."""
        return {
            "id": "emp-123",
            "hourly_rate": 40.0,
            "province_of_employment": "ON",
            "hire_date": "2024-01-15",
            "vacation_config": {"vacation_rate": 0.04},
            "vacation_balance": 800.0,
        }

    @pytest.mark.asyncio
    async def test_raises_404_when_no_employee(self):
        """Test raises 404 when no employee found."""
        from app.api.v1.employee_portal import get_my_leave_balance

        user = MockCurrentUser()

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_my_leave_balance(user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_leave_balance(self, mock_employee):
        """Test returns leave balance response."""
        from app.api.v1.employee_portal import get_my_leave_balance

        user = MockCurrentUser()

        mock_supabase = MagicMock()

        # Mock empty records result
        mock_records_result = MagicMock()
        mock_records_result.data = []

        mock_gross_result = MagicMock()
        mock_gross_result.data = []

        mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.gte.return_value.lte.return_value.execute.return_value = mock_records_result
        mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.gte.return_value.lt.return_value.execute.return_value = mock_gross_result

        mock_sick_leave_service = MagicMock()
        mock_sick_leave_service.get_config.return_value = MagicMock(paid_days_per_year=5)
        mock_sick_leave_service.create_new_year_balance.return_value = MagicMock(paid_days_remaining=5.0)

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
            patch(
                "app.services.payroll.sick_leave_service.SickLeaveService",
                return_value=mock_sick_leave_service,
            ),
        ):
            result = await get_my_leave_balance(user)

        assert result.vacationDollars == 800.0
        assert result.vacationHours == 20.0  # 800 / 40
        assert result.sickHoursAllowance == 40.0  # 5 days * 8 hours


class TestUpdatePersonalInfo:
    """Tests for update_personal_info endpoint."""

    @pytest.fixture
    def mock_employee(self) -> dict[str, Any]:
        """Create a mock employee record."""
        return {"id": "emp-123", "first_name": "John", "last_name": "Doe"}

    @pytest.mark.asyncio
    async def test_raises_404_when_no_employee(self):
        """Test raises 404 when no employee found."""
        from app.api.v1.employee_portal import update_personal_info

        user = MockCurrentUser()
        request = PersonalInfoUpdateRequest(phone="416-555-0123")

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_personal_info(request, user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_success_when_no_changes(self, mock_employee):
        """Test returns success when no changes to update."""
        from app.api.v1.employee_portal import update_personal_info

        user = MockCurrentUser()
        request = PersonalInfoUpdateRequest()  # All fields None

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=mock_employee,
        ):
            result = await update_personal_info(request, user)

        assert result.success is True
        assert "No changes" in result.message

    @pytest.mark.asyncio
    async def test_updates_personal_info(self, mock_employee):
        """Test updates personal information."""
        from app.api.v1.employee_portal import update_personal_info

        user = MockCurrentUser()
        request = PersonalInfoUpdateRequest(
            phone="416-555-9999",
            addressStreet="456 New St",
            addressCity="Vancouver",
        )

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            result = await update_personal_info(request, user)

        assert result.success is True
        assert "updated successfully" in result.message

        # Verify update was called with correct data
        update_call = mock_supabase.table.return_value.update.call_args[0][0]
        assert update_call["phone"] == "416-555-9999"
        assert update_call["address_street"] == "456 New St"
        assert update_call["address_city"] == "Vancouver"

    @pytest.mark.asyncio
    async def test_handles_update_failure(self, mock_employee):
        """Test handles update failure gracefully."""
        from app.api.v1.employee_portal import update_personal_info

        user = MockCurrentUser()
        request = PersonalInfoUpdateRequest(phone="416-555-9999")

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("DB error")

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_personal_info(request, user)

        assert exc_info.value.status_code == 500


class TestSubmitTaxChangeRequest:
    """Tests for submit_tax_change_request endpoint."""

    @pytest.fixture
    def mock_employee(self) -> dict[str, Any]:
        """Create a mock employee record."""
        return {
            "id": "emp-123",
            "first_name": "John",
            "last_name": "Doe",
            "company_id": "comp-123",
            "user_id": "user-123",
        }

    @pytest.mark.asyncio
    async def test_raises_404_when_no_employee(self):
        """Test raises 404 when no employee found."""
        from app.api.v1.employee_portal import submit_tax_change_request

        user = MockCurrentUser()
        request = TaxInfoChangeRequest(federalAdditionalClaims=500.0)

        with patch(
            "app.api.v1.employee_portal.get_employee_by_user_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await submit_tax_change_request(request, user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_creates_change_request(self, mock_employee):
        """Test creates change request successfully."""
        from app.api.v1.employee_portal import submit_tax_change_request

        user = MockCurrentUser()
        request = TaxInfoChangeRequest(federalAdditionalClaims=500.0)

        mock_supabase = MagicMock()

        # Mock current tax claims query
        mock_tax_result = MagicMock()
        mock_tax_result.data = {
            "federal_additional_claims": 0.0,
            "provincial_additional_claims": 0.0,
        }

        # Mock insert result
        mock_insert_result = MagicMock()
        mock_insert_result.data = [
            {
                "id": "change-123",
                "submitted_at": "2025-01-15T10:00:00Z",
            }
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_tax_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result

        with (
            patch(
                "app.api.v1.employee_portal.get_employee_by_user_email",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ),
            patch(
                "app.api.v1.employee_portal.get_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            result = await submit_tax_change_request(request, user)

        assert result.id == "change-123"
        assert result.status == "pending"
        assert result.changeType == "tax_info"


class TestInviteToPortal:
    """Tests for invite_to_portal endpoint."""

    @pytest.mark.asyncio
    async def test_raises_404_when_employee_not_found(self):
        """Test raises 404 when employee not found."""
        from app.api.v1.employee_portal import invite_to_portal

        user = MockCurrentUser()
        request = PortalInviteRequest()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await invite_to_portal("emp-123", request, user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_success_when_already_active(self):
        """Test returns success when employee already has active portal access."""
        from app.api.v1.employee_portal import invite_to_portal

        user = MockCurrentUser()
        request = PortalInviteRequest()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = {
            "id": "emp-123",
            "email": "john@example.com",
            "portal_status": "active",
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await invite_to_portal("emp-123", request, user)

        assert result.success is True
        assert result.portalStatus == "active"


class TestGetPendingProfileChanges:
    """Tests for get_pending_profile_changes endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_changes(self):
        """Test returns empty list when no pending changes."""
        from app.api.v1.employee_portal import get_pending_profile_changes

        user = MockCurrentUser()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await get_pending_profile_changes(user)

        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_returns_pending_changes(self):
        """Test returns pending profile changes."""
        from app.api.v1.employee_portal import get_pending_profile_changes

        user = MockCurrentUser()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "change-123",
                "employee_id": "emp-123",
                "change_type": "tax_info",
                "status": "pending",
                "current_values": {"federalAdditionalClaims": 0},
                "requested_values": {"federalAdditionalClaims": 500},
                "submitted_at": "2025-01-15T10:00:00Z",
                "employees": {"first_name": "John", "last_name": "Doe"},
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await get_pending_profile_changes(user)

        assert len(result.items) == 1
        assert result.items[0].id == "change-123"
        assert result.items[0].employeeName == "John Doe"


class TestApproveProfileChange:
    """Tests for approve_profile_change endpoint."""

    @pytest.mark.asyncio
    async def test_raises_404_when_change_not_found(self):
        """Test raises 404 when change request not found."""
        from app.api.v1.employee_portal import approve_profile_change

        user = MockCurrentUser()

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await approve_profile_change("change-123", user)

        assert exc_info.value.status_code == 404


class TestRejectProfileChange:
    """Tests for reject_profile_change endpoint."""

    @pytest.mark.asyncio
    async def test_raises_404_when_change_not_found(self):
        """Test raises 404 when change request not found."""
        from app.api.v1.employee_portal import reject_profile_change

        user = MockCurrentUser()
        request = ChangeRequestActionRequest(rejectionReason="Invalid request")

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await reject_profile_change("change-123", request, user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rejects_change_request(self):
        """Test rejects change request successfully."""
        from app.api.v1.employee_portal import reject_profile_change

        user = MockCurrentUser()
        request = ChangeRequestActionRequest(rejectionReason="Not valid")

        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = {
            "id": "change-123",
            "employee_id": "emp-123",
            "change_type": "tax_info",
            "current_values": {},
            "requested_values": {},
            "submitted_at": "2025-01-15T10:00:00Z",
            "employees": {"first_name": "John", "last_name": "Doe"},
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        with patch(
            "app.api.v1.employee_portal.get_supabase_client",
            return_value=mock_supabase,
        ):
            result = await reject_profile_change("change-123", request, user)

        assert result.status == "rejected"
        assert result.rejectionReason == "Not valid"
