"""
Tests for tax_tables.py module.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, mock_open

import pytest

from app.services.payroll.tax_tables import (
    TaxConfigError,
    SUPPORTED_PROVINCES,
    _load_json_file,
    _get_config_path,
    _get_july_cutoff,
    _get_federal_config_with_edition,
    get_federal_config,
    get_cpp_config,
    get_ei_config,
    _get_provinces_config_with_edition,
    get_province_config,
    get_all_provinces,
    find_tax_bracket,
    calculate_dynamic_bpa,
    _calculate_bpa_manitoba,
    _calculate_bpa_nova_scotia,
    validate_config_schema,
    _has_versioned_federal_config,
    _has_versioned_provinces_config,
    validate_tax_tables,
)


class TestConstants:
    """Tests for module constants."""

    def test_supported_provinces_count(self):
        """Test that SUPPORTED_PROVINCES contains 12 provinces."""
        assert len(SUPPORTED_PROVINCES) == 12

    def test_supported_provinces_excludes_quebec(self):
        """Test that Quebec is excluded from supported provinces."""
        assert "QC" not in SUPPORTED_PROVINCES

    def test_supported_provinces_includes_all_others(self):
        """Test that all other provinces/territories are included."""
        expected = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"}
        assert SUPPORTED_PROVINCES == expected


class TestLoadJsonFile:
    """Tests for _load_json_file function."""

    def setup_method(self):
        """Clear LRU cache before each test."""
        _load_json_file.cache_clear()

    def test_raises_error_for_missing_file(self, tmp_path: Path):
        """Test that missing file raises TaxConfigError."""
        missing_path = tmp_path / "nonexistent.json"

        with pytest.raises(TaxConfigError, match="Tax configuration file not found"):
            _load_json_file(str(missing_path))

    def test_raises_error_for_invalid_json(self, tmp_path: Path):
        """Test that invalid JSON raises TaxConfigError."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")

        with pytest.raises(TaxConfigError, match="Invalid JSON"):
            _load_json_file(str(invalid_file))

    def test_loads_valid_json_file(self, tmp_path: Path):
        """Test loading a valid JSON file."""
        valid_file = tmp_path / "valid.json"
        expected_data = {"key": "value", "number": 123}
        valid_file.write_text(json.dumps(expected_data))

        result = _load_json_file(str(valid_file))

        assert result == expected_data

    def test_caches_file_content(self, tmp_path: Path):
        """Test that file content is cached."""
        valid_file = tmp_path / "cached.json"
        valid_file.write_text('{"cached": true}')

        # First call
        result1 = _load_json_file(str(valid_file))
        # Modify file
        valid_file.write_text('{"cached": false}')
        # Second call should return cached value
        result2 = _load_json_file(str(valid_file))

        assert result1 == result2
        assert result1 == {"cached": True}


class TestGetConfigPath:
    """Tests for _get_config_path function."""

    def test_returns_correct_path(self):
        """Test that correct path is returned for year and filename."""
        path = _get_config_path(2025, "federal.json")

        assert path.name == "federal.json"
        assert "2025" in str(path)
        assert "tax_tables" in str(path)

    def test_works_with_different_years(self):
        """Test that path changes with year."""
        path_2025 = _get_config_path(2025, "cpp_ei.json")
        path_2026 = _get_config_path(2026, "cpp_ei.json")

        assert "2025" in str(path_2025)
        assert "2026" in str(path_2026)
        assert path_2025 != path_2026


class TestGetJulyCutoff:
    """Tests for _get_july_cutoff function."""

    def test_returns_july_first(self):
        """Test that July 1st is returned for given year."""
        result = _get_july_cutoff(2025)

        assert result == date(2025, 7, 1)

    def test_works_with_different_years(self):
        """Test that correct date is returned for various years."""
        assert _get_july_cutoff(2024) == date(2024, 7, 1)
        assert _get_july_cutoff(2026) == date(2026, 7, 1)


class TestGetFederalConfig:
    """Tests for get_federal_config function."""

    def setup_method(self):
        """Clear caches before each test."""
        _load_json_file.cache_clear()

    def test_uses_july_edition_by_default(self):
        """Test that July edition is used when no pay_date specified."""
        with patch("app.services.payroll.tax_tables._get_federal_config_with_edition") as mock:
            mock.return_value = {"bpaf": 16129}

            get_federal_config(2025)

            mock.assert_called_once_with(2025, "jul")

    def test_uses_jan_edition_before_july(self):
        """Test that January edition is used for dates before July 1."""
        with patch("app.services.payroll.tax_tables._get_federal_config_with_edition") as mock:
            mock.return_value = {"bpaf": 15705}

            get_federal_config(2025, pay_date=date(2025, 3, 15))

            mock.assert_called_once_with(2025, "jan")

    def test_uses_jul_edition_from_july_onwards(self):
        """Test that July edition is used from July 1 onwards."""
        with patch("app.services.payroll.tax_tables._get_federal_config_with_edition") as mock:
            mock.return_value = {"bpaf": 16129}

            get_federal_config(2025, pay_date=date(2025, 7, 1))

            mock.assert_called_once_with(2025, "jul")

    def test_uses_jul_edition_after_july(self):
        """Test that July edition is used for dates after July 1."""
        with patch("app.services.payroll.tax_tables._get_federal_config_with_edition") as mock:
            mock.return_value = {"bpaf": 16129}

            get_federal_config(2025, pay_date=date(2025, 9, 15))

            mock.assert_called_once_with(2025, "jul")


class TestGetFederalConfigWithEdition:
    """Tests for _get_federal_config_with_edition function."""

    def setup_method(self):
        """Clear caches before each test."""
        _load_json_file.cache_clear()

    def test_loads_versioned_file_when_exists(self, tmp_path: Path):
        """Test that versioned file is loaded when it exists."""
        with patch("app.services.payroll.tax_tables._get_config_path") as mock_path:
            versioned_file = tmp_path / "federal_jan.json"
            versioned_file.write_text('{"bpaf": 15705}')
            mock_path.return_value = versioned_file

            result = _get_federal_config_with_edition(2025, "jan")

            assert result == {"bpaf": 15705}

    def test_falls_back_to_single_file(self, tmp_path: Path):
        """Test that single file is used when versioned doesn't exist."""
        versioned_file = tmp_path / "federal_jan.json"  # Doesn't exist
        single_file = tmp_path / "federal.json"
        single_file.write_text('{"bpaf": 16000}')

        call_count = 0

        def side_effect(year: int, filename: str) -> Path:
            nonlocal call_count
            call_count += 1
            if "jan" in filename:
                return versioned_file
            return single_file

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _get_federal_config_with_edition(2025, "jan")

            assert result == {"bpaf": 16000}

    def test_raises_error_when_no_config_found(self, tmp_path: Path):
        """Test that error is raised when no config file exists."""
        missing_versioned = tmp_path / "federal_jan.json"
        missing_single = tmp_path / "federal.json"

        call_count = 0

        def side_effect(year: int, filename: str) -> Path:
            nonlocal call_count
            call_count += 1
            if "jan" in filename:
                return missing_versioned
            return missing_single

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            with pytest.raises(TaxConfigError, match="No federal config found"):
                _get_federal_config_with_edition(2025, "jan")


class TestGetCppConfig:
    """Tests for get_cpp_config function."""

    def setup_method(self):
        """Clear caches before each test."""
        get_cpp_config.cache_clear()
        _load_json_file.cache_clear()

    def test_returns_cpp_section(self, tmp_path: Path):
        """Test that CPP section is extracted from config file."""
        config_data = {
            "cpp": {"ympe": 71300, "basic_exemption": 3500},
            "ei": {"mie": 65700}
        }
        config_file = tmp_path / "cpp_ei.json"
        config_file.write_text(json.dumps(config_data))

        with patch("app.services.payroll.tax_tables._get_config_path", return_value=config_file):
            result = get_cpp_config(2025)

            assert result == {"ympe": 71300, "basic_exemption": 3500}


class TestGetEiConfig:
    """Tests for get_ei_config function."""

    def setup_method(self):
        """Clear caches before each test."""
        get_ei_config.cache_clear()
        _load_json_file.cache_clear()

    def test_returns_ei_section(self, tmp_path: Path):
        """Test that EI section is extracted from config file."""
        config_data = {
            "cpp": {"ympe": 71300},
            "ei": {"mie": 65700, "employee_rate": 0.0163}
        }
        config_file = tmp_path / "cpp_ei.json"
        config_file.write_text(json.dumps(config_data))

        with patch("app.services.payroll.tax_tables._get_config_path", return_value=config_file):
            result = get_ei_config(2025)

            assert result == {"mie": 65700, "employee_rate": 0.0163}


class TestGetProvincesConfigWithEdition:
    """Tests for _get_provinces_config_with_edition function."""

    def setup_method(self):
        """Clear caches before each test."""
        _get_provinces_config_with_edition.cache_clear()
        _load_json_file.cache_clear()

    def test_loads_versioned_file_when_exists(self, tmp_path: Path):
        """Test that versioned provinces file is loaded."""
        config_data = {"provinces": {"ON": {"bpa": 12747}, "BC": {"bpa": 12932}}}
        versioned_file = tmp_path / "provinces_jul.json"
        versioned_file.write_text(json.dumps(config_data))

        with patch("app.services.payroll.tax_tables._get_config_path", return_value=versioned_file):
            result = _get_provinces_config_with_edition(2025, "jul")

            assert result == {"ON": {"bpa": 12747}, "BC": {"bpa": 12932}}

    def test_falls_back_to_single_file(self, tmp_path: Path):
        """Test fallback to single provinces.json file."""
        versioned_file = tmp_path / "provinces_jul.json"  # Doesn't exist
        single_file = tmp_path / "provinces.json"
        single_file.write_text('{"provinces": {"ON": {"bpa": 12000}}}')

        def side_effect(year: int, filename: str) -> Path:
            if "jul" in filename:
                return versioned_file
            return single_file

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _get_provinces_config_with_edition(2025, "jul")

            assert result == {"ON": {"bpa": 12000}}

    def test_raises_error_when_no_config_found(self, tmp_path: Path):
        """Test error when no provinces config exists."""
        missing_versioned = tmp_path / "provinces_jul.json"
        missing_single = tmp_path / "provinces.json"

        def side_effect(year: int, filename: str) -> Path:
            if "jul" in filename:
                return missing_versioned
            return missing_single

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            with pytest.raises(TaxConfigError, match="No provinces config found"):
                _get_provinces_config_with_edition(2025, "jul")


class TestGetProvinceConfig:
    """Tests for get_province_config function."""

    def setup_method(self):
        """Clear caches before each test."""
        _get_provinces_config_with_edition.cache_clear()
        _load_json_file.cache_clear()

    def test_raises_error_for_unsupported_province(self):
        """Test that unsupported province raises error."""
        with pytest.raises(TaxConfigError, match="Province 'QC' not supported"):
            get_province_config("QC")

    def test_normalizes_province_code_to_uppercase(self):
        """Test that province code is normalized to uppercase."""
        with patch("app.services.payroll.tax_tables._get_provinces_config_with_edition") as mock:
            mock.return_value = {"ON": {"bpa": 12747}}

            result = get_province_config("on")  # lowercase

            assert result == {"bpa": 12747}

    def test_uses_july_edition_by_default(self):
        """Test that July edition is used by default."""
        with patch("app.services.payroll.tax_tables._get_provinces_config_with_edition") as mock:
            mock.return_value = {"ON": {"bpa": 12747}}

            get_province_config("ON", 2025)

            mock.assert_called_once_with(2025, "jul")

    def test_uses_jan_edition_before_july(self):
        """Test that January edition is used for dates before July 1."""
        with patch("app.services.payroll.tax_tables._get_provinces_config_with_edition") as mock:
            mock.return_value = {"ON": {"bpa": 11865}}

            get_province_config("ON", 2025, pay_date=date(2025, 3, 15))

            mock.assert_called_once_with(2025, "jan")

    def test_raises_error_when_province_not_in_config(self):
        """Test error when province exists in SUPPORTED but not in config file."""
        with patch("app.services.payroll.tax_tables._get_provinces_config_with_edition") as mock:
            mock.return_value = {"BC": {"bpa": 12932}}  # ON not in config

            with pytest.raises(TaxConfigError, match="Province 'ON' not found"):
                get_province_config("ON", 2025)


class TestGetAllProvinces:
    """Tests for get_all_provinces function."""

    def test_returns_sorted_list(self):
        """Test that provinces are returned in sorted order."""
        result = get_all_provinces()

        assert result == sorted(result)

    def test_returns_12_provinces(self):
        """Test that 12 provinces are returned."""
        result = get_all_provinces()

        assert len(result) == 12


class TestFindTaxBracket:
    """Tests for find_tax_bracket function."""

    def test_finds_first_bracket_for_low_income(self):
        """Test finding first bracket for low income."""
        brackets = [
            {"threshold": 0, "rate": 0.15, "constant": 0},
            {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
        ]

        rate, constant = find_tax_bracket(Decimal("30000"), brackets)

        assert rate == Decimal("0.15")
        assert constant == Decimal("0")

    def test_finds_second_bracket_for_mid_income(self):
        """Test finding second bracket for mid income."""
        brackets = [
            {"threshold": 0, "rate": 0.15, "constant": 0},
            {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
            {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
        ]

        rate, constant = find_tax_bracket(Decimal("75000"), brackets)

        assert rate == Decimal("0.205")
        assert constant == Decimal("3155.63")

    def test_finds_last_bracket_for_high_income(self):
        """Test finding last bracket for high income."""
        brackets = [
            {"threshold": 0, "rate": 0.15, "constant": 0},
            {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
            {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
        ]

        rate, constant = find_tax_bracket(Decimal("500000"), brackets)

        assert rate == Decimal("0.26")
        assert constant == Decimal("9252.65")

    def test_handles_float_input(self):
        """Test that float input is converted to Decimal."""
        brackets = [
            {"threshold": 0, "rate": 0.15, "constant": 0},
        ]

        rate, constant = find_tax_bracket(50000.50, brackets)

        assert isinstance(rate, Decimal)
        assert isinstance(constant, Decimal)

    def test_handles_exact_threshold(self):
        """Test income exactly at threshold uses that bracket."""
        brackets = [
            {"threshold": 0, "rate": 0.15, "constant": 0},
            {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
        ]

        rate, constant = find_tax_bracket(Decimal("55867"), brackets)

        assert rate == Decimal("0.205")


class TestCalculateDynamicBpa:
    """Tests for calculate_dynamic_bpa function."""

    def test_returns_static_bpa_when_not_dynamic(self):
        """Test static BPA is returned for non-dynamic provinces."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock:
            mock.return_value = {"bpa": 12747, "bpa_is_dynamic": False}

            result = calculate_dynamic_bpa("ON", Decimal("60000"))

            assert result == Decimal("12747")

    def test_returns_static_bpa_when_flag_missing(self):
        """Test static BPA is returned when dynamic flag is missing."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock:
            mock.return_value = {"bpa": 12747}

            result = calculate_dynamic_bpa("ON", Decimal("60000"))

            assert result == Decimal("12747")

    def test_calls_manitoba_calculation(self):
        """Test Manitoba dynamic BPA calculation is called."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock_config, \
             patch("app.services.payroll.tax_tables._calculate_bpa_manitoba") as mock_calc:
            mock_config.return_value = {
                "bpa": 15591,
                "bpa_is_dynamic": True,
                "dynamic_bpa_type": "income_based_reduction",
                "dynamic_bpa_config": {"base_bpa": 15591}
            }
            mock_calc.return_value = Decimal("10000")

            result = calculate_dynamic_bpa("MB", Decimal("300000"))

            mock_calc.assert_called_once()
            assert result == Decimal("10000")

    def test_calls_nova_scotia_calculation(self):
        """Test Nova Scotia dynamic BPA calculation is called."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock_config, \
             patch("app.services.payroll.tax_tables._calculate_bpa_nova_scotia") as mock_calc:
            mock_config.return_value = {
                "bpa": 11744,
                "bpa_is_dynamic": True,
                "dynamic_bpa_type": "income_based_increase",
                "dynamic_bpa_config": {"base_bpa": 11744}
            }
            mock_calc.return_value = Decimal("13500")

            result = calculate_dynamic_bpa("NS", Decimal("50000"))

            mock_calc.assert_called_once()
            assert result == Decimal("13500")

    def test_yukon_follows_federal(self):
        """Test Yukon BPA follows federal BPA."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock_config, \
             patch("app.services.payroll.tax_tables.get_federal_config") as mock_federal:
            mock_config.return_value = {
                "bpa": 16129,
                "bpa_is_dynamic": True,
                "dynamic_bpa_type": "follows_federal",
            }
            mock_federal.return_value = {"bpaf": 16129}

            result = calculate_dynamic_bpa("YT", Decimal("80000"))

            assert result == Decimal("16129")

    def test_normalizes_province_code(self):
        """Test province code is normalized to uppercase."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock:
            mock.return_value = {"bpa": 12747}

            calculate_dynamic_bpa("on", Decimal("50000"))

            # get_province_config should be called with uppercase
            mock.assert_called_once()


class TestCalculateBpaManitoba:
    """Tests for _calculate_bpa_manitoba function."""

    def test_returns_base_bpa_below_reduction_start(self):
        """Test full BPA for income below reduction threshold."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        result = _calculate_bpa_manitoba(Decimal("150000"), config)

        assert result == Decimal("15591")

    def test_returns_base_bpa_at_reduction_start(self):
        """Test full BPA at exactly reduction start threshold."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        result = _calculate_bpa_manitoba(Decimal("200000"), config)

        assert result == Decimal("15591")

    def test_returns_min_bpa_above_reduction_end(self):
        """Test minimum BPA for income above reduction end."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        result = _calculate_bpa_manitoba(Decimal("500000"), config)

        assert result == Decimal("0")

    def test_returns_min_bpa_at_reduction_end(self):
        """Test minimum BPA at exactly reduction end threshold."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        result = _calculate_bpa_manitoba(Decimal("400000"), config)

        assert result == Decimal("0")

    def test_linear_reduction_in_middle(self):
        """Test linear reduction in middle of range."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        # At $300,000 (midpoint), BPA should be half of base
        result = _calculate_bpa_manitoba(Decimal("300000"), config)

        expected = Decimal("15591") / 2
        assert result == expected

    def test_handles_float_input(self):
        """Test that float input is handled correctly."""
        config = {
            "base_bpa": "15591",
            "reduction_start": "200000",
            "reduction_end": "400000",
            "min_bpa": "0"
        }

        result = _calculate_bpa_manitoba(150000.0, config)

        assert result == Decimal("15591")


class TestCalculateBpaNovascotia:
    """Tests for _calculate_bpa_nova_scotia function."""

    def test_returns_base_bpa_below_increase_start(self):
        """Test base BPA for income below increase threshold."""
        config = {
            "base_bpa": "11744",
            "increase_start": "25000",
            "increase_end": "75000",
            "increase_rate": "0.06",
            "max_bpa": "14744"
        }

        result = _calculate_bpa_nova_scotia(Decimal("20000"), config)

        assert result == Decimal("11744")

    def test_returns_base_bpa_at_increase_start(self):
        """Test base BPA at exactly increase start threshold."""
        config = {
            "base_bpa": "11744",
            "increase_start": "25000",
            "increase_end": "75000",
            "increase_rate": "0.06",
            "max_bpa": "14744"
        }

        result = _calculate_bpa_nova_scotia(Decimal("25000"), config)

        assert result == Decimal("11744")

    def test_returns_max_bpa_above_increase_end(self):
        """Test max BPA for income above increase end."""
        config = {
            "base_bpa": "11744",
            "increase_start": "25000",
            "increase_end": "75000",
            "increase_rate": "0.06",
            "max_bpa": "14744"
        }

        result = _calculate_bpa_nova_scotia(Decimal("100000"), config)

        assert result == Decimal("14744")

    def test_returns_max_bpa_at_increase_end(self):
        """Test max BPA at exactly increase end threshold."""
        config = {
            "base_bpa": "11744",
            "increase_start": "25000",
            "increase_end": "75000",
            "increase_rate": "0.06",
            "max_bpa": "14744"
        }

        result = _calculate_bpa_nova_scotia(Decimal("75000"), config)

        assert result == Decimal("14744")

    def test_linear_increase_in_middle(self):
        """Test linear increase in middle of range."""
        config = {
            "base_bpa": "11744",
            "increase_start": "25000",
            "increase_end": "75000",
            "increase_rate": "0.06",
            "max_bpa": "14744"
        }

        # At $50,000: 11744 + (50000-25000) * 0.06 = 11744 + 1500 = 13244
        result = _calculate_bpa_nova_scotia(Decimal("50000"), config)

        assert result == Decimal("13244")


class TestHasVersionedFederalConfig:
    """Tests for _has_versioned_federal_config function."""

    def test_returns_true_when_both_files_exist(self, tmp_path: Path):
        """Test returns True when both jan and jul files exist."""
        jan_file = tmp_path / "federal_jan.json"
        jul_file = tmp_path / "federal_jul.json"
        jan_file.write_text("{}")
        jul_file.write_text("{}")

        call_count = 0

        def side_effect(year: int, filename: str) -> Path:
            nonlocal call_count
            call_count += 1
            if "jan" in filename:
                return jan_file
            return jul_file

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _has_versioned_federal_config(2025)

            assert result is True

    def test_returns_false_when_jan_missing(self, tmp_path: Path):
        """Test returns False when jan file is missing."""
        missing_jan = tmp_path / "federal_jan.json"  # Doesn't exist
        jul_file = tmp_path / "federal_jul.json"
        jul_file.write_text("{}")

        def side_effect(year: int, filename: str) -> Path:
            if "jan" in filename:
                return missing_jan
            return jul_file

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _has_versioned_federal_config(2025)

            assert result is False

    def test_returns_false_when_jul_missing(self, tmp_path: Path):
        """Test returns False when jul file is missing."""
        jan_file = tmp_path / "federal_jan.json"
        missing_jul = tmp_path / "federal_jul.json"  # Doesn't exist
        jan_file.write_text("{}")

        def side_effect(year: int, filename: str) -> Path:
            if "jan" in filename:
                return jan_file
            return missing_jul

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _has_versioned_federal_config(2025)

            assert result is False


class TestHasVersionedProvincesConfig:
    """Tests for _has_versioned_provinces_config function."""

    def test_returns_true_when_both_files_exist(self, tmp_path: Path):
        """Test returns True when both jan and jul files exist."""
        jan_file = tmp_path / "provinces_jan.json"
        jul_file = tmp_path / "provinces_jul.json"
        jan_file.write_text("{}")
        jul_file.write_text("{}")

        def side_effect(year: int, filename: str) -> Path:
            if "jan" in filename:
                return jan_file
            return jul_file

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _has_versioned_provinces_config(2025)

            assert result is True

    def test_returns_false_when_files_missing(self, tmp_path: Path):
        """Test returns False when files are missing."""
        missing_jan = tmp_path / "provinces_jan.json"
        missing_jul = tmp_path / "provinces_jul.json"

        def side_effect(year: int, filename: str) -> Path:
            if "jan" in filename:
                return missing_jan
            return missing_jul

        with patch("app.services.payroll.tax_tables._get_config_path", side_effect=side_effect):
            result = _has_versioned_provinces_config(2025)

            assert result is False


class TestValidateConfigSchema:
    """Tests for validate_config_schema function."""

    def test_returns_error_when_jsonschema_not_installed(self):
        """Test error when jsonschema is not installed."""
        with patch.dict("sys.modules", {"jsonschema": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                # This simulates jsonschema not being installed
                errors = validate_config_schema(2025)

                # The function catches ImportError and adds an error message
                assert any("jsonschema" in str(e) for e in errors)


class TestValidateTaxTables:
    """Tests for validate_tax_tables function."""

    def setup_method(self):
        """Clear caches before each test."""
        _load_json_file.cache_clear()
        get_cpp_config.cache_clear()
        get_ei_config.cache_clear()
        _get_provinces_config_with_edition.cache_clear()

    def test_validates_federal_config_with_versioned_files(self):
        """Test validation with versioned federal files."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }
        cpp_ei_config = {
            "cpp": {"ympe": 71300},
            "ei": {"mie": 65700}
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=True), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value=cpp_ei_config["cpp"]), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value=cpp_ei_config["ei"]), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            # Should have no critical errors
            assert not any("missing 'bpaf'" in e for e in errors)

    def test_detects_missing_bpaf(self):
        """Test detection of missing bpaf in federal config."""
        federal_config = {
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }
        cpp_ei_config = {
            "cpp": {"ympe": 71300},
            "ei": {"mie": 65700}
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value=cpp_ei_config["cpp"]), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value=cpp_ei_config["ei"]), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("missing 'bpaf'" in e for e in errors)

    def test_detects_wrong_bracket_count(self):
        """Test detection of wrong bracket count in federal config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
            ]  # Only 2 brackets instead of 5
        }
        cpp_ei_config = {
            "cpp": {"ympe": 71300},
            "ei": {"mie": 65700}
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value=cpp_ei_config["cpp"]), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value=cpp_ei_config["ei"]), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("should have 5 brackets" in e for e in errors)

    def test_detects_missing_ympe_in_cpp(self):
        """Test detection of missing ympe in CPP config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("CPP missing 'ympe'" in e for e in errors)

    def test_detects_missing_mie_in_ei(self):
        """Test detection of missing mie in EI config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("EI missing 'mie'" in e for e in errors)

    def test_detects_province_missing_brackets(self):
        """Test detection of missing brackets in province config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            # Province config missing brackets
            mock_province.return_value = {"bpa": 12747}

            errors = validate_tax_tables(2025)

            assert any("missing 'brackets'" in e for e in errors)

    def test_detects_province_missing_bpa(self):
        """Test detection of missing BPA in province config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            # Province config missing bpa
            mock_province.return_value = {
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("missing 'bpa'" in e for e in errors)

    def test_detects_brackets_not_in_order(self):
        """Test detection of brackets not in ascending order."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            # Brackets not in ascending order
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [
                    {"threshold": 100000, "rate": 0.10},
                    {"threshold": 0, "rate": 0.05},  # Out of order
                ]
            }

            errors = validate_tax_tables(2025)

            assert any("not in ascending order" in e for e in errors)

    def test_detects_first_bracket_not_starting_at_zero(self):
        """Test detection of first bracket not starting at zero."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            # First bracket doesn't start at 0
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [
                    {"threshold": 10000, "rate": 0.05},  # Starts at 10000, not 0
                    {"threshold": 50000, "rate": 0.10},
                ]
            }

            errors = validate_tax_tables(2025)

            assert any("first bracket must start at 0" in e for e in errors)

    def test_handles_tax_config_error(self):
        """Test handling of TaxConfigError during validation."""
        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config") as mock_federal, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_federal.side_effect = TaxConfigError("Test error")

            errors = validate_tax_tables(2025)

            assert any("Test error" in e for e in errors)

    def test_handles_cpp_ei_tax_config_error(self):
        """Test handling of TaxConfigError during CPP/EI validation."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config") as mock_cpp, \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_cpp.side_effect = TaxConfigError("CPP error")
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": [{"threshold": 0, "rate": 0.05}]
            }

            errors = validate_tax_tables(2025)

            assert any("CPP/EI config error" in e for e in errors)

    def test_detects_empty_brackets(self):
        """Test detection of empty brackets list in province config."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            # Empty brackets list
            mock_province.return_value = {
                "bpa": 12747,
                "brackets": []
            }

            errors = validate_tax_tables(2025)

            assert any("empty brackets list" in e for e in errors)

    def test_handles_province_tax_config_error(self):
        """Test handling of TaxConfigError during province validation."""
        federal_config = {
            "bpaf": 16129,
            "brackets": [
                {"threshold": 0, "rate": 0.15, "constant": 0},
                {"threshold": 55867, "rate": 0.205, "constant": 3155.63},
                {"threshold": 111733, "rate": 0.26, "constant": 9252.65},
                {"threshold": 173205, "rate": 0.29, "constant": 14452.88},
                {"threshold": 246752, "rate": 0.33, "constant": 24322.90},
            ]
        }

        with patch("app.services.payroll.tax_tables._has_versioned_federal_config", return_value=False), \
             patch("app.services.payroll.tax_tables._has_versioned_provinces_config", return_value=False), \
             patch("app.services.payroll.tax_tables.get_federal_config", return_value=federal_config), \
             patch("app.services.payroll.tax_tables.get_cpp_config", return_value={"ympe": 71300}), \
             patch("app.services.payroll.tax_tables.get_ei_config", return_value={"mie": 65700}), \
             patch("app.services.payroll.tax_tables.get_province_config") as mock_province, \
             patch("app.services.payroll.tax_tables.validate_config_schema", return_value=[]):
            mock_province.side_effect = TaxConfigError("Province error")

            errors = validate_tax_tables(2025)

            assert any("Province error" in e for e in errors)


class TestCalculateDynamicBpaFallback:
    """Additional tests for calculate_dynamic_bpa fallback path."""

    def test_fallback_to_static_bpa_unknown_dynamic_type(self):
        """Test fallback to static BPA when dynamic type is unknown."""
        with patch("app.services.payroll.tax_tables.get_province_config") as mock:
            mock.return_value = {
                "bpa": 10000,
                "bpa_is_dynamic": True,
                "dynamic_bpa_type": "unknown_type",  # Unknown type
                "dynamic_bpa_config": {}
            }

            result = calculate_dynamic_bpa("ON", Decimal("50000"))

            assert result == Decimal("10000")


class TestValidateConfigSchemaFullPath:
    """Additional tests for validate_config_schema function."""

    def setup_method(self):
        """Clear caches before each test."""
        _load_json_file.cache_clear()

    def test_validates_with_jsonschema_when_available(self, tmp_path: Path):
        """Test validation path when jsonschema is available."""
        # Create valid schema files
        cpp_ei_schema = tmp_path / "cpp_ei.schema.json"
        cpp_ei_schema.write_text('{"type": "object"}')

        federal_schema = tmp_path / "federal.schema.json"
        federal_schema.write_text('{"type": "object"}')

        provinces_schema = tmp_path / "provinces.schema.json"
        provinces_schema.write_text('{"type": "object"}')

        # Create valid config files
        cpp_ei_config = tmp_path / "cpp_ei.json"
        cpp_ei_config.write_text('{"cpp": {}, "ei": {}}')

        federal_config = tmp_path / "federal.json"
        federal_config.write_text('{"bpaf": 16129, "brackets": []}')

        provinces_config = tmp_path / "provinces.json"
        provinces_config.write_text('{"provinces": {}}')

        call_count = [0]
        def path_side_effect(year: int, filename: str) -> Path:
            call_count[0] += 1
            if "cpp_ei" in filename:
                return cpp_ei_config
            elif "provinces" in filename:
                return provinces_config
            return federal_config

        with patch("app.services.payroll.tax_tables.SCHEMA_BASE_PATH", tmp_path), \
             patch("app.services.payroll.tax_tables._get_config_path", side_effect=path_side_effect):
            errors = validate_config_schema(2025)

            # Should have no jsonschema errors
            assert not any("jsonschema" in e for e in errors)

    def test_detects_missing_schema_file(self, tmp_path: Path):
        """Test detection of missing schema file."""
        # Don't create any schema files
        config_file = tmp_path / "federal.json"
        config_file.write_text('{"bpaf": 16129}')

        with patch("app.services.payroll.tax_tables.SCHEMA_BASE_PATH", tmp_path), \
             patch("app.services.payroll.tax_tables._get_config_path", return_value=config_file):
            errors = validate_config_schema(2025)

            assert any("Schema file not found" in e for e in errors)

    def test_detects_invalid_json_in_schema(self, tmp_path: Path):
        """Test detection of invalid JSON in schema file."""
        # Create invalid schema
        federal_schema = tmp_path / "federal.schema.json"
        federal_schema.write_text('{invalid json}')

        # Create valid other schemas
        cpp_ei_schema = tmp_path / "cpp_ei.schema.json"
        cpp_ei_schema.write_text('{"type": "object"}')
        provinces_schema = tmp_path / "provinces.schema.json"
        provinces_schema.write_text('{"type": "object"}')

        # Create valid config file
        config_file = tmp_path / "federal.json"
        config_file.write_text('{"bpaf": 16129}')

        with patch("app.services.payroll.tax_tables.SCHEMA_BASE_PATH", tmp_path), \
             patch("app.services.payroll.tax_tables._get_config_path", return_value=config_file):
            errors = validate_config_schema(2025)

            assert any("Invalid JSON in schema federal.schema.json" in e for e in errors)

    def test_detects_invalid_json_in_config(self, tmp_path: Path):
        """Test detection of invalid JSON in config file."""
        # Create valid schemas
        cpp_ei_schema = tmp_path / "cpp_ei.schema.json"
        cpp_ei_schema.write_text('{"type": "object"}')
        federal_schema = tmp_path / "federal.schema.json"
        federal_schema.write_text('{"type": "object"}')
        provinces_schema = tmp_path / "provinces.schema.json"
        provinces_schema.write_text('{"type": "object"}')

        # Create invalid config
        config_file = tmp_path / "cpp_ei.json"
        config_file.write_text('{invalid json}')

        with patch("app.services.payroll.tax_tables.SCHEMA_BASE_PATH", tmp_path), \
             patch("app.services.payroll.tax_tables._get_config_path", return_value=config_file):
            errors = validate_config_schema(2025)

            assert any("Invalid JSON in" in e for e in errors)
