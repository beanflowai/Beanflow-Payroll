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
    converter = TaxConfigConverter(
        glm_model=args.model,
        enable_thinking=not args.no_thinking,
        validate_output=not args.skip_validation
    )

    result = converter.convert(
        pdf_path=args.pdf,
        output_dir=args.output,
        edition=args.edition,
        dry_run=args.dry_run
    )

    if result.success:
        print(f"\n✓ Conversion successful!")
        print(f"\nGenerated files:")
        for f in result.files_generated:
            print(f"  - {f}")

        if result.validation_results:
            print(f"\nValidation results:")
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
            print(f"\nWarnings:")
            for w in result.warnings:
                print(f"  ⚠ {w}")

        return 0
    else:
        print(f"\n✗ Conversion failed!")
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
        print(f"\n✗ Some files failed validation")
        return 1


def cmd_extract(args: argparse.Namespace) -> int:
    """Handle extract command - just extract PDF text without GLM."""
    from .extractors.pdf_extractor import PDFExtractor

    extractor = PDFExtractor()
    content = extractor.extract(args.pdf)

    print(f"\n=== PDF Metadata ===")
    print(f"Edition: {content.metadata.edition}")
    print(f"Edition Number: {content.metadata.edition_number}")
    print(f"Effective Date: {content.metadata.effective_date}")
    print(f"Year: {content.metadata.year}")
    print(f"Total Pages: {content.metadata.total_pages}")

    print(f"\n=== Tables Found ===")
    for table_id, table in content.tables.items():
        print(f"Table {table_id}: {table.title[:60]}...")
        print(f"  Pages {table.start_page}-{table.end_page}, {len(table.content)} chars")

    if args.output:
        output_path = Path(args.output)
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
        required=True,
        help="Output directory for JSON files"
    )
    convert_parser.add_argument(
        "--edition", "-e",
        choices=["jan", "jul", "auto"],
        default="auto",
        help="Edition type (default: auto-detect)"
    )
    convert_parser.add_argument(
        "--model", "-m",
        default="glm-4.7",
        help="GLM model to use (default: glm-4.7)"
    )
    convert_parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Disable GLM thinking mode"
    )
    convert_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip schema validation of output"
    )
    convert_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract data but don't write files"
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
