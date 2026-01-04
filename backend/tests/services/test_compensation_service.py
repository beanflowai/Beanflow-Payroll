"""Tests for compensation service."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from postgrest.exceptions import APIError

from app.models.compensation import CompensationHistoryCreate
from app.services.compensation_service import CompensationService


class TestCompensationServiceInit:
    """Tests for CompensationService initialization."""

    def test_init_sets_user_and_company(self):
        """Test initialization sets user and company IDs."""
        with patch(
            "app.services.compensation_service.get_supabase_client"
        ) as mock_client:
            mock_client.return_value = MagicMock()

            service = CompensationService("user-123", "company-456")

            assert service.user_id == "user-123"
            assert service.company_id == "company-456"


class TestUpdateCompensation:
    """Tests for update_compensation method."""

    @pytest.mark.asyncio
    async def test_update_compensation_success(self):
        """Test successful compensation update."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "employee_id": str(uuid4()),
            "compensation_type": "salary",
            "annual_salary": "60000.00",
            "hourly_rate": None,
            "effective_date": "2025-01-15",
            "end_date": None,
            "change_reason": "Annual raise",
            "created_at": "2025-01-15T12:00:00Z",
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("60000"),
                hourlyRate=None,
                effectiveDate=date(2025, 1, 15),
                changeReason="Annual raise",
            )

            result = await service.update_compensation(employee_id, data)

            assert result is not None
            assert result.compensationType == "salary"
            mock_supabase.rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_compensation_empty_result_raises(self):
        """Test empty result raises ValueError."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.rpc.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("50000"),
                hourlyRate=None,
                effectiveDate=date(2025, 1, 15),
                changeReason="Test",
            )

            with pytest.raises(ValueError, match="Failed to create"):
                await service.update_compensation(employee_id, data)

    @pytest.mark.asyncio
    async def test_update_compensation_date_error(self):
        """Test effective date error is handled."""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = APIError({
            "message": "must be after current effective date"
        })

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("50000"),
                hourlyRate=None,
                effectiveDate=date(2025, 1, 1),
                changeReason="Backdate attempt",
            )

            with pytest.raises(ValueError, match="after current effective date"):
                await service.update_compensation(employee_id, data)

    @pytest.mark.asyncio
    async def test_update_compensation_invalid_type_error(self):
        """Test invalid compensation type error from database is handled."""
        mock_supabase = MagicMock()
        # Simulate a database error about invalid compensation type
        mock_supabase.rpc.return_value.execute.side_effect = APIError({
            "message": "Invalid compensation type: bad_type"
        })

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            # Use a valid type for the model, but simulate DB rejecting it
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("50000"),
                hourlyRate=None,
                effectiveDate=date(2025, 1, 15),
                changeReason="Test",
            )

            with pytest.raises(ValueError, match="Invalid compensation type"):
                await service.update_compensation(employee_id, data)

    @pytest.mark.asyncio
    async def test_update_compensation_required_field_error(self):
        """Test required field error from database is handled."""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = APIError({
            "message": "annual_salary is required and must be positive"
        })

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            # Use valid model data, simulate DB rejecting due to internal check
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("0.01"),  # Very small but valid
                hourlyRate=None,
                effectiveDate=date(2025, 1, 15),
                changeReason="Test",
            )

            with pytest.raises(ValueError, match="required and must be positive"):
                await service.update_compensation(employee_id, data)

    @pytest.mark.asyncio
    async def test_update_compensation_generic_api_error(self):
        """Test generic API error is handled."""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = APIError({
            "message": "Some other database error"
        })

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            data = CompensationHistoryCreate(
                compensationType="salary",
                annualSalary=Decimal("50000"),
                hourlyRate=None,
                effectiveDate=date(2025, 1, 15),
                changeReason="Test",
            )

            with pytest.raises(ValueError, match="Database error"):
                await service.update_compensation(employee_id, data)

    @pytest.mark.asyncio
    async def test_update_compensation_hourly(self):
        """Test updating to hourly compensation."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "employee_id": str(uuid4()),
            "compensation_type": "hourly",
            "annual_salary": None,
            "hourly_rate": "25.00",
            "effective_date": "2025-02-01",
            "end_date": None,
            "change_reason": "Switch to hourly",
            "created_at": "2025-02-01T12:00:00Z",
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()
            data = CompensationHistoryCreate(
                compensationType="hourly",
                annualSalary=None,
                hourlyRate=Decimal("25.00"),
                effectiveDate=date(2025, 2, 1),
                changeReason="Switch to hourly",
            )

            result = await service.update_compensation(employee_id, data)

            assert result.compensationType == "hourly"


class TestGetCurrentCompensation:
    """Tests for get_current_compensation method."""

    @pytest.mark.asyncio
    async def test_get_current_compensation_exists(self):
        """Test getting current compensation when it exists."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "employee_id": str(uuid4()),
            "compensation_type": "salary",
            "annual_salary": "55000.00",
            "hourly_rate": None,
            "effective_date": "2025-01-01",
            "end_date": None,
            "change_reason": "Initial",
            "created_at": "2025-01-01T12:00:00Z",
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()

            result = await service.get_current_compensation(employee_id)

            assert result is not None
            assert result.compensationType == "salary"

    @pytest.mark.asyncio
    async def test_get_current_compensation_not_found(self):
        """Test getting current compensation when none exists."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()

            result = await service.get_current_compensation(employee_id)

            assert result is None


class TestGetCompensationHistory:
    """Tests for get_compensation_history method."""

    @pytest.mark.asyncio
    async def test_get_compensation_history_multiple(self):
        """Test getting compensation history with multiple records."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "employee_id": str(uuid4()),
                "compensation_type": "salary",
                "annual_salary": "60000.00",
                "hourly_rate": None,
                "effective_date": "2025-01-15",
                "end_date": None,
                "change_reason": "Annual raise",
                "created_at": "2025-01-15T12:00:00Z",
            },
            {
                "id": str(uuid4()),
                "employee_id": str(uuid4()),
                "compensation_type": "salary",
                "annual_salary": "55000.00",
                "hourly_rate": None,
                "effective_date": "2024-01-01",
                "end_date": "2025-01-14",
                "change_reason": "Initial",
                "created_at": "2024-01-01T12:00:00Z",
            },
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()

            result = await service.get_compensation_history(employee_id)

            assert len(result) == 2
            assert result[0].annualSalary == Decimal("60000.00")
            assert result[1].annualSalary == Decimal("55000.00")

    @pytest.mark.asyncio
    async def test_get_compensation_history_empty(self):
        """Test getting compensation history when none exists."""
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        with patch(
            "app.services.compensation_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = CompensationService("user-123", "company-456")
            employee_id = uuid4()

            result = await service.get_compensation_history(employee_id)

            assert result == []
