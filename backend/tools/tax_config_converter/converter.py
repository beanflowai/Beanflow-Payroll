"""
Main Tax Config Converter

Orchestrates the conversion of T4127 PDF to JSON tax configuration files.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .extractors.base_parser import BaseLLMParser
from .extractors.gemini_parser import GeminiParser
from .extractors.glm_parser import GLMParser
from .extractors.pdf_extractor import PDFContent, PDFExtractor
from .generators.json_generator import JSONGenerator
from .prompts.cpp_ei_prompt import create_cpp_ei_prompt
from .prompts.federal_prompt import create_federal_prompt
from .prompts.province_single_prompt import create_single_province_prompt
from .prompts.provinces_prompt import create_provinces_prompt
from .validators.schema_validator import SchemaValidator, ValidationResult

# Text truncation limits for GLM API prompts
CPP_EI_TEXT_LIMIT = 20000
FEDERAL_TEXT_LIMIT = 30000
PROVINCES_TEXT_LIMIT = 50000

# Supported LLM providers
LLM_PROVIDERS = {
    "gemini": GeminiParser,
    "glm": GLMParser,
}

# All provinces/territories (Quebec excluded - uses separate system)
PROVINCES = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]

# Config directory for deployment
CONFIG_BASE_DIR = Path(__file__).parent.parent.parent / "config" / "tax_tables"

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
        llm_provider: str = "gemini",
        llm_model: str | None = None,
        validate_output: bool = True
    ):
        """
        Initialize converter.

        Args:
            llm_provider: LLM provider to use ("gemini" or "glm")
            llm_model: Model name (optional, uses provider default)
            validate_output: Validate generated JSON against schemas
        """
        self.pdf_extractor = PDFExtractor()

        # Initialize LLM parser based on provider
        if llm_provider not in LLM_PROVIDERS:
            raise ValueError(f"Unknown LLM provider: {llm_provider}. Use: {list(LLM_PROVIDERS.keys())}")

        parser_class = LLM_PROVIDERS[llm_provider]
        if llm_model:
            self.llm_parser: BaseLLMParser = parser_class(model=llm_model)
        else:
            self.llm_parser: BaseLLMParser = parser_class()

        logger.info(f"Using LLM provider: {llm_provider}")

        self.validator = SchemaValidator()
        self.validate_output = validate_output

    def convert(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        edition: str = "auto",
        dry_run: bool = False,
        step: str = "all"
    ) -> ConversionResult:
        """
        Convert T4127 PDF to JSON configuration files.

        Supports resumable conversion and step-by-step execution.

        Args:
            pdf_path: Path to T4127 PDF file
            output_dir: Directory to write JSON files to
            edition: "jan", "jul", or "auto" (detect from PDF)
            dry_run: If True, don't write final config files
            step: Which step to run: "extract", "cpp-ei", "federal", "provinces", "generate", "all"

        Returns:
            ConversionResult with status and generated files
        """
        import json

        result = ConversionResult(success=True)
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Define intermediate file paths
        metadata_file = output_dir / "metadata.json"
        tables_file = output_dir / "tables_extracted.json"
        input_cpp_ei_file = output_dir / "input_cpp_ei.txt"
        input_tax_file = output_dir / "input_tax_tables.txt"
        cpp_ei_file = output_dir / "cpp_ei_parsed.json"
        federal_file = output_dir / "federal_parsed.json"
        provinces_file = output_dir / "provinces_parsed.json"

        try:
            # === Step 1: Extract PDF ===
            if step in ("extract", "all"):
                # Check if all extraction outputs exist
                extraction_complete = all([
                    metadata_file.exists(),
                    tables_file.exists(),
                    input_cpp_ei_file.exists(),
                    input_tax_file.exists()
                ])
                if step == "extract" or not extraction_complete:
                    logger.info(f"[Step 1/4] Extracting PDF: {pdf_path}")
                    pdf_content = self.pdf_extractor.extract(pdf_path)

                    if edition == "auto":
                        edition = self._detect_edition(pdf_content)

                    self._save_pdf_extraction(output_dir, pdf_content)
                    logger.info("✓ PDF extraction complete")

                    if step == "extract":
                        result.files_generated = [
                            metadata_file, tables_file, input_cpp_ei_file, input_tax_file
                        ]
                        return result
                else:
                    logger.info("[Step 1/4] ✓ PDF extraction cached, skipping...")

            # Load PDF data for subsequent steps
            pdf_content, year, effective_date, source, edition = self._load_pdf_data(
                output_dir, pdf_path, edition
            )

            if not year:
                result.success = False
                result.errors.append("Could not determine year from PDF. Run --step extract first.")
                return result

            logger.info(f"Year: {year}, Edition: {edition}")

            # === Step 2: CPP/EI ===
            if step in ("cpp-ei", "all"):
                if step == "cpp-ei" or not cpp_ei_file.exists():
                    logger.info("[Step 2/4] Extracting CPP/EI data via GLM...")
                    cpp_ei_data = self._extract_cpp_ei(pdf_content, year, effective_date)
                    cpp_ei_file.write_text(json.dumps(cpp_ei_data, indent=2, ensure_ascii=False))
                    logger.info(f"✓ Saved: {cpp_ei_file.name}")

                    if step == "cpp-ei":
                        result.files_generated = [cpp_ei_file]
                        return result
                else:
                    logger.info("[Step 2/4] ✓ cpp_ei_parsed.json cached, skipping...")

            # === Step 3: Federal ===
            if step in ("federal", "all"):
                if step == "federal" or not federal_file.exists():
                    logger.info("[Step 3/4] Extracting Federal tax data via GLM...")
                    federal_data = self._extract_federal(pdf_content, year, effective_date)
                    federal_file.write_text(json.dumps(federal_data, indent=2, ensure_ascii=False))
                    logger.info(f"✓ Saved: {federal_file.name}")

                    if step == "federal":
                        result.files_generated = [federal_file]
                        return result
                else:
                    logger.info("[Step 3/4] ✓ federal_parsed.json cached, skipping...")

            # === Step 4: Provinces (sequential processing) ===
            # Support for --step province-XX (single province) or --step provinces (all)
            single_province = None
            if step.startswith("province-"):
                single_province = step.split("-")[1].upper()
                if single_province not in PROVINCES:
                    result.success = False
                    result.errors.append(f"Invalid province code: {single_province}")
                    return result

            if step in ("provinces", "all") or single_province:
                provinces_dir = output_dir / "provinces"

                # Check if all provinces are cached
                all_cached = all(
                    (provinces_dir / f"{code}_parsed.json").exists()
                    for code in PROVINCES
                )

                if step == "provinces" or single_province or not all_cached or not provinces_file.exists():
                    logger.info("[Step 4/4] Extracting Provincial tax data via GLM (sequential)...")
                    provinces_data = self._extract_provinces_sequential(
                        pdf_content, year, effective_date, output_dir, single_province
                    )

                    # If processing all provinces, merge and save combined file
                    if not single_province:
                        # Merge all individual files into provinces_parsed.json
                        provinces_data = self._merge_province_files(output_dir)
                        provinces_file.write_text(json.dumps(provinces_data, indent=2, ensure_ascii=False))
                        logger.info(f"✓ Saved: {provinces_file.name} ({len(provinces_data)} provinces)")

                    if step == "provinces" or single_province:
                        result.files_generated = [provinces_file] if provinces_file.exists() else []
                        return result
                else:
                    logger.info("[Step 4/4] ✓ provinces_parsed.json cached, skipping...")

            # === Generate final config files ===
            if step in ("generate", "all"):
                if dry_run:
                    logger.info("Dry run - skipping final JSON generation")
                    result.files_generated = [
                        f for f in [metadata_file, tables_file, cpp_ei_file, federal_file, provinces_file]
                        if f.exists()
                    ]
                    result.warnings.append("Dry run mode - intermediate files only")
                    return result

                # Load all parsed data
                cpp_ei_data = json.loads(cpp_ei_file.read_text()) if cpp_ei_file.exists() else {}
                federal_data = json.loads(federal_file.read_text()) if federal_file.exists() else {}
                provinces_data = json.loads(provinces_file.read_text()) if provinces_file.exists() else {}

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

            # === Step: Deploy to config ===
            if step in ("deploy", "all"):
                logger.info("[Deploy] Copying files to config/tax_tables/...")
                deployed = self._deploy_to_config(output_dir, year, edition)
                result.files_generated.extend(deployed)
                logger.info(f"✓ Deployed {len(deployed)} files to {CONFIG_BASE_DIR / str(year)}")

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            result.success = False
            result.errors.append(str(e))

        return result

    def _deploy_to_config(
        self,
        output_dir: Path,
        year: int,
        edition: str
    ) -> list[Path]:
        """
        Deploy generated files to backend/config/tax_tables/{year}/.

        Copies and reformats:
        - cpp_ei.json
        - federal_{edition}.json
        - provinces_{edition}.json

        Args:
            output_dir: Source directory with generated files
            year: Tax year
            edition: "jan" or "jul"

        Returns:
            List of deployed file paths
        """
        import json

        config_dir = CONFIG_BASE_DIR / str(year)
        config_dir.mkdir(parents=True, exist_ok=True)

        deployed: list[Path] = []
        files_to_deploy = [
            "cpp_ei.json",
            f"federal_{edition}.json",
            f"provinces_{edition}.json"
        ]

        for filename in files_to_deploy:
            src = output_dir / filename
            if src.exists():
                dst = config_dir / filename
                # Read, reformat, write
                data = json.loads(src.read_text())
                dst.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
                deployed.append(dst)
                logger.info(f"  → {dst}")
            else:
                logger.warning(f"  ⚠ {filename} not found in {output_dir}")

        return deployed

    def _load_pdf_data(
        self,
        output_dir: Path,
        pdf_path: Path,
        edition: str
    ) -> tuple[PDFContent | None, int | None, str | None, str | None, str]:
        """Load PDF data from cache or extract from PDF."""
        import json

        from .extractors.pdf_extractor import PDFContent, PDFMetadata, TableSection

        metadata_file = output_dir / "metadata.json"
        tables_file = output_dir / "tables_extracted.json"

        if metadata_file.exists() and tables_file.exists():
            metadata = json.loads(metadata_file.read_text())
            tables_data = json.loads(tables_file.read_text())

            year = metadata.get("year")
            effective_date = metadata.get("effectiveDate")
            source = f"CRA T4127 ({metadata.get('edition')})"

            if edition == "auto":
                if effective_date:
                    month = effective_date.split("-")[1]
                    edition = "jan" if month in ("01", "02", "03", "04", "05", "06") else "jul"
                else:
                    edition = "jan"

            pdf_content = PDFContent(
                full_text="",
                tables={
                    tid: TableSection(
                        table_id=tid,
                        title=tdata["title"],
                        content=tdata["content"],
                        start_page=tdata["startPage"],
                        end_page=tdata["endPage"]
                    )
                    for tid, tdata in tables_data.items()
                },
                metadata=PDFMetadata(
                    edition=metadata.get("edition", ""),
                    edition_number=metadata.get("editionNumber"),
                    effective_date=effective_date,
                    year=year,
                    total_pages=metadata.get("pageCount", 0)
                )
            )
            return pdf_content, year, effective_date, source, edition

        # No cache, need to extract first
        return None, None, None, None, edition

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
        return self.llm_parser.parse_json(prompt)

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
        return self.llm_parser.parse_json(prompt)

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
        return self.llm_parser.parse_json(prompt)

    def _extract_provinces_sequential(
        self,
        pdf_content: PDFContent,
        year: int,
        effective_date: str,
        output_dir: Path,
        single_province: str | None = None
    ) -> dict[str, Any]:
        """
        Extract provincial tax data one province at a time.

        Supports resumable extraction with per-province caching.
        Each province is processed individually and cached in provinces/ subdir.

        Args:
            pdf_content: Extracted PDF content
            year: Tax year
            effective_date: Effective date string
            output_dir: Output directory for caching
            single_province: If set, only process this province (for debugging)

        Returns:
            Combined dict with all province data
        """
        import json

        provinces_dir = output_dir / "provinces"
        provinces_dir.mkdir(exist_ok=True)

        # Get Table 8.1/8.2 content
        table_text = ""
        if "8.1" in pdf_content.tables:
            table_text = pdf_content.tables["8.1"].content
        if "8.2" in pdf_content.tables:
            table_text += "\n\n" + pdf_content.tables["8.2"].content

        if not table_text:
            table_text = self.pdf_extractor.extract_chapter_8_from_text(
                pdf_content.full_text, pdf_content.tables
            )[:PROVINCES_TEXT_LIMIT]

        all_provinces: dict[str, Any] = {}
        provinces_to_process = [single_province] if single_province else PROVINCES

        for code in provinces_to_process:
            province_file = provinces_dir / f"{code}_parsed.json"

            # Resume support: skip already processed provinces
            if province_file.exists() and not single_province:
                logger.info(f"  ✓ {code} cached, loading...")
                data = json.loads(province_file.read_text())
                all_provinces[code] = data
                continue

            logger.info(f"  → Processing {code}...")
            prompt = create_single_province_prompt(table_text, year, effective_date, code)

            try:
                data = self.llm_parser.parse_json(prompt)
                province_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                all_provinces[code] = data
                logger.info(f"  ✓ {code} done")
            except Exception as e:
                logger.error(f"  ✗ {code} failed: {e}")
                # Continue with next province instead of failing entirely
                continue

        return all_provinces

    def _merge_province_files(self, output_dir: Path) -> dict[str, Any]:
        """
        Merge individual province files into provinces_parsed.json.

        Args:
            output_dir: Output directory containing provinces/ subdir

        Returns:
            Combined dict with all province data
        """
        import json

        provinces_dir = output_dir / "provinces"
        all_provinces: dict[str, Any] = {}

        for code in PROVINCES:
            province_file = provinces_dir / f"{code}_parsed.json"
            if province_file.exists():
                all_provinces[code] = json.loads(province_file.read_text())
            else:
                logger.warning(f"Province file missing: {province_file}")

        return all_provinces

    def _save_pdf_extraction(
        self,
        output_dir: Path,
        pdf_content: PDFContent
    ) -> None:
        """Save PDF extraction results (metadata + tables + pre-split input files)."""
        import json

        # Save metadata
        metadata_file = output_dir / "metadata.json"
        metadata = {
            "edition": pdf_content.metadata.edition,
            "editionNumber": pdf_content.metadata.edition_number,
            "year": pdf_content.metadata.year,
            "effectiveDate": pdf_content.metadata.effective_date,
            "pageCount": pdf_content.metadata.total_pages,
            "tableCount": len(pdf_content.tables)
        }
        metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        logger.info(f"Saved: {metadata_file}")

        # Save tables
        tables_file = output_dir / "tables_extracted.json"
        tables_data = {
            table_id: {
                "title": table.title,
                "startPage": table.start_page,
                "endPage": table.end_page,
                "content": table.content
            }
            for table_id, table in pdf_content.tables.items()
        }
        tables_file.write_text(json.dumps(tables_data, indent=2, ensure_ascii=False))
        logger.info(f"Saved: {tables_file}")

        # Pre-generate split input files for subsequent steps
        # input_cpp_ei.txt - Tables 8.3-8.7 for CPP/EI parsing
        cpp_ei_text = ""
        for tid in ["8.3", "8.4", "8.5", "8.6", "8.7"]:
            if tid in pdf_content.tables:
                cpp_ei_text += pdf_content.tables[tid].content + "\n\n"
        input_cpp_ei_file = output_dir / "input_cpp_ei.txt"
        input_cpp_ei_file.write_text(cpp_ei_text.strip())
        logger.info(f"Saved: {input_cpp_ei_file} ({len(cpp_ei_text)} chars)")

        # input_tax_tables.txt - Tables 8.1-8.2 for Federal/Provincial parsing
        tax_text = ""
        for tid in ["8.1", "8.2"]:
            if tid in pdf_content.tables:
                tax_text += pdf_content.tables[tid].content + "\n\n"
        input_tax_file = output_dir / "input_tax_tables.txt"
        input_tax_file.write_text(tax_text.strip())
        logger.info(f"Saved: {input_tax_file} ({len(tax_text)} chars)")

    def _save_intermediate_files(
        self,
        output_dir: Path,
        pdf_content: PDFContent,
        cpp_ei_data: dict[str, Any],
        federal_data: dict[str, Any],
        provinces_data: dict[str, Any]
    ) -> list[Path]:
        """
        Save intermediate files for debugging and caching.

        Saves:
        - metadata.json: PDF metadata
        - tables_extracted.json: Raw table text
        - cpp_ei_parsed.json: GLM parsed CPP/EI data
        - federal_parsed.json: GLM parsed federal data
        - provinces_parsed.json: GLM parsed provincial data
        """
        import json

        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files: list[Path] = []

        # 1. Save metadata
        metadata_file = output_dir / "metadata.json"
        metadata = {
            "edition": pdf_content.metadata.edition,
            "year": pdf_content.metadata.year,
            "effectiveDate": pdf_content.metadata.effective_date,
            "pageCount": pdf_content.metadata.page_count,
            "tableCount": len(pdf_content.tables)
        }
        metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        saved_files.append(metadata_file)
        logger.info(f"Saved: {metadata_file}")

        # 2. Save extracted tables
        tables_file = output_dir / "tables_extracted.json"
        tables_data = {
            table_id: {
                "title": table.title,
                "startPage": table.start_page,
                "endPage": table.end_page,
                "content": table.content
            }
            for table_id, table in pdf_content.tables.items()
        }
        tables_file.write_text(json.dumps(tables_data, indent=2, ensure_ascii=False))
        saved_files.append(tables_file)
        logger.info(f"Saved: {tables_file}")

        # 3. Save GLM parsed results
        cpp_ei_file = output_dir / "cpp_ei_parsed.json"
        cpp_ei_file.write_text(json.dumps(cpp_ei_data, indent=2, ensure_ascii=False))
        saved_files.append(cpp_ei_file)
        logger.info(f"Saved: {cpp_ei_file}")

        federal_file = output_dir / "federal_parsed.json"
        federal_file.write_text(json.dumps(federal_data, indent=2, ensure_ascii=False))
        saved_files.append(federal_file)
        logger.info(f"Saved: {federal_file}")

        provinces_file = output_dir / "provinces_parsed.json"
        provinces_file.write_text(json.dumps(provinces_data, indent=2, ensure_ascii=False))
        saved_files.append(provinces_file)
        logger.info(f"Saved: {provinces_file}")

        return saved_files

    def validate_config(self, config_dir: str | Path) -> dict[str, ValidationResult]:
        """
        Validate existing configuration files.

        Args:
            config_dir: Directory containing JSON config files

        Returns:
            Dict of filename -> ValidationResult
        """
        return self.validator.validate_directory(config_dir)
