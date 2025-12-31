"""
JSON Generator for Tax Configuration Files

Generates properly formatted JSON files from extracted tax data.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONGenerator:
    """
    Generate tax configuration JSON files.

    Creates the 5 required JSON files per year:
    - cpp_ei.json
    - federal_jan.json / federal_jul.json
    - provinces_jan.json / provinces_jul.json
    """

    def __init__(self, output_dir: str | Path):
        """
        Initialize JSON generator.

        Args:
            output_dir: Directory to write JSON files to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_cpp_ei(
        self,
        data: dict[str, Any],
        year: int,
        effective_date: str,
        source: str
    ) -> Path:
        """
        Generate cpp_ei.json file.

        Args:
            data: Extracted CPP/EI data with 'cpp' and 'ei' keys
            year: Tax year
            effective_date: Effective date (YYYY-MM-DD)
            source: Source document reference

        Returns:
            Path to generated file
        """
        output = {
            "_metadata": self._create_metadata(effective_date, source),
            "year": year,
            "effective_date": effective_date,
            "source": source,
            "cpp": data.get("cpp", {}),
            "ei": data.get("ei", {})
        }

        return self._write_json("cpp_ei.json", output)

    def generate_federal(
        self,
        data: dict[str, Any],
        year: int,
        effective_date: str,
        source: str,
        edition: str = "jan"
    ) -> Path:
        """
        Generate federal_jan.json or federal_jul.json file.

        Args:
            data: Extracted federal tax data
            year: Tax year
            effective_date: Effective date (YYYY-MM-DD)
            source: Source document reference
            edition: "jan" or "jul"

        Returns:
            Path to generated file
        """
        output = {
            "_metadata": self._create_metadata(effective_date, source),
            "year": year,
            "effective_date": effective_date,
            "source": source,
            "bpaf": data.get("bpaf", 0),
            "cea": data.get("cea", 0),
            "indexing_rate": data.get("indexing_rate"),
            "brackets": data.get("brackets", []),
            "k1_rate": data.get("k1_rate", 0.15),
            "k2_cpp_ei_rate": data.get("k2_cpp_ei_rate", 0.15),
            "k4_canada_employment_rate": data.get("k4_canada_employment_rate", 0.15)
        }

        # Add end_date for jan edition
        if edition == "jan":
            output["end_date"] = f"{year}-06-30"
            output["_metadata"]["end_date"] = f"{year}-06-30"

        filename = f"federal_{edition}.json"
        return self._write_json(filename, output)

    def generate_provinces(
        self,
        data: dict[str, Any],
        year: int,
        effective_date: str,
        source: str,
        edition: str = "jan"
    ) -> Path:
        """
        Generate provinces_jan.json or provinces_jul.json file.

        Args:
            data: Dict of province code -> province data
            year: Tax year
            effective_date: Effective date (YYYY-MM-DD)
            source: Source document reference
            edition: "jan" or "jul"

        Returns:
            Path to generated file
        """
        output = {
            "_metadata": self._create_metadata(effective_date, source),
            "year": year,
            "effective_date": effective_date,
            "source": source,
            "provinces": data
        }

        # Add provinces covered to metadata
        output["_metadata"]["provinces_covered"] = sorted(data.keys())

        filename = f"provinces_{edition}.json"
        return self._write_json(filename, output)

    def _create_metadata(self, effective_date: str, source: str) -> dict[str, Any]:
        """Create metadata section for JSON file."""
        return {
            "effective_date": effective_date,
            "source": {
                "document": "CRA T4127 Payroll Deductions Formulas",
                "extracted_from": source,
                "url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html"
            },
            "generated": {
                "tool": "tax_config_converter",
                "timestamp": datetime.now().isoformat(),
                "method": "GLM AI extraction"
            },
            "validation": {
                "pdoc_validated": False,
                "schema_validated": False
            }
        }

    def _write_json(self, filename: str, data: dict[str, Any]) -> Path:
        """Write data to JSON file with proper formatting."""
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Trailing newline

        logger.info(f"Generated: {filepath}")
        return filepath

    def generate_all(
        self,
        cpp_ei_data: dict[str, Any],
        federal_data: dict[str, Any],
        provinces_data: dict[str, Any],
        year: int,
        effective_date: str,
        source: str,
        edition: str = "jan"
    ) -> list[Path]:
        """
        Generate all JSON files for a year/edition.

        Args:
            cpp_ei_data: CPP/EI data
            federal_data: Federal tax data
            provinces_data: All provinces data
            year: Tax year
            effective_date: Effective date
            source: Source document reference
            edition: "jan" or "jul"

        Returns:
            List of generated file paths
        """
        files = []

        # CPP/EI is shared across editions
        files.append(self.generate_cpp_ei(cpp_ei_data, year, effective_date, source))

        # Federal and provinces are edition-specific
        files.append(self.generate_federal(
            federal_data, year, effective_date, source, edition
        ))
        files.append(self.generate_provinces(
            provinces_data, year, effective_date, source, edition
        ))

        return files
