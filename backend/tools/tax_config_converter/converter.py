"""
Main Tax Config Converter

Orchestrates the conversion of T4127 PDF to JSON tax configuration files.
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

# Text truncation limits for GLM API prompts
CPP_EI_TEXT_LIMIT = 20000
FEDERAL_TEXT_LIMIT = 30000
PROVINCES_TEXT_LIMIT = 50000

from .extractors.pdf_extractor import PDFExtractor, PDFContent
from .extractors.glm_parser import GLMParser
from .prompts.cpp_ei_prompt import create_cpp_ei_prompt
from .prompts.federal_prompt import create_federal_prompt
from .prompts.provinces_prompt import create_provinces_prompt
from .generators.json_generator import JSONGenerator
from .validators.schema_validator import SchemaValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    files_generated: list[Path] = field(default_factory=list)
    validation_results: dict[str, ValidationResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.success:
            files = ", ".join(f.name for f in self.files_generated)
            return f"Conversion successful. Generated: {files}"
        else:
            return f"Conversion failed: {'; '.join(self.errors)}"


class TaxConfigConverter:
    """
    Convert T4127 PDF documents to JSON tax configuration files.

    Usage:
        converter = TaxConfigConverter()
        result = converter.convert(
            pdf_path="docs/tax-tables/2025/01/t4127-01-25e.pdf",
            output_dir="backend/config/tax_tables/2025/"
        )
    """

    def __init__(
        self,
        glm_model: str = "glm-4.7",
        enable_thinking: bool = True,
        validate_output: bool = True
    ):
        """
        Initialize converter.

        Args:
            glm_model: GLM model to use for parsing
            enable_thinking: Enable GLM thinking mode
            validate_output: Validate generated JSON against schemas
        """
        self.pdf_extractor = PDFExtractor()
        self.glm_parser = GLMParser(
            model=glm_model,
            enable_thinking=enable_thinking
        )
        self.validator = SchemaValidator()
        self.validate_output = validate_output

    def convert(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        edition: str = "auto",
        dry_run: bool = False
    ) -> ConversionResult:
        """
        Convert T4127 PDF to JSON configuration files.

        Args:
            pdf_path: Path to T4127 PDF file
            output_dir: Directory to write JSON files to
            edition: "jan", "jul", or "auto" (detect from PDF)
            dry_run: If True, extract but don't write files

        Returns:
            ConversionResult with status and generated files
        """
        result = ConversionResult(success=True)
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        try:
            # Step 1: Extract PDF content
            logger.info(f"Extracting PDF: {pdf_path}")
            pdf_content = self.pdf_extractor.extract(pdf_path)

            # Determine edition
            if edition == "auto":
                edition = self._detect_edition(pdf_content)
            logger.info(f"Edition: {edition}")

            year = pdf_content.metadata.year
            effective_date = pdf_content.metadata.effective_date
            source = f"CRA T4127 ({pdf_content.metadata.edition})"

            if not year:
                result.success = False
                result.errors.append("Could not determine year from PDF")
                return result

            # Step 2: Extract CPP/EI data
            logger.info("Extracting CPP/EI data...")
            cpp_ei_data = self._extract_cpp_ei(pdf_content, year, effective_date)

            # Step 3: Extract Federal data
            logger.info("Extracting Federal tax data...")
            federal_data = self._extract_federal(pdf_content, year, effective_date)

            # Step 4: Extract Provincial data
            logger.info("Extracting Provincial tax data...")
            provinces_data = self._extract_provinces(pdf_content, year, effective_date)

            if dry_run:
                logger.info("Dry run - not writing files")
                result.warnings.append("Dry run mode - no files written")
                self._log_extracted_data(cpp_ei_data, federal_data, provinces_data)
                return result

            # Step 5: Generate JSON files
            logger.info(f"Generating JSON files in: {output_dir}")
            generator = JSONGenerator(output_dir)

            files = generator.generate_all(
                cpp_ei_data=cpp_ei_data,
                federal_data=federal_data,
                provinces_data=provinces_data,
                year=year,
                effective_date=effective_date,
                source=source,
                edition=edition
            )
            result.files_generated = files

            # Step 6: Validate generated files
            if self.validate_output:
                logger.info("Validating generated files...")
                for filepath in files:
                    validation = self.validator.validate_file(filepath)
                    result.validation_results[filepath.name] = validation
                    if not validation.valid:
                        result.warnings.append(
                            f"{filepath.name}: Validation failed"
                        )
                        for error in validation.errors:
                            result.warnings.append(f"  - {error.path}: {error.message}")

            logger.info(f"Conversion complete: {len(files)} files generated")

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            result.success = False
            result.errors.append(str(e))

        return result

    def _detect_edition(self, pdf_content: PDFContent) -> str:
        """Detect edition (jan/jul) from PDF metadata."""
        effective_date = pdf_content.metadata.effective_date
        if effective_date:
            month = effective_date.split("-")[1]
            if month in ("01", "02", "03", "04", "05", "06"):
                return "jan"
            else:
                return "jul"
        return "jan"

    def _extract_cpp_ei(
        self,
        pdf_content: PDFContent,
        year: int,
        effective_date: str
    ) -> dict[str, Any]:
        """Extract CPP/EI data using GLM."""
        # Get relevant table text
        table_text = ""
        for table_id in ["8.3", "8.4", "8.5", "8.6", "8.7"]:
            if table_id in pdf_content.tables:
                table_text += pdf_content.tables[table_id].content + "\n\n"

        if not table_text:
            # Fallback to Chapter 8 content
            table_text = self.pdf_extractor.extract_chapter_8_from_text(
                pdf_content.full_text, pdf_content.tables
            )[:CPP_EI_TEXT_LIMIT]

        prompt = create_cpp_ei_prompt(table_text, year, effective_date)
        return self.glm_parser.parse_json(prompt)

    def _extract_federal(
        self,
        pdf_content: PDFContent,
        year: int,
        effective_date: str
    ) -> dict[str, Any]:
        """Extract federal tax data using GLM."""
        # Get Table 8.1 content
        table_text = ""
        if "8.1" in pdf_content.tables:
            table_text = pdf_content.tables["8.1"].content
        if "8.2" in pdf_content.tables:
            table_text += "\n\n" + pdf_content.tables["8.2"].content

        if not table_text:
            # Fallback
            table_text = self.pdf_extractor.extract_chapter_8_from_text(
                pdf_content.full_text, pdf_content.tables
            )[:FEDERAL_TEXT_LIMIT]

        prompt = create_federal_prompt(table_text, year, effective_date)
        return self.glm_parser.parse_json(prompt)

    def _extract_provinces(
        self,
        pdf_content: PDFContent,
        year: int,
        effective_date: str
    ) -> dict[str, Any]:
        """Extract all provincial tax data using GLM."""
        # Get Table 8.1 content (contains all provincial data)
        table_text = ""
        if "8.1" in pdf_content.tables:
            table_text = pdf_content.tables["8.1"].content
        if "8.2" in pdf_content.tables:
            table_text += "\n\n" + pdf_content.tables["8.2"].content

        if not table_text:
            # Fallback
            table_text = self.pdf_extractor.extract_chapter_8_from_text(
                pdf_content.full_text, pdf_content.tables
            )[:PROVINCES_TEXT_LIMIT]

        prompt = create_provinces_prompt(table_text, year, effective_date)
        return self.glm_parser.parse_json(prompt)

    def _log_extracted_data(
        self,
        cpp_ei: dict[str, Any],
        federal: dict[str, Any],
        provinces: dict[str, Any]
    ) -> None:
        """Log extracted data summary for dry run."""
        import json

        logger.info("=== Extracted CPP/EI ===")
        logger.info(json.dumps(cpp_ei, indent=2)[:500])

        logger.info("=== Extracted Federal ===")
        logger.info(json.dumps(federal, indent=2)[:500])

        logger.info("=== Extracted Provinces ===")
        province_codes = list(provinces.keys()) if isinstance(provinces, dict) else []
        logger.info(f"Provinces: {province_codes}")

    def validate_config(self, config_dir: str | Path) -> dict[str, ValidationResult]:
        """
        Validate existing configuration files.

        Args:
            config_dir: Directory containing JSON config files

        Returns:
            Dict of filename -> ValidationResult
        """
        return self.validator.validate_directory(config_dir)
