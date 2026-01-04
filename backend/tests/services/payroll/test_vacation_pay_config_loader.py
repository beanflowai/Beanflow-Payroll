"""
Tests for vacation_pay_config_loader.py module.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.payroll.vacation_pay_config_loader import (
    VacationTier,
    ProvinceVacationConfig,
    VacationPayConfigLoader,
    DEFAULT_CONFIG,
    _load_json_file,
    _get_available_editions,
    _get_edition_for_date,
    _load_provinces_config,
    _dict_to_config,
    get_config,
    get_all_configs,
    get_minimum_rate,
    get_config_metadata,
    clear_cache,
    calculate_years_of_service,
)


class TestVacationTier:
    """Tests for VacationTier dataclass."""

    def test_creates_tier_with_all_fields(self):
        """Test creating a VacationTier with all fields."""
        tier = VacationTier(
            min_years_of_service=5,
            vacation_weeks=3,
            vacation_rate=Decimal("0.06"),
            notes="3 weeks after 5 years",
        )

        assert tier.min_years_of_service == 5
        assert tier.vacation_weeks == 3
        assert tier.vacation_rate == Decimal("0.06")
        assert tier.notes == "3 weeks after 5 years"

    def test_creates_tier_without_notes(self):
        """Test creating a VacationTier without notes."""
        tier = VacationTier(
            min_years_of_service=0,
            vacation_weeks=2,
            vacation_rate=Decimal("0.04"),
        )

        assert tier.notes is None

    def test_tier_is_frozen(self):
        """Test that VacationTier is immutable."""
        tier = VacationTier(
            min_years_of_service=0,
            vacation_weeks=2,
            vacation_rate=Decimal("0.04"),
        )

        with pytest.raises(AttributeError):
            tier.vacation_weeks = 3


class TestProvinceVacationConfig:
    """Tests for ProvinceVacationConfig dataclass."""

    @pytest.fixture
    def bc_config(self) -> ProvinceVacationConfig:
        """Create a BC config for testing."""
        return ProvinceVacationConfig(
            province_code="BC",
            name="British Columbia",
            tiers=(
                VacationTier(
                    min_years_of_service=0,
                    vacation_weeks=2,
                    vacation_rate=Decimal("0.04"),
                ),
                VacationTier(
                    min_years_of_service=5,
                    vacation_weeks=3,
                    vacation_rate=Decimal("0.06"),
                ),
            ),
            notes="BC vacation pay",
        )

    def test_get_tier_for_years_returns_first_tier(self, bc_config):
        """Test getting first tier for new employee."""
        tier = bc_config.get_tier_for_years(0)

        assert tier.vacation_weeks == 2
        assert tier.vacation_rate == Decimal("0.04")

    def test_get_tier_for_years_returns_second_tier(self, bc_config):
        """Test getting second tier for employee with 5+ years."""
        tier = bc_config.get_tier_for_years(5)

        assert tier.vacation_weeks == 3
        assert tier.vacation_rate == Decimal("0.06")

    def test_get_tier_for_years_returns_highest_applicable(self, bc_config):
        """Test getting highest applicable tier."""
        tier = bc_config.get_tier_for_years(10)

        assert tier.vacation_weeks == 3  # Still 3 weeks, highest available

    def test_get_tier_for_years_mid_range(self, bc_config):
        """Test tier for years between thresholds."""
        tier = bc_config.get_tier_for_years(3)

        assert tier.vacation_weeks == 2  # Still first tier

    def test_get_minimum_rate(self, bc_config):
        """Test getting minimum rate."""
        rate = bc_config.get_minimum_rate(0)
        assert rate == Decimal("0.04")

        rate = bc_config.get_minimum_rate(5)
        assert rate == Decimal("0.06")

    def test_get_minimum_weeks(self, bc_config):
        """Test getting minimum weeks."""
        weeks = bc_config.get_minimum_weeks(0)
        assert weeks == 2

        weeks = bc_config.get_minimum_weeks(5)
        assert weeks == 3


class TestDefaultConfig:
    """Tests for DEFAULT_CONFIG constant."""

    def test_default_config_is_bc(self):
        """Test that default config is BC."""
        assert DEFAULT_CONFIG.province_code == "BC"

    def test_default_config_has_two_tiers(self):
        """Test that default config has two tiers."""
        assert len(DEFAULT_CONFIG.tiers) == 2

    def test_default_config_first_tier(self):
        """Test first tier of default config."""
        tier = DEFAULT_CONFIG.tiers[0]
        assert tier.min_years_of_service == 0
        assert tier.vacation_weeks == 2
        assert tier.vacation_rate == Decimal("0.04")

    def test_default_config_second_tier(self):
        """Test second tier of default config."""
        tier = DEFAULT_CONFIG.tiers[1]
        assert tier.min_years_of_service == 5
        assert tier.vacation_weeks == 3
        assert tier.vacation_rate == Decimal("0.06")


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
        with patch("app.services.payroll.vacation_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
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

        with patch("app.services.payroll.vacation_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _get_available_editions(2025)

            assert len(result) == 2
            assert result[0][0] == "jan"
            assert result[1][0] == "jun"

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

        with patch("app.services.payroll.vacation_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
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
        with patch("app.services.payroll.vacation_pay_config_loader._get_available_editions", return_value=[]):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_first_edition_for_early_date(self):
        """Test that first edition is returned for early dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 5, 31)),
            ("jun", date(2025, 6, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.vacation_pay_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 3, 15))

            assert result == "jan"

    def test_returns_later_edition_for_later_date(self):
        """Test that later edition is returned for later dates."""
        editions = [
            ("jan", date(2025, 1, 1), date(2025, 5, 31)),
            ("jun", date(2025, 6, 1), date(2025, 12, 31)),
        ]

        with patch("app.services.payroll.vacation_pay_config_loader._get_available_editions", return_value=editions):
            result = _get_edition_for_date(2025, date(2025, 7, 15))

            assert result == "jun"


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
        expected = {"provinces": {"BC": {"tiers": []}}}
        config_file.write_text(json.dumps(expected))

        with patch("app.services.payroll.vacation_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == expected

    def test_returns_empty_provinces_for_missing_file(self, tmp_path: Path):
        """Test that empty provinces dict is returned for missing file."""
        with patch("app.services.payroll.vacation_pay_config_loader.CONFIG_BASE_PATH", tmp_path):
            result = _load_provinces_config(2025, "jan")

            assert result == {"provinces": {}}


class TestDictToConfig:
    """Tests for _dict_to_config function."""

    def test_converts_complete_dict(self):
        """Test converting a complete dictionary to ProvinceVacationConfig."""
        province_data = {
            "province_code": "BC",
            "name": "British Columbia",
            "tiers": [
                {
                    "min_years_of_service": 0,
                    "vacation_weeks": 2,
                    "vacation_rate": "0.04",
                    "notes": "2 weeks",
                },
                {
                    "min_years_of_service": 5,
                    "vacation_weeks": 3,
                    "vacation_rate": "0.06",
                },
            ],
            "notes": "BC vacation",
        }

        result = _dict_to_config(province_data)

        assert isinstance(result, ProvinceVacationConfig)
        assert result.province_code == "BC"
        assert result.name == "British Columbia"
        assert len(result.tiers) == 2
        assert result.tiers[0].vacation_rate == Decimal("0.04")
        assert result.notes == "BC vacation"

    def test_sorts_tiers_by_years(self):
        """Test that tiers are sorted by min_years_of_service."""
        province_data = {
            "province_code": "BC",
            "name": "British Columbia",
            "tiers": [
                {"min_years_of_service": 5, "vacation_weeks": 3, "vacation_rate": "0.06"},
                {"min_years_of_service": 0, "vacation_weeks": 2, "vacation_rate": "0.04"},
            ],
        }

        result = _dict_to_config(province_data)

        assert result.tiers[0].min_years_of_service == 0
        assert result.tiers[1].min_years_of_service == 5


class TestGetConfig:
    """Tests for get_config function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_config_for_existing_province(self):
        """Test getting config for an existing province."""
        province_data = {
            "province_code": "BC",
            "name": "British Columbia",
            "tiers": [
                {"min_years_of_service": 0, "vacation_weeks": 2, "vacation_rate": "0.04"},
            ],
        }

        with patch("app.services.payroll.vacation_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.vacation_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": province_data}}

            result = get_config("BC")

            assert result.province_code == "BC"

    def test_returns_default_for_missing_province(self):
        """Test that DEFAULT_CONFIG is returned for missing province."""
        with patch("app.services.payroll.vacation_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.vacation_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {}}

            result = get_config("ZZ")

            assert result == DEFAULT_CONFIG


class TestGetAllConfigs:
    """Tests for get_all_configs function."""

    def setup_method(self):
        """Clear cache before each test."""
        _load_json_file.cache_clear()

    def test_returns_all_configs(self):
        """Test getting all configs."""
        bc_data = {
            "province_code": "BC",
            "name": "British Columbia",
            "tiers": [{"min_years_of_service": 0, "vacation_weeks": 2, "vacation_rate": "0.04"}],
        }
        on_data = {
            "province_code": "ON",
            "name": "Ontario",
            "tiers": [{"min_years_of_service": 0, "vacation_weeks": 2, "vacation_rate": "0.04"}],
        }

        with patch("app.services.payroll.vacation_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.vacation_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = {"provinces": {"BC": bc_data, "ON": on_data}}

            result = get_all_configs()

            assert len(result) == 2
            assert "BC" in result
            assert "ON" in result


class TestGetMinimumRate:
    """Tests for get_minimum_rate function."""

    def test_returns_minimum_rate(self):
        """Test getting minimum rate."""
        config = ProvinceVacationConfig(
            province_code="BC",
            name="BC",
            tiers=(
                VacationTier(min_years_of_service=0, vacation_weeks=2, vacation_rate=Decimal("0.04")),
                VacationTier(min_years_of_service=5, vacation_weeks=3, vacation_rate=Decimal("0.06")),
            ),
        )

        with patch("app.services.payroll.vacation_pay_config_loader.get_config", return_value=config):
            rate = get_minimum_rate("BC", 0)
            assert rate == Decimal("0.04")

            rate = get_minimum_rate("BC", 5)
            assert rate == Decimal("0.06")


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
            "notes": "2025 vacation pay configuration",
        }

        with patch("app.services.payroll.vacation_pay_config_loader._get_edition_for_date", return_value="jan"), \
             patch("app.services.payroll.vacation_pay_config_loader._load_provinces_config") as mock_load:
            mock_load.return_value = config_data

            result = get_config_metadata()

            assert result["year"] == 2025
            assert result["edition"] == "jan"
            assert result["source"] == "Provincial regulations"


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


class TestVacationPayConfigLoader:
    """Tests for VacationPayConfigLoader class."""

    @pytest.fixture
    def mock_configs(self) -> dict[str, ProvinceVacationConfig]:
        """Create mock configs."""
        return {
            "BC": ProvinceVacationConfig(
                province_code="BC",
                name="British Columbia",
                tiers=(
                    VacationTier(min_years_of_service=0, vacation_weeks=2, vacation_rate=Decimal("0.04")),
                    VacationTier(min_years_of_service=5, vacation_weeks=3, vacation_rate=Decimal("0.06")),
                ),
            ),
            "SK": ProvinceVacationConfig(
                province_code="SK",
                name="Saskatchewan",
                tiers=(
                    VacationTier(min_years_of_service=0, vacation_weeks=3, vacation_rate=Decimal("0.0577")),
                    VacationTier(min_years_of_service=10, vacation_weeks=4, vacation_rate=Decimal("0.0769")),
                ),
            ),
        }

    @pytest.fixture
    def loader(self, mock_configs):
        """Create a VacationPayConfigLoader with mocked configs."""
        with patch("app.services.payroll.vacation_pay_config_loader.get_all_configs", return_value=mock_configs):
            return VacationPayConfigLoader(year=2025)

    def test_init_loads_configs(self, mock_configs):
        """Test that configs are loaded on initialization."""
        with patch("app.services.payroll.vacation_pay_config_loader.get_all_configs") as mock:
            mock.return_value = mock_configs

            loader = VacationPayConfigLoader(year=2025)

            mock.assert_called_once_with(2025, None)
            assert "BC" in loader._configs

    def test_get_config_returns_province(self, loader):
        """Test getting config for existing province."""
        result = loader.get_config("BC")

        assert result.province_code == "BC"

    def test_get_config_returns_default_for_missing(self, loader):
        """Test getting config for non-existing province returns default."""
        result = loader.get_config("ZZ")

        assert result == DEFAULT_CONFIG

    def test_get_all_configs(self, loader):
        """Test getting all configs."""
        result = loader.get_all_configs()

        assert "BC" in result
        assert "SK" in result

    def test_get_minimum_rate(self, loader):
        """Test getting minimum rate."""
        rate = loader.get_minimum_rate("BC", 0)
        assert rate == Decimal("0.04")

        rate = loader.get_minimum_rate("SK", 0)
        assert rate == Decimal("0.0577")

    def test_get_effective_rate_without_override(self, loader):
        """Test getting effective rate without override."""
        rate = loader.get_effective_rate("BC", 0)

        assert rate == Decimal("0.04")

    def test_get_effective_rate_with_valid_override(self, loader):
        """Test getting effective rate with valid override."""
        rate = loader.get_effective_rate("BC", 0, override=Decimal("0.08"))

        assert rate == Decimal("0.08")

    def test_get_effective_rate_rejects_low_override(self, loader):
        """Test that override below minimum raises ValueError."""
        with pytest.raises(ValueError, match="below provincial minimum"):
            loader.get_effective_rate("BC", 0, override=Decimal("0.02"))

    def test_get_effective_rate_with_equal_override(self, loader):
        """Test that override equal to minimum is accepted."""
        rate = loader.get_effective_rate("BC", 0, override=Decimal("0.04"))

        assert rate == Decimal("0.04")

    def test_clear_cache_reloads_configs(self, loader):
        """Test that clear_cache reloads configurations."""
        new_configs = {"ON": MagicMock()}

        with patch("app.services.payroll.vacation_pay_config_loader.clear_cache") as mock_clear, \
             patch("app.services.payroll.vacation_pay_config_loader.get_all_configs") as mock_get:
            mock_get.return_value = new_configs

            loader.clear_cache()

            mock_clear.assert_called_once()
            mock_get.assert_called_once_with(2025, None)


class TestCalculateYearsOfService:
    """Tests for calculate_years_of_service function."""

    def test_calculates_full_years(self):
        """Test calculating complete years of service."""
        hire_date = date(2020, 3, 15)
        reference_date = date(2025, 6, 15)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 5

    def test_adjusts_for_incomplete_year(self):
        """Test that incomplete year is not counted."""
        hire_date = date(2020, 6, 15)
        reference_date = date(2025, 3, 15)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 4  # Not yet 5 years

    def test_same_day_anniversary(self):
        """Test on anniversary day."""
        hire_date = date(2020, 3, 15)
        reference_date = date(2025, 3, 15)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 5

    def test_one_day_before_anniversary(self):
        """Test one day before anniversary."""
        hire_date = date(2020, 3, 15)
        reference_date = date(2025, 3, 14)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 4

    def test_uses_today_when_no_reference_date(self):
        """Test that today is used when reference_date is None."""
        # This test might be flaky based on current date
        # Use a hire date far in the past
        hire_date = date(2010, 1, 1)

        result = calculate_years_of_service(hire_date)

        # Should be at least 14 years (assuming test runs in 2024 or later)
        assert result >= 14

    def test_returns_zero_for_future_hire(self):
        """Test that 0 is returned for future hire date."""
        hire_date = date(2030, 1, 1)
        reference_date = date(2025, 6, 15)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 0

    def test_returns_zero_for_same_year(self):
        """Test 0 years for employee hired same year."""
        hire_date = date(2025, 1, 15)
        reference_date = date(2025, 6, 15)

        result = calculate_years_of_service(hire_date, reference_date)

        assert result == 0

    def test_leap_year_handling(self):
        """Test handling of leap year birthdays."""
        # Hired on Feb 29 in a leap year
        hire_date = date(2020, 2, 29)

        # Check on Mar 1 of next year (not a leap year)
        reference_date = date(2021, 3, 1)
        result = calculate_years_of_service(hire_date, reference_date)
        assert result == 1

        # Check on Feb 28 of next year
        reference_date = date(2021, 2, 28)
        result = calculate_years_of_service(hire_date, reference_date)
        assert result == 0  # Before anniversary
