"""
Schema Validator for Tax Configuration Files

Validates generated JSON files against JSON Schema definitions.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default schema directory relative to this file
DEFAULT_SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "config" / "tax_tables" / "schemas"


@dataclass
class ValidationError:
    """Represents a validation error."""
    path: str
    message: str
    schema_path: str = ""


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.valid:
            return "Validation passed"
        error_msgs = [f"  - {e.path}: {e.message}" for e in self.errors]
        return "Validation failed:\n" + "\n".join(error_msgs)


class SchemaValidator:
    """
    Validate tax configuration JSON files against schemas.

    Usage:
        validator = SchemaValidator()
        result = validator.validate_file("path/to/cpp_ei.json")
        if not result.valid:
            print(result.errors)
    """

    def __init__(self, schema_dir: str | Path | None = None):
        """
        Initialize validator with schema directory.

        Args:
            schema_dir: Path to directory containing schema files.
                       Defaults to backend/config/tax_tables/schemas/
        """
        self.schema_dir = Path(schema_dir) if schema_dir else DEFAULT_SCHEMA_DIR
        self._schemas: dict[str, dict] = {}
        self._jsonschema = None

    def _get_jsonschema(self):
        """Lazy import of jsonschema."""
        if self._jsonschema is None:
            try:
                import jsonschema
                self._jsonschema = jsonschema
            except ImportError:
                raise ImportError(
                    "jsonschema package is required. Install with: uv add jsonschema"
                )
        return self._jsonschema

    def _load_schema(self, schema_name: str) -> dict:
        """Load and cache a schema file."""
        if schema_name not in self._schemas:
            schema_path = self.schema_dir / f"{schema_name}.schema.json"
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema not found: {schema_path}")

            with open(schema_path, "r", encoding="utf-8") as f:
                self._schemas[schema_name] = json.load(f)

            logger.debug(f"Loaded schema: {schema_name}")

        return self._schemas[schema_name]

    def _get_schema_for_file(self, filename: str) -> str:
        """Determine which schema to use for a given filename."""
        if "cpp_ei" in filename:
            return "cpp_ei"
        elif "federal" in filename:
            return "federal"
        elif "provinces" in filename:
            return "provinces"
        else:
            raise ValueError(f"Unknown file type: {filename}")

    def validate_file(self, filepath: str | Path) -> ValidationResult:
        """
        Validate a JSON file against its schema.

        Args:
            filepath: Path to JSON file to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        filepath = Path(filepath)
        jsonschema = self._get_jsonschema()

        if not filepath.exists():
            return ValidationResult(
                valid=False,
                errors=[ValidationError("file", f"File not found: {filepath}")]
            )

        # Load the data
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError("json", f"Invalid JSON: {e}")]
            )

        # Determine and load schema
        try:
            schema_name = self._get_schema_for_file(filepath.name)
            schema = self._load_schema(schema_name)
        except (ValueError, FileNotFoundError) as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError("schema", str(e))]
            )

        # Validate - collect all errors, not just the first one
        errors = []
        validator_cls = jsonschema.Draft7Validator
        validator = validator_cls(schema)
        for error in validator.iter_errors(data):
            errors.append(ValidationError(
                path=".".join(str(p) for p in error.absolute_path),
                message=error.message,
                schema_path=".".join(str(p) for p in error.absolute_schema_path)
            ))

        # Run additional sanity checks
        warnings = self._sanity_checks(data, schema_name)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_data(
        self, data: dict, schema_name: str
    ) -> ValidationResult:
        """
        Validate data dict against a named schema.

        Args:
            data: Data dictionary to validate
            schema_name: Name of schema ("cpp_ei", "federal", "provinces")

        Returns:
            ValidationResult with validation status and any errors
        """
        jsonschema = self._get_jsonschema()

        try:
            schema = self._load_schema(schema_name)
        except FileNotFoundError as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError("schema", str(e))]
            )

        # Validate - collect all errors, not just the first one
        errors = []
        validator_cls = jsonschema.Draft7Validator
        validator = validator_cls(schema)
        for error in validator.iter_errors(data):
            errors.append(ValidationError(
                path=".".join(str(p) for p in error.absolute_path),
                message=error.message,
                schema_path=".".join(str(p) for p in error.absolute_schema_path)
            ))

        warnings = self._sanity_checks(data, schema_name)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _sanity_checks(self, data: dict, schema_name: str) -> list[str]:
        """
        Run additional sanity checks beyond schema validation.

        Returns list of warning messages.
        """
        warnings = []

        if schema_name == "cpp_ei":
            warnings.extend(self._check_cpp_ei(data))
        elif schema_name == "federal":
            warnings.extend(self._check_federal(data))
        elif schema_name == "provinces":
            warnings.extend(self._check_provinces(data))

        return warnings

    def _check_cpp_ei(self, data: dict) -> list[str]:
        """Sanity checks for CPP/EI data."""
        warnings = []
        cpp = data.get("cpp", {})
        ei = data.get("ei", {})

        # Check YMPE < YAMPE
        if cpp.get("ympe", 0) >= cpp.get("yampe", 0):
            warnings.append("YMPE should be less than YAMPE")

        # Check rate bounds
        if not (0 < cpp.get("base_rate", 0) < 0.10):
            warnings.append(f"CPP base_rate {cpp.get('base_rate')} seems unusual")

        if not (0 < ei.get("employee_rate", 0) < 0.05):
            warnings.append(f"EI rate {ei.get('employee_rate')} seems unusual")

        # Check max contribution calculation
        expected_base = (cpp.get("ympe", 0) - cpp.get("basic_exemption", 0)) * cpp.get("base_rate", 0)
        actual_base = cpp.get("max_base_contribution", 0)
        if abs(expected_base - actual_base) > 1:
            warnings.append(
                f"max_base_contribution {actual_base} doesn't match "
                f"calculated value {expected_base:.2f}"
            )

        return warnings

    def _check_federal(self, data: dict) -> list[str]:
        """Sanity checks for federal tax data."""
        warnings = []
        brackets = data.get("brackets", [])

        # Check bracket ordering
        thresholds = [b.get("threshold", 0) for b in brackets]
        if thresholds != sorted(thresholds):
            warnings.append("Bracket thresholds are not in ascending order")

        # Check rate progression
        rates = [b.get("rate", 0) for b in brackets]
        if rates != sorted(rates):
            warnings.append("Bracket rates are not in ascending order")

        # Check BPAF reasonable range
        bpaf = data.get("bpaf", 0)
        if not (10000 < bpaf < 25000):
            warnings.append(f"BPAF {bpaf} seems outside expected range")

        return warnings

    def _check_provinces(self, data: dict) -> list[str]:
        """Sanity checks for provinces data."""
        warnings = []
        provinces = data.get("provinces", {})

        expected_codes = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"}
        actual_codes = set(provinces.keys())

        missing = expected_codes - actual_codes
        if missing:
            warnings.append(f"Missing provinces: {missing}")

        extra = actual_codes - expected_codes
        if extra:
            warnings.append(f"Unexpected province codes: {extra}")

        # Check each province
        for code, prov in provinces.items():
            # Check bracket ordering
            brackets = prov.get("brackets", [])
            thresholds = [b.get("threshold", 0) for b in brackets]
            if thresholds != sorted(thresholds):
                warnings.append(f"{code}: Bracket thresholds not in order")

            # Check BPA range
            bpa = prov.get("bpa", 0)
            if not (5000 < bpa < 30000):
                warnings.append(f"{code}: BPA {bpa} seems outside expected range")

        return warnings

    def validate_directory(self, directory: str | Path) -> dict[str, ValidationResult]:
        """
        Validate all JSON files in a directory.

        Args:
            directory: Path to directory with JSON files

        Returns:
            Dict of filename -> ValidationResult
        """
        directory = Path(directory)
        results = {}

        for filepath in directory.glob("*.json"):
            results[filepath.name] = self.validate_file(filepath)

        return results
