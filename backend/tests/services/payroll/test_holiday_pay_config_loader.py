"""
Tests for holiday_pay_config_loader.py module.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll.holiday_pay_config_loader import (
    HolidayPayConfigLoader,
    DEFAULT_BC_CONFIG,
    _load_json_file,
    _get_available_editions,
    _get_edition_for_date,
    _load_provinces_config,
    _dict_to_config,
    get_config,
    get_all_configs,
    get_config_metadata,
    clear_cache,
)


class TestDefaultBcConfig:
    """Tests for DEFAULT_BC_CONFIG constant."""

    def test_default_config_is_bc(self):
        """Test that default config is BC."""
        assert DEFAULT_BC_CONFIG.province_code == "BC"

    def test_default_config_formula_type(self):
        """Test default config formula type."""
        assert DEFAULT_BC_CONFIG.formula_type == "30_day_average"

    def test_default_config_lookback_days(self):
        """Test default config lookback days."""
        assert DEFAULT_BC_CONFIG.formula_params.lookback_days == 30

    def test_default_config_premium_rate(self):
        """Test default config premium rate."""
        assert DEFAULT_BC_CONFIG.premium_rate == Decimal("1.5")

    def test_default_config_eligibility(self):
        """Test default config eligibility rules."""
        assert DEFAULT_BC_CONFIG.eligibility.min_employment_days == 30
        assert DEFAULT_BC_CONFIG.eligibility.require_last_first_rule is False

    def test_default_config_daily_hours(self):
        """Test default config daily hours."""
        assert DEFAULT_BC_CONFIG.formula_params.default_daily_hours == Decimal("8")


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
        with patch("app.services.payroll.holiday_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
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
            "end_date": "2025-08-31",
            "provinces": {}
        }))

        sep_file = year_path / "provinces_sep.json"
        sep_file.write_text(json.dumps({
            "effective_date": "2025-09-01",
            "end_date": "2025-12-31",
            "provinces": {}
        }))

        with patch("app.services.payroll.holiday_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _get_available_editions(2025)

            assert len(result) == 2
            assert result[0][0] == "jan"
            assert result[1][0] == "sep"

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

        with patch("app.services.payroll.holiday_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
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
        with patch("app.services.payroll.holiday_pay_config_loader._get_available_editions", return_value=[]):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_first_edition_for_early_date(self):
        """Test that first edition is returned for early dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 8, 31)),
            ("sep", date(2025, 9, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.holiday_pay_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_later_edition_for_later_date(self):
        """Test that later edition is returned for later dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 8, 31)),
            ("sep", date(2025, 9, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.holiday_pay_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 10, 15))

            assert result == "sep"

    def test_uses_today_when_no_date_provided(self):
        """Test that today is used when pay_date is None."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.holiday_pay_config_loader._get_available_editions", return_value=editions):
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
        expected = {"provinces": {"BC": {"formula_type": "30_day_average"}}}
        config_file.write_text(json.dumps(expected))

        with patch("app.services.payroll.holiday_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == expected

    def test_returns_empty_provinces_for_missing_file(self, tmp_path: Path):
        """Test that empty provinces dict is returned for missing file."""
        with patch("app.services.payroll.holiday_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == {"provinces": {}}


class TestDictToConfig:
    """Tests for _dict_to_config function."""

    def test_converts_basic_config(self):
        """Test converting a basic config dictionary."""
        province_data = {
            "province_code": "BC",
            "formula_type": "30_day_average",
            "formula_params": {
                "lookback_days": 30,
                "method": "total_wages_div_days",
                "include_overtime": False,
                "default_daily_hours": 8,
            },
            "eligibility": {
                "min_employment_days": 30,
                "require_last_first_rule": False,
            },
            "premium_rate": 1.5,
            "name": "British Columbia",
            "notes": "BC holiday pay",
        }

        result = _dict_to_config(province_data)

        assert isinstance(result, HolidayPayConfig)
        assert result.province_code == "BC"
        assert result.formula_type == "30_day_average"
        assert result.formula_params.lookback_days == 30
        assert result.eligibility.min_employment_days == 30
        assert result.premium_rate == Decimal("1.5")
        assert result.name == "British Columbia"

    def test_converts_ontario_config(self):
        """Test converting Ontario-style config with lookback_weeks."""
        province_data = {
            "province_code": "ON",
            "formula_type": "4_week_average",
            "formula_params": {
                "lookback_weeks": 4,
                "divisor": 20,
                "include_vacation_pay": True,
            },
            "eligibility": {
                "min_employment_days": 0,
                "require_last_first_rule": True,
            },
            "premium_rate": 1.5,
        }

        result = _dict_to_config(province_data)

        assert result.formula_type == "4_week_average"
        assert result.formula_params.lookback_weeks == 4
        assert result.formula_params.divisor == 20
        assert result.formula_params.include_vacation_pay is True
        assert result.eligibility.require_last_first_rule is True

    def test_converts_saskatchewan_config(self):
        """Test converting Saskatchewan-style config with percentage."""
        province_data = {
            "province_code": "SK",
            "formula_type": "5_percent_28_days",
            "formula_params": {
                "percentage": 0.05,
                "lookback_days": 28,
                "include_previous_holiday_pay": True,
            },
            "eligibility": {
                "min_employment_days": 0,
                "require_last_first_rule": False,
            },
            "premium_rate": 1.5,
        }

        result = _dict_to_config(province_data)

        assert result.formula_type == "5_percent_28_days"
        assert result.formula_params.percentage == Decimal("0.05")
        assert result.formula_params.lookback_days == 28
        assert result.formula_params.include_previous_holiday_pay is True

    def test_uses_default_values(self):
        """Test that default values are used for missing fields."""
        province_data = {
            "province_code": "AB",
            "formula_type": "4_week_average_daily",
            "formula_params": {},
            "eligibility": {},
        }

        result = _dict_to_config(province_data)

        assert result.formula_params.default_daily_hours == Decimal("8")
        assert result.eligibility.min_employment_days == 30
        assert result.premium_rate == Decimal("1.5")

    def test_handles_new_employee_fallback(self):
        """Test handling of new_employee_fallback parameter."""
        province_data = {
            "province_code": "SK",
            "formula_type": "5_percent_28_days",
            "formula_params": {
                "new_employee_fallback": "pro_rated",
            },
            "eligibility": {},
        }

        result = _dict_to_config(province_data)

        assert result.formula_params.new_employee_fallback == "pro_rated"


class TestGetConfig:
    """Tests for get_config function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_config_for_existing_province(self):
        """Test getting config for an existing province."""
        province_data = {
            "province_code": "BC",
            "formula_type": "30_day_average",
            "formula_params": {"lookback_days": 30},
            "eligibility": {"min_employment_days": 30},
        }

        with patch("app.services.payroll.holiday_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.holiday_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": province_data}}

            result = get_config("BC")

            assert result.province_code == "BC"
            assert result.formula_type == "30_day_average"

    def test_returns_default_for_missing_province(self):
        """Test that DEFAULT_BC_CONFIG is returned for missing province."""
        with patch("app.services.payroll.holiday_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.holiday_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {}}

            result = get_config("ZZ")

            assert result == DEFAULT_BC_CONFIG


class TestGetAllConfigs:
    """Tests for get_all_configs function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_all_configs(self):
        """Test getting all configs."""
        bc_data = {
            "province_code": "BC",
            "formula_type": "30_day_average",
            "formula_params": {"lookback_days": 30},
            "eligibility": {},
        }
        on_data = {
            "province_code": "ON",
            "formula_type": "4_week_average",
            "formula_params": {"lookback_weeks": 4},
            "eligibility": {},
        }

        with patch("app.services.payroll.holiday_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.holiday_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": bc_data, "ON": on_data}}

            result = get_all_configs()

            assert len(result) == 2
            assert "BC" in result
            assert "ON" in result
            assert result["BC"].formula_type == "30_day_average"
            assert result["ON"].formula_type == "4_week_average"


class TestGetConfigMetadata:
    """Tests for get_config_metadata function."""

    def test_returns_metadata(self):
        """Test getting config metadata."""
        config_data = {
            "year": 2025,
            "edition": "jan",
            "effective_date": "2025-01-01",
            "end_date": "2025-12-31",
            "source": "Provincial ESA",
            "changes": ["Initial 2025 configuration"],
        }

        with patch("app.services.payroll.holiday_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.holiday_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = config_data

            result = get_config_metadata()

            assert result["year"] == 2025
            assert result["edition"] == "jan"
            assert result["source"] == "Provincial ESA"
            assert result["changes"] == ["Initial 2025 configuration"]

    def test_uses_defaults_for_missing_fields(self):
        """Test that defaults are used for missing metadata fields."""
        with patch("app.services.payroll.holiday_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.holiday_pay_config_loader._load_provinces_config") as mock_load:
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


class TestHolidayPayConfigLoader:
    """Tests for HolidayPayConfigLoader class."""

    @pytest.fixture
    def mock_configs(self) -> dict[str, HolidayPayConfig]:
        """Create mock configs."""
        return {
            "BC": HolidayPayConfig(
                province_code="BC",
                formula_type="30_day_average",
                formula_params=HolidayPayFormulaParams(
                    lookback_days=30,
                    method="total_wages_div_days",
                ),
                eligibility=HolidayPayEligibility(
                    min_employment_days=30,
                    require_last_first_rule=False,
                ),
                premium_rate=Decimal("1.5"),
            ),
            "ON": HolidayPayConfig(
                province_code="ON",
                formula_type="4_week_average",
                formula_params=HolidayPayFormulaParams(
                    lookback_weeks=4,
                    divisor=20,
                    include_vacation_pay=True,
                ),
                eligibility=HolidayPayEligibility(
                    min_employment_days=0,
                    require_last_first_rule=True,
                ),
                premium_rate=Decimal("1.5"),
            ),
        }

    @pytest.fixture
    def loader(self, mock_configs):
        """Create a HolidayPayConfigLoader with mocked configs."""
        with patch("app.services.payroll.holiday_pay_config_loader.get_all_configs", return_value=mock_configs):
            return HolidayPayConfigLoader(year=2025)

    def test_init_loads_configs(self, mock_configs):
        """Test that configs are loaded on initialization."""
        with patch("app.services.payroll.holiday_pay_config_loader.get_all_configs") as mock:
            mock.return_value = mock_configs

            loader = HolidayPayConfigLoader(year=2025)

            mock.assert_called_once_with(2025, None)
            assert "BC" in loader._configs

    def test_init_with_pay_date(self, mock_configs):
        """Test initialization with pay_date."""
        pay_date = date(2025, 9, 15)

        with patch("app.services.payroll.holiday_pay_config_loader.get_all_configs") as mock:
            mock.return_value = mock_configs

            loader = HolidayPayConfigLoader(year=2025, pay_date=pay_date)

            mock.assert_called_once_with(2025, pay_date)

    def test_get_config_returns_province(self, loader):
        """Test getting config for existing province."""
        result = loader.get_config("BC")

        assert result.province_code == "BC"
        assert result.formula_type == "30_day_average"

    def test_get_config_returns_default_for_missing(self, loader):
        """Test getting config for non-existing province returns default."""
        result = loader.get_config("ZZ")

        assert result == DEFAULT_BC_CONFIG

    def test_get_all_configs(self, loader):
        """Test getting all configs."""
        result = loader.get_all_configs()

        assert "BC" in result
        assert "ON" in result

    def test_clear_cache_reloads_configs(self, loader):
        """Test that clear_cache reloads configurations."""
        new_configs = {"AB": MagicMock()}

        with patch("app.services.payroll.holiday_pay_config_loader.clear_cache") as mock_clear, \
             patch("app.services.payroll.holiday_pay_config_loader.get_all_configs") as mock_get:
            mock_get.return_value = new_configs

            loader.clear_cache()

            mock_clear.assert_called_once()
            mock_get.assert_called_once_with(2025, None)


class TestHolidayPayConfigLoaderWithDifferentProvinces:
    """Integration-like tests for different province configurations."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_bc_config_lookback(self):
        """Test BC config uses 30 day lookback."""
        bc_data = {
            "province_code": "BC",
            "formula_type": "30_day_average",
            "formula_params": {
                "lookback_days": 30,
                "method": "total_wages_div_days",
            },
            "eligibility": {"min_employment_days": 30},
        }

        result = _dict_to_config(bc_data)

        assert result.formula_params.lookback_days == 30
        assert result.formula_params.method == "total_wages_div_days"

    def test_ontario_config_with_vacation_pay(self):
        """Test Ontario config includes vacation pay."""
        on_data = {
            "province_code": "ON",
            "formula_type": "4_week_average",
            "formula_params": {
                "lookback_weeks": 4,
                "divisor": 20,
                "include_vacation_pay": True,
            },
            "eligibility": {"require_last_first_rule": True},
        }

        result = _dict_to_config(on_data)

        assert result.formula_params.include_vacation_pay is True
        assert result.eligibility.require_last_first_rule is True

    def test_saskatchewan_5_percent_formula(self):
        """Test Saskatchewan 5% formula configuration."""
        sk_data = {
            "province_code": "SK",
            "formula_type": "5_percent_28_days",
            "formula_params": {
                "percentage": 0.05,
                "lookback_days": 28,
                "include_previous_holiday_pay": True,
                "new_employee_fallback": "pro_rated",
            },
            "eligibility": {"min_employment_days": 0},
        }

        result = _dict_to_config(sk_data)

        assert result.formula_type == "5_percent_28_days"
        assert result.formula_params.percentage == Decimal("0.05")
        assert result.formula_params.include_previous_holiday_pay is True
        assert result.formula_params.new_employee_fallback == "pro_rated"

    def test_alberta_daily_average(self):
        """Test Alberta daily average configuration."""
        ab_data = {
            "province_code": "AB",
            "formula_type": "4_week_average_daily",
            "formula_params": {
                "lookback_weeks": 4,
                "method": "wages_div_days_worked",
            },
            "eligibility": {"min_employment_days": 30},
        }

        result = _dict_to_config(ab_data)

        assert result.formula_type == "4_week_average_daily"
        assert result.formula_params.method == "wages_div_days_worked"

    def test_federal_config(self):
        """Test Federal jurisdiction configuration."""
        federal_data = {
            "province_code": "Federal",
            "formula_type": "20_day_average",
            "formula_params": {
                "lookback_days": 20,
            },
            "eligibility": {"min_employment_days": 30},
            "premium_rate": 1.5,
            "name": "Federal (Canada Labour Code)",
        }

        result = _dict_to_config(federal_data)

        assert result.province_code == "Federal"
        assert result.name == "Federal (Canada Labour Code)"
