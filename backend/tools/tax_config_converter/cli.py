"""
CLI Interface for Tax Config Converter

Usage:
    uv run python -m tools.tax_config_converter convert --pdf path/to/t4127.pdf --output dir/
    uv run python -m tools.tax_config_converter validate --config dir/
"""

import argparse
import logging
import sys
from pathlib import Path

from .converter import TaxConfigConverter

# Base output directory for generated files
OUTPUT_BASE_DIR = Path(__file__).parent / "output"


def infer_output_path(pdf_path: str) -> Path:
    """
    Infer output path from PDF path structure.

    Example:
        docs/tax-tables/2025/01/t4127-01-25e.pdf → output/2025/01/

    Args:
        pdf_path: Path to PDF file

    Returns:
        Path to output directory
    """
    pdf = Path(pdf_path).resolve()
    parts = pdf.parts

    # Look for "tax-tables" in path and extract year/month
    for i, part in enumerate(parts):
        if part == "tax-tables" and i + 2 < len(parts):
            year = parts[i + 1]  # e.g., "2025"
            month = parts[i + 2]  # e.g., "01"
            return OUTPUT_BASE_DIR / year / month

    # Fallback: use PDF stem as directory name
    return OUTPUT_BASE_DIR / pdf.stem


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )


def cmd_convert(args: argparse.Namespace) -> int:
    """Handle convert command."""
    # Infer output path if not specified
    output_dir = args.output if args.output else infer_output_path(args.pdf)
    print(f"Output directory: {output_dir}")

    converter = TaxConfigConverter(
        llm_provider=args.llm,
        llm_model=args.model if args.model else None,
        validate_output=not args.skip_validation
    )

    result = converter.convert(
        pdf_path=args.pdf,
        output_dir=output_dir,
        edition=args.edition,
        dry_run=args.dry_run,
        step=args.step
    )

    if result.success:
        print("\n✓ Conversion successful!")
        print("\nGenerated files:")
        for f in result.files_generated:
            print(f"  - {f}")

        if result.validation_results:
            print("\nValidation results:")
            all_valid = True
            for filename, validation in result.validation_results.items():
                status = "✓" if validation.valid else "✗"
                print(f"  {status} {filename}")
                if not validation.valid:
                    all_valid = False
                    for error in validation.errors:
                        print(f"      {error.path}: {error.message}")
                for warning in validation.warnings:
                    print(f"      ⚠ {warning}")

            if not all_valid:
                print("\n⚠ Some validations failed. Please review and fix.")

        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  ⚠ {w}")

        return 0
    else:
        print("\n✗ Conversion failed!")
        for error in result.errors:
            print(f"  - {error}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle validate command."""
    converter = TaxConfigConverter()
    results = converter.validate_config(args.config)

    if not results:
        print(f"No JSON files found in {args.config}")
        return 1

    all_valid = True
    print(f"\nValidation results for {args.config}:\n")

    for filename, result in sorted(results.items()):
        status = "✓" if result.valid else "✗"
        print(f"{status} {filename}")

        if not result.valid:
            all_valid = False
            for error in result.errors:
                print(f"    Error: {error.path}: {error.message}")

        for warning in result.warnings:
            print(f"    Warning: {warning}")

    if all_valid:
        print(f"\n✓ All {len(results)} files passed validation!")
        return 0
    else:
        print("\n✗ Some files failed validation")
        return 1


def cmd_extract(args: argparse.Namespace) -> int:
    """Handle extract command - just extract PDF text without GLM."""
    import json

    from .extractors.pdf_extractor import PDFExtractor

    extractor = PDFExtractor()
    content = extractor.extract(args.pdf)

    print("\n=== PDF Metadata ===")
    print(f"Edition: {content.metadata.edition}")
    print(f"Edition Number: {content.metadata.edition_number}")
    print(f"Effective Date: {content.metadata.effective_date}")
    print(f"Year: {content.metadata.year}")
    print(f"Total Pages: {content.metadata.total_pages}")

    print("\n=== Tables Found ===")
    for table_id, table in content.tables.items():
        print(f"Table {table_id}: {table.title[:60]}...")
        print(f"  Pages {table.start_page}-{table.end_page}, {len(table.content)} chars")

    if args.output:
        output_path = Path(args.output)

        # If output is a directory, save structured JSON files
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path.mkdir(parents=True, exist_ok=True)

            # Save metadata.json
            metadata_file = output_path / "metadata.json"
            metadata = {
                "edition": content.metadata.edition,
                "editionNumber": content.metadata.edition_number,
                "year": content.metadata.year,
                "effectiveDate": content.metadata.effective_date,
                "pageCount": content.metadata.total_pages,
                "tableCount": len(content.tables)
            }
            metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
            print(f"\nSaved: {metadata_file}")

            # Save tables_extracted.json
            tables_file = output_path / "tables_extracted.json"
            tables_data = {
                table_id: {
                    "title": table.title,
                    "startPage": table.start_page,
                    "endPage": table.end_page,
                    "content": table.content
                }
                for table_id, table in content.tables.items()
            }
            tables_file.write_text(json.dumps(tables_data, indent=2, ensure_ascii=False))
            print(f"Saved: {tables_file}")

            print(f"\n✓ Extracted to {output_path}")
        else:
            # Output is a file - save text
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if args.table:
                # Output specific table
                if args.table in content.tables:
                    text = content.tables[args.table].content
                else:
                    print(f"Table {args.table} not found")
                    return 1
            else:
                # Output full text
                text = content.full_text

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"\nText written to: {output_path}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="tax_config_converter",
        description="Convert CRA T4127 PDF documents to JSON tax configuration files"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert T4127 PDF to JSON configuration files"
    )
    convert_parser.add_argument(
        "--pdf", "-p",
        required=True,
        help="Path to T4127 PDF file"
    )
    convert_parser.add_argument(
        "--output", "-o",
        required=False,
        default=None,
        help="Output directory for JSON files (auto-inferred from PDF path if not specified)"
    )
    convert_parser.add_argument(
        "--edition", "-e",
        choices=["jan", "jul", "auto"],
        default="auto",
        help="Edition type (default: auto-detect)"
    )
    convert_parser.add_argument(
        "--llm", "-l",
        choices=["gemini", "glm"],
        default="gemini",
        help="LLM provider: gemini (fast, needs GEMINI_API_KEY) or glm (slow but free, needs GLM_API_KEY)"
    )
    convert_parser.add_argument(
        "--model", "-m",
        default=None,
        help="LLM model name (optional, uses provider default)"
    )
    convert_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip schema validation of output"
    )
    convert_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract data but don't write final config files"
    )
    convert_parser.add_argument(
        "--step", "-s",
        default="all",
        help=(
            "Run specific step only: extract (PDF), cpp-ei, federal, provinces, "
            "province-XX (single province, e.g., province-ON), generate (final JSON), "
            "deploy (copy to config/tax_tables), all (default)"
        )
    )
    convert_parser.set_defaults(func=cmd_convert)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate existing JSON configuration files"
    )
    validate_parser.add_argument(
        "--config", "-c",
        required=True,
        help="Directory containing JSON config files"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # Extract command (for debugging)
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract text from PDF (for debugging)"
    )
    extract_parser.add_argument(
        "--pdf", "-p",
        required=True,
        help="Path to T4127 PDF file"
    )
    extract_parser.add_argument(
        "--output", "-o",
        help="Output file for extracted text"
    )
    extract_parser.add_argument(
        "--table", "-t",
        help="Extract specific table (e.g., 8.1)"
    )
    extract_parser.set_defaults(func=cmd_extract)

    args = parser.parse_args()
    setup_logging(args.verbose)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
