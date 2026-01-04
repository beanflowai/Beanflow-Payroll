"""
Tests for sick_leave_config_loader.py module.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.payroll.sick_leave_config_loader import (
    SickLeaveConfigLoader,
    _load_json_file,
    _get_available_editions,
    _get_edition_for_date,
    _load_provinces_config,
    _dict_to_config,
    get_config,
    get_all_configs,
    get_provinces_with_paid_sick_leave,
    get_provinces_with_sick_leave_carryover,
    get_config_metadata,
    clear_cache,
)
from app.services.payroll.sick_leave_service import SickLeaveBalance, SickLeaveConfig


class TestLoadJsonFile:
    """Tests for _load_json_file function."""

    def setup_method(self):
        """Clear LRU cache before each test."""
        _load_json_file.cache_clear()

    def test_loads_valid_json(self, tmp_path: Path):
        """Test loading a valid JSON file."""
        json_file = tmp_path / "test.json"
        expected = {"key": "value", "number": 42}
        json_file.write_text(json.dumps(expected))

        result = _load_json_file(str(json_file))

        assert result == expected

    def test_raises_file_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            _load_json_file(str(missing_file))

    def test_raises_json_decode_error(self, tmp_path: Path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            _load_json_file(str(invalid_file))

    def test_caches_results(self, tmp_path: Path):
        """Test that results are cached."""
        json_file = tmp_path / "cached.json"
        json_file.write_text('{"cached": true}')

        # First call
        result1 = _load_json_file(str(json_file))
        # Modify file
        json_file.write_text('{"cached": false}')
        # Second call should return cached value
        result2 = _load_json_file(str(json_file))

        assert result1 == result2
        assert result1 == {"cached": True}


class TestGetAvailableEditions:
    """Tests for _get_available_editions function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_empty_for_missing_year(self, tmp_path: Path):
        """Test that empty list is returned for missing year directory."""
        with patch("app.services.payroll.sick_leave_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _get_available_editions(2025)

            assert result == []

    def test_returns_editions_sorted_by_date(self, tmp_path: Path):
        """Test that editions are sorted by effective date."""
        year_path = tmp_path / "2025"
        year_path.mkdir()

        # Create two edition files
        jan_file = year_path / "provinces_jan.json"
        jan_file.write_text(json.dumps({
            "effective_date": "2025-01-01",
            "end_date": "2025-05-31",
            "provinces": {}
        }))

        jun_file = year_path / "provinces_jun.json"
        jun_file.write_text(json.dumps({
            "effective_date": "2025-06-01",
            "end_date": "2025-12-31",
            "provinces": {}
        }))

        with patch("app.services.payroll.sick_leave_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _get_available_editions(2025)

            assert len(result) == 2
            assert result[0][0] == "jan"
            assert result[1][0] == "jun"
            assert result[0][1] == date(2025, 1, 1)

    def test_skips_invalid_files(self, tmp_path: Path):
        """Test that invalid config files are skipped."""
        year_path = tmp_path / "2025"
        year_path.mkdir()

        # Create valid file
        valid_file = year_path / "provinces_jan.json"
        valid_file.write_text(json.dumps({
            "effective_date": "2025-01-01",
            "end_date": "2025-12-31",
            "provinces": {}
        }))

        # Create invalid file (missing required fields)
        invalid_file = year_path / "provinces_feb.json"
        invalid_file.write_text('{"provinces": {}}')

        with patch("app.services.payroll.sick_leave_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _get_available_editions(2025)

            assert len(result) == 1
            assert result[0][0] == "jan"


class TestGetEditionForDate:
    """Tests for _get_edition_for_date function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_jan_when_no_editions(self):
        """Test that 'jan' is returned when no editions found."""
        with patch("app.services.payroll.sick_leave_config_loader._get_available_editions", return_value=[]):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_first_edition_for_early_date(self):
        """Test that first edition is returned for early dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 5, 31)),
            ("jun", date(2025, 6, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.sick_leave_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_later_edition_for_later_date(self):
        """Test that later edition is returned for later dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 5, 31)),
            ("jun", date(2025, 6, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.sick_leave_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 7, 15))

            assert result == "jun"

    def test_returns_edition_on_effective_date(self):
        """Test correct edition on exact effective date."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 5, 31)),
            ("jun", date(2025, 6, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.sick_leave_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 6, 1))

            assert result == "jun"

    def test_uses_today_when_no_date(self):
        """Test that today's date is used when pay_date is None."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.sick_leave_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025)

            assert result == "jan"


class TestLoadProvincesConfig:
    """Tests for _load_provinces_config function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_config_for_existing_file(self, tmp_path: Path):
        """Test loading config from existing file."""
        year_path = tmp_path / "2025"
        year_path.mkdir()
        config_file = year_path / "provinces_jan.json"
        expected = {"provinces": {"BC": {"paid_days_per_year": 5}}}
        config_file.write_text(json.dumps(expected))

        with patch("app.services.payroll.sick_leave_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == expected

    def test_returns_empty_provinces_for_missing_file(self, tmp_path: Path):
        """Test that empty provinces dict is returned for missing file."""
        with patch("app.services.payroll.sick_leave_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == {"provinces": {}}


class TestDictToConfig:
    """Tests for _dict_to_config function."""

    def test_converts_complete_dict(self):
        """Test converting a complete dictionary to SickLeaveConfig."""
        province_data = {
            "province_code": "BC",
            "paid_days_per_year": 5,
            "unpaid_days_per_year": 3,
            "waiting_period_days": 90,
            "allows_carryover": True,
            "max_carryover_days": 5,
            "accrual_method": "annual",
            "initial_days_after_qualifying": 0,
            "days_per_month_after_initial": 0,
        }

        result = _dict_to_config(province_data)

        assert isinstance(result, SickLeaveConfig)
        assert result.province_code == "BC"
        assert result.paid_days_per_year == 5
        assert result.unpaid_days_per_year == 3
        assert result.waiting_period_days == 90
        assert result.allows_carryover is True
        assert result.max_carryover_days == 5
        assert result.accrual_method == "annual"

    def test_uses_defaults_for_optional_fields(self):
        """Test that defaults are used for optional fields."""
        province_data = {
            "province_code": "ON",
            "paid_days_per_year": 3,
            "unpaid_days_per_year": 0,
            "waiting_period_days": 0,
            "allows_carryover": False,
            "max_carryover_days": 0,
            "accrual_method": "annual",
            # initial_days_after_qualifying and days_per_month_after_initial omitted
        }

        result = _dict_to_config(province_data)

        assert result.initial_days_after_qualifying == 0
        assert result.days_per_month_after_initial == 0


class TestGetConfig:
    """Tests for get_config function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_config_for_existing_province(self):
        """Test getting config for an existing province."""
        province_data = {
            "province_code": "BC",
            "paid_days_per_year": 5,
            "unpaid_days_per_year": 3,
            "waiting_period_days": 90,
            "allows_carryover": True,
            "max_carryover_days": 5,
            "accrual_method": "annual",
        }

        with patch("app.services.payroll.sick_leave_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.sick_leave_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": province_data}}

            result = get_config("BC")

            assert result is not None
            assert result.province_code == "BC"
            assert result.paid_days_per_year == 5

    def test_returns_none_for_missing_province(self):
        """Test that None is returned for missing province."""
        with patch("app.services.payroll.sick_leave_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.sick_leave_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": {}}}

            result = get_config("ON")

            assert result is None


class TestGetAllConfigs:
    """Tests for get_all_configs function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_all_configs(self):
        """Test getting all configs."""
        bc_data = {
            "province_code": "BC",
            "paid_days_per_year": 5,
            "unpaid_days_per_year": 3,
            "waiting_period_days": 90,
            "allows_carryover": True,
            "max_carryover_days": 5,
            "accrual_method": "annual",
        }
        on_data = {
            "province_code": "ON",
            "paid_days_per_year": 3,
            "unpaid_days_per_year": 0,
            "waiting_period_days": 0,
            "allows_carryover": False,
            "max_carryover_days": 0,
            "accrual_method": "annual",
        }

        with patch("app.services.payroll.sick_leave_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.sick_leave_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": bc_data, "ON": on_data}}

            result = get_all_configs()

            assert len(result) == 2
            assert "BC" in result
            assert "ON" in result
            assert result["BC"].paid_days_per_year == 5
            assert result["ON"].paid_days_per_year == 3


class TestGetProvincesWithPaidSickLeave:
    """Tests for get_provinces_with_paid_sick_leave function."""

    def test_returns_provinces_with_paid_leave(self):
        """Test getting provinces with paid sick leave."""
        bc_config = SickLeaveConfig(
            province_code="BC",
            paid_days_per_year=5,
            unpaid_days_per_year=3,
            waiting_period_days=90,
            allows_carryover=True,
            max_carryover_days=5,
            accrual_method="annual",
        )
        ab_config = SickLeaveConfig(
            province_code="AB",
            paid_days_per_year=0,  # No paid leave
            unpaid_days_per_year=5,
            waiting_period_days=90,
            allows_carryover=False,
            max_carryover_days=0,
            accrual_method="annual",
        )

        with patch("app.services.payroll.sick_leave_config_loader.get_all_configs") as mock:
            mock.return_value = {"BC": bc_config, "AB": ab_config}

            result = get_provinces_with_paid_sick_leave()

            assert result == ["BC"]


class TestGetProvincesWithSickLeaveCarryover:
    """Tests for get_provinces_with_sick_leave_carryover function."""

    def test_returns_provinces_with_carryover(self):
        """Test getting provinces with sick leave carryover."""
        bc_config = SickLeaveConfig(
            province_code="BC",
            paid_days_per_year=5,
            unpaid_days_per_year=3,
            waiting_period_days=90,
            allows_carryover=True,
            max_carryover_days=5,
            accrual_method="annual",
        )
        on_config = SickLeaveConfig(
            province_code="ON",
            paid_days_per_year=3,
            unpaid_days_per_year=0,
            waiting_period_days=0,
            allows_carryover=False,
            max_carryover_days=0,
            accrual_method="annual",
        )

        with patch("app.services.payroll.sick_leave_config_loader.get_all_configs") as mock:
            mock.return_value = {"BC": bc_config, "ON": on_config}

            result = get_provinces_with_sick_leave_carryover()

            assert result == ["BC"]


class TestGetConfigMetadata:
    """Tests for get_config_metadata function."""

    def test_returns_metadata(self):
        """Test getting config metadata."""
        config_data = {
            "year": 2025,
            "edition": "jan",
            "effective_date": "2025-01-01",
            "end_date": "2025-12-31",
            "source": "Provincial regulations",
            "changes": ["Initial 2025 configuration"],
        }

        with patch("app.services.payroll.sick_leave_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.sick_leave_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = config_data

            result = get_config_metadata()

            assert result["year"] == 2025
            assert result["edition"] == "jan"
            assert result["effective_date"] == "2025-01-01"
            assert result["source"] == "Provincial regulations"

    def test_returns_defaults_for_missing_fields(self):
        """Test defaults are used for missing metadata fields."""
        with patch("app.services.payroll.sick_leave_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.sick_leave_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {}

            result = get_config_metadata(year=2025)

            assert result["year"] == 2025
            assert result["edition"] == "jan"
            assert result["changes"] == []


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clears_json_cache(self, tmp_path: Path):
        """Test that cache is cleared."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"initial": true}')

        # Load file to cache it
        _load_json_file(str(json_file))

        # Modify file
        json_file.write_text('{"modified": true}')

        # Clear cache
        clear_cache()

        # Reload - should get new value
        result = _load_json_file(str(json_file))

        assert result == {"modified": True}


class TestSickLeaveConfigLoader:
    """Tests for SickLeaveConfigLoader class."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def loader(self, mock_supabase):
        """Create a SickLeaveConfigLoader with mocked configs."""
        with patch("app.services.payroll.sick_leave_config_loader.get_all_configs") as mock:
            mock.return_value = {
                "BC": SickLeaveConfig(
                    province_code="BC",
                    paid_days_per_year=5,
                    unpaid_days_per_year=3,
                    waiting_period_days=90,
                    allows_carryover=True,
                    max_carryover_days=5,
                    accrual_method="annual",
                ),
            }
            return SickLeaveConfigLoader(mock_supabase, year=2025)

    def test_init_loads_configs(self, mock_supabase):
        """Test that configs are loaded on initialization."""
        with patch("app.services.payroll.sick_leave_config_loader.get_all_configs") as mock:
            mock.return_value = {"BC": MagicMock()}

            loader = SickLeaveConfigLoader(mock_supabase, year=2025)

            mock.assert_called_once_with(2025, None)
            assert "BC" in loader._configs

    def test_get_config_returns_province(self, loader):
        """Test getting config for existing province."""
        result = loader.get_config("BC")

        assert result is not None
        assert result.province_code == "BC"

    def test_get_config_returns_none_for_missing(self, loader):
        """Test getting config for non-existing province."""
        result = loader.get_config("ZZ")

        assert result is None

    def test_get_all_configs(self, loader):
        """Test getting all configs."""
        result = loader.get_all_configs()

        assert "BC" in result

    def test_clear_cache_reloads_configs(self, loader, mock_supabase):
        """Test that clear_cache reloads configurations."""
        with patch("app.services.payroll.sick_leave_config_loader.clear_cache") as mock_clear, \
             patch("app.services.payroll.sick_leave_config_loader.get_all_configs") as mock_get:
            mock_get.return_value = {"ON": MagicMock()}

            loader.clear_cache()

            mock_clear.assert_called_once()
            mock_get.assert_called_once_with(2025, None)


class TestSickLeaveConfigLoaderEmployeeBalance:
    """Tests for SickLeaveConfigLoader employee balance operations."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def loader(self, mock_supabase):
        """Create a SickLeaveConfigLoader."""
        with patch("app.services.payroll.sick_leave_config_loader.get_all_configs", return_value={}):
            return SickLeaveConfigLoader(mock_supabase, year=2025)

    @pytest.mark.asyncio
    async def test_get_employee_balance_success(self, loader, mock_supabase):
        """Test successfully getting employee balance."""
        balance_data = {
            "employee_id": "emp-123",
            "year": 2025,
            "paid_days_entitled": "5",
            "unpaid_days_entitled": "3",
            "paid_days_used": "2",
            "unpaid_days_used": "1",
            "carried_over_days": "0",
            "is_eligible": True,
            "eligibility_date": "2025-03-15",
            "accrued_days_ytd": "2.5",
        }

        mock_response = MagicMock()
        mock_response.data = balance_data
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await loader.get_employee_balance("emp-123", 2025)

        assert result is not None
        assert result.employee_id == "emp-123"
        assert result.year == 2025
        assert result.paid_days_entitled == Decimal("5")
        assert result.paid_days_used == Decimal("2")
        assert result.is_eligible is True
        assert result.eligibility_date == date(2025, 3, 15)

    @pytest.mark.asyncio
    async def test_get_employee_balance_not_found(self, loader, mock_supabase):
        """Test getting non-existent employee balance."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await loader.get_employee_balance("emp-999", 2025)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_employee_balance_handles_exception(self, loader, mock_supabase):
        """Test handling exception when getting balance."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")

        result = await loader.get_employee_balance("emp-123", 2025)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_employee_balance_without_eligibility_date(self, loader, mock_supabase):
        """Test getting balance without eligibility date."""
        balance_data = {
            "employee_id": "emp-123",
            "year": 2025,
            "paid_days_entitled": "5",
            "unpaid_days_entitled": "3",
            "paid_days_used": "0",
            "unpaid_days_used": "0",
            "carried_over_days": "0",
            "is_eligible": False,
            "eligibility_date": None,
            "accrued_days_ytd": "0",
        }

        mock_response = MagicMock()
        mock_response.data = balance_data
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await loader.get_employee_balance("emp-123", 2025)

        assert result is not None
        assert result.eligibility_date is None

    @pytest.mark.asyncio
    async def test_create_employee_balance_success(self, loader, mock_supabase):
        """Test successfully creating employee balance."""
        balance = SickLeaveBalance(
            employee_id="emp-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
            eligibility_date=date(2025, 3, 15),
            accrued_days_ytd=Decimal("0"),
        )

        mock_response = MagicMock()
        mock_response.data = {"id": "balance-1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        result = await loader.create_employee_balance(balance)

        assert result is not None
        assert result.employee_id == "emp-123"
        mock_supabase.table.assert_called_with("employee_sick_leave_balances")

    @pytest.mark.asyncio
    async def test_create_employee_balance_failure(self, loader, mock_supabase):
        """Test handling failure when creating balance."""
        balance = SickLeaveBalance(
            employee_id="emp-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
            accrued_days_ytd=Decimal("0"),
        )

        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        result = await loader.create_employee_balance(balance)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_employee_balance_handles_exception(self, loader, mock_supabase):
        """Test handling exception when creating balance."""
        balance = SickLeaveBalance(
            employee_id="emp-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
            accrued_days_ytd=Decimal("0"),
        )

        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB error")

        result = await loader.create_employee_balance(balance)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_employee_balance_success(self, loader, mock_supabase):
        """Test successfully updating employee balance."""
        # Mock get_employee_balance
        current_balance = SickLeaveBalance(
            employee_id="emp-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("1"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
            accrued_days_ytd=Decimal("2"),
        )

        with patch.object(loader, "get_employee_balance", return_value=current_balance):
            mock_response = MagicMock()
            mock_response.data = {"id": "balance-1"}
            mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

            result = await loader.update_employee_balance(
                "emp-123", 2025, paid_days_used_delta=Decimal("1")
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_update_employee_balance_no_current_balance(self, loader, mock_supabase):
        """Test updating when no current balance exists."""
        with patch.object(loader, "get_employee_balance", return_value=None):
            result = await loader.update_employee_balance(
                "emp-123", 2025, paid_days_used_delta=Decimal("1")
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_update_employee_balance_handles_exception(self, loader, mock_supabase):
        """Test handling exception when updating balance."""
        current_balance = SickLeaveBalance(
            employee_id="emp-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("1"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
            accrued_days_ytd=Decimal("2"),
        )

        with patch.object(loader, "get_employee_balance", return_value=current_balance):
            mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")

            result = await loader.update_employee_balance(
                "emp-123", 2025, paid_days_used_delta=Decimal("1")
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_record_sick_leave_usage_success(self, loader, mock_supabase):
        """Test successfully recording sick leave usage."""
        mock_response = MagicMock()
        mock_response.data = {"id": "usage-1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        result = await loader.record_sick_leave_usage(
            employee_id="emp-123",
            balance_id="balance-1",
            payroll_record_id="payroll-1",
            usage_date=date(2025, 3, 15),
            hours_taken=Decimal("8"),
            days_taken=Decimal("1"),
            is_paid=True,
            average_day_pay=Decimal("200"),
            sick_pay_amount=Decimal("200"),
            calculation_method="bc_30_day_avg",
            notes="Sick day",
        )

        assert result is True
        mock_supabase.table.assert_called_with("sick_leave_usage_history")

    @pytest.mark.asyncio
    async def test_record_sick_leave_usage_without_optional_fields(self, loader, mock_supabase):
        """Test recording usage without optional fields."""
        mock_response = MagicMock()
        mock_response.data = {"id": "usage-1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        result = await loader.record_sick_leave_usage(
            employee_id="emp-123",
            balance_id="balance-1",
            payroll_record_id=None,
            usage_date=date(2025, 3, 15),
            hours_taken=Decimal("8"),
            days_taken=Decimal("1"),
            is_paid=True,
            average_day_pay=Decimal("200"),
            sick_pay_amount=Decimal("200"),
            calculation_method="bc_30_day_avg",
            notes=None,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_sick_leave_usage_failure(self, loader, mock_supabase):
        """Test handling failure when recording usage."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        result = await loader.record_sick_leave_usage(
            employee_id="emp-123",
            balance_id="balance-1",
            payroll_record_id=None,
            usage_date=date(2025, 3, 15),
            hours_taken=Decimal("8"),
            days_taken=Decimal("1"),
            is_paid=True,
            average_day_pay=Decimal("200"),
            sick_pay_amount=Decimal("200"),
            calculation_method="bc_30_day_avg",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_record_sick_leave_usage_handles_exception(self, loader, mock_supabase):
        """Test handling exception when recording usage."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB error")

        result = await loader.record_sick_leave_usage(
            employee_id="emp-123",
            balance_id="balance-1",
            payroll_record_id=None,
            usage_date=date(2025, 3, 15),
            hours_taken=Decimal("8"),
            days_taken=Decimal("1"),
            is_paid=True,
            average_day_pay=Decimal("200"),
            sick_pay_amount=Decimal("200"),
            calculation_method="bc_30_day_avg",
        )

        assert result is False
