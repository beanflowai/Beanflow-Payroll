"""
Tests for PayrollRunOperations.__init__ method.

Covers:
- Initialization of all attributes
- Creation of HolidayPayCalculator
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.payroll_run.run_operations import PayrollRunOperations


class TestInit:
    """Tests for __init__."""

    def test_initializes_all_attributes(
        self,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_user_id: str,
        sample_company_id: str,
    ):
        """Should initialize all instance attributes."""
        get_run = AsyncMock()
        get_records = AsyncMock()
        create_records = AsyncMock()

        with patch(
            "app.services.payroll_run.run_operations.HolidayPayCalculator"
        ) as mock_holiday_calc_class:
            mock_holiday_calc = MagicMock()
            mock_holiday_calc_class.return_value = mock_holiday_calc

            ops = PayrollRunOperations(
                supabase=mock_supabase,
                user_id=sample_user_id,
                company_id=sample_company_id,
                ytd_calculator=mock_ytd_calculator,
                get_run_func=get_run,
                get_run_records_func=get_records,
                create_records_func=create_records,
            )

            assert ops.supabase is mock_supabase
            assert ops.user_id == sample_user_id
            assert ops.company_id == sample_company_id
            assert ops.ytd_calculator is mock_ytd_calculator
            assert ops.holiday_calculator is mock_holiday_calc
            assert ops._get_run is get_run
            assert ops._get_run_records is get_records
            assert ops._create_records_for_employees is create_records

    def test_creates_holiday_calculator(
        self,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_user_id: str,
        sample_company_id: str,
    ):
        """Should create HolidayPayCalculator with correct arguments."""
        with patch(
            "app.services.payroll_run.run_operations.HolidayPayCalculator"
        ) as mock_holiday_calc_class:
            PayrollRunOperations(
                supabase=mock_supabase,
                user_id=sample_user_id,
                company_id=sample_company_id,
                ytd_calculator=mock_ytd_calculator,
                get_run_func=AsyncMock(),
                get_run_records_func=AsyncMock(),
                create_records_func=AsyncMock(),
            )

            mock_holiday_calc_class.assert_called_once_with(
                mock_supabase, sample_user_id, sample_company_id
            )
