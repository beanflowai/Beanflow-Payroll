# Phase 6: Configuration Architecture & Parameterization

**Status**: Planning Phase
**Complexity**: Medium
**Prerequisites**: Phase 1-5 design completed

---

## 🎯 Objectives

Design a configuration-driven architecture that externalizes all tax rates, thresholds, and formulas to JSON files, enabling zero-code updates when CRA publishes new T4127 editions.

### Problem Statement

**Current Challenge:**
- CRA publishes T4127 Payroll Deductions Formulas **twice per year** (January and July editions)
- Tax rates, brackets, CPP/EI limits, and indexing factors change regularly
- Current design hardcodes these values in `tax_tables_2025.py`
- Each update requires code changes, testing, and deployment

**Business Impact:**
- Developer time spent on manual transcription from T4127 PDF
- Risk of human error when updating 12 provinces × multiple tax brackets
- Inability to perform historical calculations (e.g., "What was payroll for Jan 2024?")
- Testing burden for every CRA update

**Solution:**
- Externalize all tax configuration to JSON files
- Create Python configuration loader with Decimal precision
- Enable version-controlled tax history (2024/jan, 2024/jul, 2025/jan, etc.)
- Support "time-travel" calculations for historical payroll

---

## 📦 Configuration File Architecture

### Directory Structure

```
backend/
├── config/
│   └── tax_tables/
│       ├── 2024/
│       │   ├── jan/
│       │   │   ├── federal_2024_jan.json
│       │   │   ├── provinces_2024_jan.json
│       │   │   ├── cpp_ei_2024_jan.json
│       │   │   └── special_taxes_2024_jan.json
│       │   └── jul/
│       │       ├── federal_2024_jul.json
│       │       ├── provinces_2024_jul.json
│       │       ├── cpp_ei_2024_jul.json
│       │       └── special_taxes_2024_jul.json
│       └── 2025/
│           ├── jan/
│           │   ├── federal_2025_jan.json
│           │   ├── provinces_2025_jan.json
│           │   ├── cpp_ei_2025_jan.json
│           │   └── special_taxes_2025_jan.json
│           └── jul/
│               ├── federal_2025_jul.json
│               ├── provinces_2025_jul.json
│               ├── cpp_ei_2025_jul.json
│               └── special_taxes_2025_jul.json
```

### Configuration File Types

| File Name | Purpose | Update Frequency |
|-----------|---------|------------------|
| `federal_{year}_{edition}.json` | Federal tax brackets, BPA, CEA, indexing | Every T4127 edition |
| `provinces_{year}_{edition}.json` | 12 provincial tax tables, BPA, indexing | Every T4127 edition |
| `cpp_ei_{year}_{edition}.json` | CPP/EI rates, maximums, exemptions | Annually (January) |
| `special_taxes_{year}_{edition}.json` | Ontario surtax/health premium, BC tax reduction | When thresholds change |

---

## 📄 JSON Schema Examples

### 1. Federal Tax Configuration

**File**: `backend/config/tax_tables/2025/jul/federal_2025_jul.json`

```json
{
  "metadata": {
    "year": 2025,
    "edition": "jul",
    "effective_date": "2025-07-01",
    "t4127_edition": "121st Edition, July 2025",
    "source_url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas/t4127-jul.html",
    "created_date": "2025-06-15",
    "verified_against_pdoc": true
  },
  "federal_tax": {
    "bpaf": "16129.00",
    "cea": "1471.00",
    "indexing_rate": "0.027",
    "tax_brackets": [
      {
        "threshold": "0",
        "rate": "0.1400",
        "constant": "0",
        "description": "Up to $57,375"
      },
      {
        "threshold": "57375",
        "rate": "0.2050",
        "constant": "3729",
        "description": "$57,375 to $114,750"
      },
      {
        "threshold": "114750",
        "rate": "0.2600",
        "constant": "11492",
        "description": "$114,750 to $177,882"
      },
      {
        "threshold": "177882",
        "rate": "0.2900",
        "constant": "27906",
        "description": "$177,882 to $253,414"
      },
      {
        "threshold": "253414",
        "rate": "0.3300",
        "constant": "49485",
        "description": "Over $253,414"
      }
    ]
  },
  "validation": {
    "bracket_count": 5,
    "first_threshold_is_zero": true,
    "thresholds_ascending": true,
    "verified_with_t4127_page": 18
  }
}
```

### 2. Provincial Tax Configuration

**File**: `backend/config/tax_tables/2025/jul/provinces_2025_jul.json`

```json
{
  "metadata": {
    "year": 2025,
    "edition": "jul",
    "effective_date": "2025-07-01",
    "t4127_edition": "121st Edition, July 2025",
    "provinces_count": 12,
    "note": "Quebec not included (separate system)"
  },
  "provinces": {
    "AB": {
      "code": "AB",
      "name": "Alberta",
      "basic_personal_amount": "22323.00",
      "bpa_is_dynamic": false,
      "indexing_rate": "0.020",
      "has_surtax": false,
      "has_health_premium": false,
      "has_tax_reduction": false,
      "lcp_rate": null,
      "lcp_max_amount": null,
      "tax_brackets": [
        {
          "threshold": "0",
          "rate": "0.1000",
          "constant": "0",
          "description": "Up to $148,269"
        },
        {
          "threshold": "148269",
          "rate": "0.1200",
          "constant": "14827",
          "description": "$148,269 to $177,922"
        },
        {
          "threshold": "177922",
          "rate": "0.1300",
          "constant": "18393",
          "description": "$177,922 to $237,230"
        },
        {
          "threshold": "237230",
          "rate": "0.1400",
          "constant": "26103",
          "description": "$237,230 to $355,845"
        },
        {
          "threshold": "355845",
          "rate": "0.1500",
          "constant": "42709",
          "description": "$355,845 to $474,460"
        },
        {
          "threshold": "474460",
          "rate": "0.1600",
          "constant": "60501",
          "description": "Over $474,460"
        }
      ],
      "special_features": {
        "has_k5p_credit": true,
        "k5p_threshold": "3600.00",
        "k5p_rate_ratio": "0.6667"
      }
    },
    "BC": {
      "code": "BC",
      "name": "British Columbia",
      "basic_personal_amount": "12932.00",
      "bpa_is_dynamic": false,
      "indexing_rate": "0.015",
      "has_surtax": false,
      "has_health_premium": false,
      "has_tax_reduction": true,
      "lcp_rate": null,
      "lcp_max_amount": null,
      "tax_brackets": [
        {
          "threshold": "0",
          "rate": "0.0506",
          "constant": "0",
          "description": "Up to $47,937"
        },
        {
          "threshold": "47937",
          "rate": "0.0770",
          "constant": "2426",
          "description": "$47,937 to $95,875"
        },
        {
          "threshold": "95875",
          "rate": "0.1050",
          "constant": "6117",
          "description": "$95,875 to $110,076"
        },
        {
          "threshold": "110076",
          "rate": "0.1229",
          "constant": "7608",
          "description": "$110,076 to $133,664"
        },
        {
          "threshold": "133664",
          "rate": "0.1470",
          "constant": "10509",
          "description": "$133,664 to $181,232"
        },
        {
          "threshold": "181232",
          "rate": "0.1680",
          "constant": "17502",
          "description": "$181,232 to $252,752"
        },
        {
          "threshold": "252752",
          "rate": "0.2050",
          "constant": "29519",
          "description": "Over $252,752"
        }
      ]
    },
    "ON": {
      "code": "ON",
      "name": "Ontario",
      "basic_personal_amount": "12747.00",
      "bpa_is_dynamic": false,
      "indexing_rate": "0.025",
      "has_surtax": true,
      "has_health_premium": true,
      "has_tax_reduction": false,
      "lcp_rate": null,
      "lcp_max_amount": null,
      "tax_brackets": [
        {
          "threshold": "0",
          "rate": "0.0505",
          "constant": "0",
          "description": "Up to $51,446"
        },
        {
          "threshold": "51446",
          "rate": "0.0915",
          "constant": "2598",
          "description": "$51,446 to $102,894"
        },
        {
          "threshold": "102894",
          "rate": "0.1116",
          "constant": "7307",
          "description": "$102,894 to $150,000"
        },
        {
          "threshold": "150000",
          "rate": "0.1216",
          "constant": "12563",
          "description": "$150,000 to $220,000"
        },
        {
          "threshold": "220000",
          "rate": "0.1316",
          "constant": "21075",
          "description": "Over $220,000"
        }
      ]
    }
  }
}
```

**Note**: Full file would include all 12 provinces. Example shows AB, BC, ON for brevity.

### 3. CPP/EI Configuration

**File**: `backend/config/tax_tables/2025/jul/cpp_ei_2025_jul.json`

```json
{
  "metadata": {
    "year": 2025,
    "edition": "jul",
    "effective_date": "2025-01-01",
    "note": "CPP/EI rates change annually in January, not mid-year"
  },
  "cpp": {
    "ympe": "71200.00",
    "yampe": "76000.00",
    "basic_exemption": "3500.00",
    "base_rate": "0.0595",
    "additional_rate": "0.0100",
    "max_base_contribution": "3356.10",
    "max_additional_contribution": "480.00",
    "employer_matches_employee": true
  },
  "ei": {
    "mie": "65000.00",
    "employee_rate": "0.0170",
    "employer_rate": "0.0238",
    "max_premium": "1077.48",
    "employer_multiplier": "1.4"
  },
  "validation": {
    "cpp_max_calculation": "($71,200 - $3,500) × 5.95% = $3,356.10",
    "cpp2_max_calculation": "($76,000 - $71,200) × 1.00% = $480.00",
    "ei_max_calculation": "$65,000 × 1.70% = $1,077.48"
  }
}
```

### 4. Special Taxes Configuration

**File**: `backend/config/tax_tables/2025/jul/special_taxes_2025_jul.json`

```json
{
  "metadata": {
    "year": 2025,
    "edition": "jul",
    "effective_date": "2025-07-01",
    "note": "Ontario surtax/health premium and BC tax reduction"
  },
  "ontario": {
    "surtax": {
      "enabled": true,
      "thresholds": [
        {
          "basic_tax_min": "0",
          "basic_tax_max": "5710",
          "rate": "0",
          "description": "No surtax"
        },
        {
          "basic_tax_min": "5710",
          "basic_tax_max": "7307",
          "rate": "0.20",
          "base_threshold": "5710",
          "description": "20% on amount over $5,710"
        },
        {
          "basic_tax_min": "7307",
          "basic_tax_max": null,
          "rates": {
            "tier1_rate": "0.20",
            "tier1_threshold": "5710",
            "tier2_rate": "0.36",
            "tier2_threshold": "7307"
          },
          "description": "20% on amount over $5,710 + 36% on amount over $7,307"
        }
      ],
      "formula": "if T4 <= 5710: V1=0; elif T4 <= 7307: V1=0.20×(T4-5710); else: V1=0.20×(T4-5710)+0.36×(T4-7307)",
      "reference": "backend/rag/cra_tax/ontario_surtax_health_premium_2025.md"
    },
    "health_premium": {
      "enabled": true,
      "brackets": [
        {
          "income_min": "0",
          "income_max": "20000",
          "premium": "0",
          "formula": "0"
        },
        {
          "income_min": "20000",
          "income_max": "36000",
          "premium_cap": "300",
          "rate": "0.06",
          "base_income": "20000",
          "formula": "min(300, 0.06 × (A - 20000))"
        },
        {
          "income_min": "36000",
          "income_max": "48000",
          "premium_cap": "450",
          "base_premium": "300",
          "rate": "0.06",
          "base_income": "36000",
          "formula": "min(450, 300 + 0.06 × (A - 36000))"
        },
        {
          "income_min": "48000",
          "income_max": "72000",
          "premium_cap": "600",
          "base_premium": "450",
          "rate": "0.25",
          "base_income": "48000",
          "formula": "min(600, 450 + 0.25 × (A - 48000))"
        },
        {
          "income_min": "72000",
          "income_max": "200000",
          "premium_cap": "750",
          "base_premium": "600",
          "rate": "0.25",
          "base_income": "72000",
          "formula": "min(750, 600 + 0.25 × (A - 72000))"
        },
        {
          "income_min": "200000",
          "income_max": null,
          "premium_cap": "900",
          "base_premium": "750",
          "rate": "0.25",
          "base_income": "200000",
          "formula": "min(900, 750 + 0.25 × (A - 200000))"
        }
      ],
      "reference": "backend/rag/cra_tax/ontario_surtax_health_premium_2025.md"
    }
  },
  "british_columbia": {
    "tax_reduction": {
      "enabled": true,
      "max_reduction": "562.00",
      "full_reduction_threshold": "25020.00",
      "zero_reduction_threshold": "40807.00",
      "phase_out_rate": "0.0356",
      "formula": "if A <= 25020: S=562; elif A < 40807: S=562-(0.0356×(A-25020)); else: S=0",
      "reference": "backend/rag/cra_tax/bc_tax_reduction_2025.md",
      "calculation_notes": {
        "phase_out_range": "$25,020 to $40,807",
        "phase_out_income_range": "$15,787",
        "rate_derivation": "$562 / $15,787 = 0.0356 (3.56%)"
      }
    }
  }
}
```

---

## 🔧 Python Configuration Loader Design

### TaxYearConfigLoader Class

**File**: `backend/app/services/payroll/config_loader.py`

```python
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import date
from pydantic import BaseModel, Field

class ConfigMetadata(BaseModel):
    """Configuration file metadata"""
    year: int
    edition: str  # "jan" or "jul"
    effective_date: date
    t4127_edition: str
    source_url: Optional[str] = None
    created_date: Optional[date] = None
    verified_against_pdoc: bool = False

class TaxYearConfigLoader:
    """
    Loader for tax year configuration files

    Loads JSON configuration files and converts all monetary values
    to Python Decimal for precision.
    """

    CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "tax_tables"
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_config(
        cls,
        tax_year: int,
        edition: str,
        config_type: str
    ) -> Dict[str, Any]:
        """
        Load a configuration file for a specific tax year and edition

        Args:
            tax_year: Year (e.g., 2025)
            edition: "jan" or "jul"
            config_type: "federal", "provinces", "cpp_ei", or "special_taxes"

        Returns:
            Configuration dictionary with Decimal values

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        cache_key = f"{tax_year}_{edition}_{config_type}"

        # Check cache
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Build file path
        config_file = (
            cls.CONFIG_DIR /
            str(tax_year) /
            edition /
            f"{config_type}_{tax_year}_{edition}.json"
        )

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}\n"
                f"Expected: {config_type}_{tax_year}_{edition}.json"
            )

        # Load JSON
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Convert to Decimal
        config_data = cls._decimalize_config(config_data)

        # Validate
        cls._validate_config(config_data, config_type)

        # Cache and return
        cls._cache[cache_key] = config_data
        return config_data

    @classmethod
    def _decimalize_config(cls, config: Any) -> Any:
        """
        Recursively convert all string numbers to Decimal

        Handles nested dicts and lists.
        """
        if isinstance(config, dict):
            return {
                key: cls._decimalize_config(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [cls._decimalize_config(item) for item in config]
        elif isinstance(config, str):
            # Try to convert to Decimal if it looks like a number
            try:
                return Decimal(config)
            except:
                return config
        else:
            return config

    @classmethod
    def _validate_config(cls, config: Dict[str, Any], config_type: str):
        """
        Validate configuration structure

        Args:
            config: Configuration dictionary
            config_type: Type of configuration

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        # Check metadata
        if "metadata" not in config:
            errors.append(f"{config_type}: Missing 'metadata' section")

        # Type-specific validation
        if config_type == "federal":
            if "federal_tax" not in config:
                errors.append("Missing 'federal_tax' section")
            else:
                fed = config["federal_tax"]
                if "tax_brackets" not in fed:
                    errors.append("Missing 'tax_brackets'")
                elif not isinstance(fed["tax_brackets"], list):
                    errors.append("'tax_brackets' must be a list")
                elif len(fed["tax_brackets"]) != 5:
                    errors.append(f"Expected 5 federal brackets, got {len(fed['tax_brackets'])}")

        elif config_type == "provinces":
            if "provinces" not in config:
                errors.append("Missing 'provinces' section")
            else:
                provinces = config["provinces"]
                if len(provinces) != 12:
                    errors.append(f"Expected 12 provinces, got {len(provinces)}")

        elif config_type == "cpp_ei":
            if "cpp" not in config or "ei" not in config:
                errors.append("Missing 'cpp' or 'ei' section")

        if errors:
            raise ValueError(
                f"Configuration validation errors for {config_type}:\n" +
                "\n".join(f"  - {err}" for err in errors)
            )

    @classmethod
    def load_federal_config(cls, tax_year: int, edition: str) -> Dict[str, Any]:
        """Load federal tax configuration"""
        return cls.load_config(tax_year, edition, "federal")["federal_tax"]

    @classmethod
    def load_provincial_config(cls, tax_year: int, edition: str) -> Dict[str, Any]:
        """Load provincial tax configurations"""
        return cls.load_config(tax_year, edition, "provinces")["provinces"]

    @classmethod
    def load_cpp_ei_config(cls, tax_year: int, edition: str) -> Dict[str, Any]:
        """Load CPP and EI configurations"""
        config = cls.load_config(tax_year, edition, "cpp_ei")
        return {
            "cpp": config["cpp"],
            "ei": config["ei"]
        }

    @classmethod
    def load_special_taxes_config(cls, tax_year: int, edition: str) -> Dict[str, Any]:
        """Load special taxes (Ontario, BC)"""
        return cls.load_config(tax_year, edition, "special_taxes")

    @classmethod
    def get_current_config(cls, config_type: str) -> Dict[str, Any]:
        """
        Get configuration for the current tax year/edition

        Automatically determines year and edition based on current date.
        """
        today = date.today()
        year = today.year
        edition = "jan" if today.month < 7 else "jul"

        return cls.load_config(year, edition, config_type)

    @classmethod
    def clear_cache(cls):
        """Clear configuration cache (useful for testing)"""
        cls._cache.clear()
```

### Usage Examples

```python
from backend.app.services.payroll.config_loader import TaxYearConfigLoader
from decimal import Decimal

# Load federal tax config for July 2025
federal_config = TaxYearConfigLoader.load_federal_config(2025, "jul")
bpaf = federal_config["bpaf"]  # Returns: Decimal("16129.00")
brackets = federal_config["tax_brackets"]  # List of bracket dicts

# Load provincial configs
provinces = TaxYearConfigLoader.load_provincial_config(2025, "jul")
ontario = provinces["ON"]
ontario_bpa = ontario["basic_personal_amount"]  # Decimal("12747.00")

# Load CPP/EI
cpp_ei = TaxYearConfigLoader.load_cpp_ei_config(2025, "jul")
ympe = cpp_ei["cpp"]["ympe"]  # Decimal("71200.00")
ei_rate = cpp_ei["ei"]["employee_rate"]  # Decimal("0.0170")

# Load special taxes
special = TaxYearConfigLoader.load_special_taxes_config(2025, "jul")
ontario_surtax = special["ontario"]["surtax"]
bc_reduction = special["british_columbia"]["tax_reduction"]

# Automatic current config
current_federal = TaxYearConfigLoader.get_current_config("federal")
```

---

## 🔄 Tax Calculation Engine Integration

### Updated Tax Calculators

**Before** (hardcoded in `tax_tables_2025.py`):
```python
FEDERAL_TAX_CONFIG = {
    "bpaf": Decimal("16129.00"),
    "cea": Decimal("1471.00"),
    "tax_brackets": [...]
}
```

**After** (loaded from config):
```python
from .config_loader import TaxYearConfigLoader

class FederalTaxCalculator:
    def __init__(
        self,
        pay_periods_per_year: int = 26,
        tax_year: int = None,
        edition: str = None
    ):
        self.P = pay_periods_per_year

        # Load config for specific year/edition, or use current
        if tax_year and edition:
            self.config = TaxYearConfigLoader.load_federal_config(tax_year, edition)
        else:
            self.config = TaxYearConfigLoader.get_current_config("federal")["federal_tax"]

        self.bpaf = self.config["bpaf"]
        self.cea = self.config["cea"]
        self.brackets = self.config["tax_brackets"]
```

### Backward Compatibility

To maintain backward compatibility during migration:

```python
# Option 1: Keep hardcoded as fallback
try:
    config = TaxYearConfigLoader.load_federal_config(2025, "jul")
except FileNotFoundError:
    # Fallback to hardcoded (legacy)
    from .tax_tables_2025 import FEDERAL_TAX_CONFIG as config

# Option 2: Environment variable flag
import os
USE_CONFIG_FILES = os.getenv("PAYROLL_USE_CONFIG_FILES", "false").lower() == "true"

if USE_CONFIG_FILES:
    config = TaxYearConfigLoader.load_federal_config(2025, "jul")
else:
    from .tax_tables_2025 import FEDERAL_TAX_CONFIG as config
```

### Time-Travel Calculations

```python
def calculate_historical_payroll(
    employee_data: dict,
    pay_period_date: date
) -> PayrollResult:
    """
    Calculate payroll using tax rates effective for a specific date

    Args:
        employee_data: Employee and pay period information
        pay_period_date: Date of the pay period

    Returns:
        Payroll calculation result using historical tax rates
    """
    # Determine tax year and edition for that date
    year = pay_period_date.year
    edition = "jan" if pay_period_date.month < 7 else "jul"

    # Create calculators with historical configs
    cpp_calc = CPPCalculator(
        pay_periods_per_year=26,
        tax_year=year,
        edition=edition
    )

    fed_calc = FederalTaxCalculator(
        pay_periods_per_year=26,
        tax_year=year,
        edition=edition
    )

    # ... calculate using historical rates
```

---

## 📋 CRA Update Workflow

### When CRA Publishes New T4127 (e.g., January 2026)

**Step 1: Download and Review**
1. Download T4127 PDF from CRA website
2. Review changes from previous edition (diff tool recommended)
3. Note all changed values: tax brackets, BPA, CPP/EI limits, indexing rates

**Step 2: Create Configuration Files**
```bash
# Create directory
mkdir -p backend/config/tax_tables/2026/jan

# Create files
touch backend/config/tax_tables/2026/jan/federal_2026_jan.json
touch backend/config/tax_tables/2026/jan/provinces_2026_jan.json
touch backend/config/tax_tables/2026/jan/cpp_ei_2026_jan.json
touch backend/config/tax_tables/2026/jan/special_taxes_2026_jan.json
```

**Step 3: Populate JSON Files**
- Transcribe values from T4127 Table 8.1 (tax brackets)
- Update metadata with T4127 edition and effective date
- Use Decimal strings for all monetary values (e.g., `"16129.00"`, not `16129`)

**Step 4: Validate Against CRA PDOC**
```python
# backend/tests/test_config_validation.py

def test_2026_jan_federal_config():
    """Validate 2026 January federal config against CRA PDOC"""
    config = TaxYearConfigLoader.load_federal_config(2026, "jan")

    # Test against CRA PDOC examples
    calc = FederalTaxCalculator(26, tax_year=2026, edition="jan")

    # PDOC test case: Ontario employee, bi-weekly, $60k annual
    result = calc.calculate_tax_per_period(
        gross_per_period=Decimal("2307.69"),
        total_claim_amount=config["bpaf"],
        cpp_per_period=Decimal("100.00"),
        ei_per_period=Decimal("39.23")
    )

    # Verify against PDOC (±$1 tolerance)
    expected_from_pdoc = Decimal("205.00")
    assert abs(result - expected_from_pdoc) <= Decimal("1.00")
```

**Step 5: Run Validation Suite**
```bash
# Run all validation tests
pytest backend/tests/test_config_validation.py -v

# Expected output:
# ✓ test_2026_jan_federal_config
# ✓ test_2026_jan_provincial_configs (12 provinces)
# ✓ test_2026_jan_cpp_ei_config
# ✓ test_2026_jan_special_taxes
```

**Step 6: Update RAG Documentation** (if formulas changed)
- Update `backend/rag/cra_tax/*.md` if calculation logic changed
- Most T4127 updates only change values, not formulas

**Step 7: Git Commit**
```bash
git add backend/config/tax_tables/2026/
git commit -m "feat(payroll): add CRA T4127 2026 January edition tax tables

- Federal: BPAF $16,500 (indexed 2.3%)
- CPP: YMPE $73,200, YAMPE $78,000
- EI: MIE $67,000, rate 1.65%
- Provinces: All indexed per T4127 Table 8.1

Validated against CRA PDOC test cases.
Reference: T4127 122nd Edition, January 2026"
```

**Step 8: Deploy**
- No code changes needed!
- Deploy configuration files to production
- System automatically uses new rates based on `effective_date`

---

## ✅ Benefits & Trade-offs

### ✅ Benefits

1. **Zero-Code Tax Updates**
   - CRA publishes new T4127 → Create JSON files → Deploy
   - No need to modify Python code for rate changes
   - Reduces developer time from hours to minutes

2. **Historical Calculations**
   - Support "time-travel" payroll calculations
   - Example: "What was net pay for Jan 2024?" uses 2024/jan config
   - Essential for payroll corrections and audits

3. **Easy Auditing**
   - JSON files are human-readable
   - Version control tracks all changes
   - Easy to diff: `git diff 2025/jan 2025/jul`

4. **Reduced Error Risk**
   - Configuration validation catches structural errors
   - PDOC validation ensures calculation accuracy
   - Separate data from code logic

5. **Multi-Year Support**
   - Run payroll for multiple tax years simultaneously
   - Example: Process Q4 2025 payroll in January 2026

6. **Testing Flexibility**
   - Test with hypothetical rates (e.g., "What if CPP rate was 6%?")
   - Easier to create test fixtures

### ⚠️ Trade-offs

1. **Configuration Validation Complexity**
   - Need robust validation to catch malformed JSON
   - Mitigation: Comprehensive validation in `TaxYearConfigLoader`

2. **Configuration File Maintenance**
   - 4 files × 2 editions/year = 8 new files annually
   - Mitigation: Scripts to auto-generate JSON from T4127 PDF (future)

3. **Additional Testing**
   - Must validate each new configuration against CRA PDOC
   - Mitigation: Automated PDOC test suite

4. **Cache Management**
   - Need to manage config cache in long-running processes
   - Mitigation: Cache invalidation strategy in `TaxYearConfigLoader`

---

## 🚀 Implementation Phases

### Phase 0: Foundation (Week 1)

**Deliverables:**
1. Create JSON schema documentation
2. Implement `TaxYearConfigLoader` class
3. Write configuration validation tests
4. Create sample configs for 2025/jul

**Tasks:**
- [ ] Design JSON schema for all 4 config types
- [ ] Implement `TaxYearConfigLoader` with Decimal conversion
- [ ] Add validation logic for each config type
- [ ] Create `backend/config/tax_tables/` directory structure
- [ ] Write unit tests for config loader

**Validation:**
```bash
pytest backend/tests/test_config_loader.py -v
# Expected: 15+ tests passing
```

---

### Phase 1: Federal & Provincial Migration (Week 2-3)

**Deliverables:**
1. `federal_2025_jul.json` with all 5 brackets
2. `provinces_2025_jul.json` with all 12 provinces
3. Updated `FederalTaxCalculator` to use configs
4. Updated `ProvincialTaxCalculator` to use configs

**Tasks:**
- [ ] Transcribe federal tax data from T4127 Table 8.1
- [ ] Transcribe all 12 provincial tax tables
- [ ] Refactor `FederalTaxCalculator` to use `TaxYearConfigLoader`
- [ ] Refactor `ProvincialTaxCalculator` to use `TaxYearConfigLoader`
- [ ] Validate against CRA PDOC for all provinces

**Validation:**
```python
# Test all provinces against PDOC
for province in ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]:
    calc = ProvincialTaxCalculator(province, 26, tax_year=2025, edition="jul")
    # ... PDOC validation
```

---

### Phase 2: CPP/EI Migration (Week 4)

**Deliverables:**
1. `cpp_ei_2025_jul.json` with all limits and rates
2. Updated `CPPCalculator` to use configs
3. Updated `EICalculator` to use configs

**Tasks:**
- [ ] Create CPP/EI configuration JSON
- [ ] Refactor `CPPCalculator` to use `TaxYearConfigLoader`
- [ ] Refactor `EICalculator` to use `TaxYearConfigLoader`
- [ ] Validate CPP/EI maximums

**Validation:**
```python
# Verify CPP maximums
cpp_calc = CPPCalculator(26, tax_year=2025, edition="jul")
assert cpp_calc.config["max_base_contribution"] == Decimal("3356.10")
assert cpp_calc.config["max_additional_contribution"] == Decimal("480.00")
```

---

### Phase 3: Special Taxes Migration (Week 5)

**Deliverables:**
1. `special_taxes_2025_jul.json` with Ontario and BC formulas
2. Implemented Ontario surtax calculation
3. Implemented Ontario health premium calculation
4. Implemented BC tax reduction calculation

**Tasks:**
- [ ] Create special taxes configuration JSON
- [ ] Implement `calculate_ontario_surtax()` using config
- [ ] Implement `calculate_ontario_health_premium()` using config
- [ ] Implement `calculate_bc_tax_reduction()` using config
- [ ] Integrate into `ProvincialTaxCalculator`

**Validation:**
```python
# Test Ontario surtax
calc = ProvincialTaxCalculator("ON", 26, tax_year=2025, edition="jul")
result = calc.calculate_provincial_tax(...)
assert result["surtax_v1"] > Decimal("0")  # For high earners
assert result["health_premium_v2"] > Decimal("0")  # For income > $20k

# Test BC tax reduction
calc = ProvincialTaxCalculator("BC", 26, tax_year=2025, edition="jul")
result = calc.calculate_provincial_tax(...)
assert result["tax_reduction_s"] == Decimal("562")  # For low income
```

---

### Phase 4: Testing & PDOC Validation (Week 6)

**Deliverables:**
1. Comprehensive PDOC validation suite
2. Configuration validation tools
3. Migration from hardcoded to config complete

**Tasks:**
- [ ] Create PDOC test cases for all provinces
- [ ] Test time-travel calculations (2024 vs 2025)
- [ ] Performance testing (config loading overhead)
- [ ] Documentation updates

**Validation:**
```bash
# Run full PDOC validation suite
pytest backend/tests/test_pdoc_validation.py -v

# Expected: 50+ test cases covering:
# - All 12 provinces
# - Federal tax
# - CPP/EI
# - Ontario special taxes
# - BC tax reduction
# - Multiple income levels
# - Multiple pay frequencies
```

---

## 📚 Related Documentation

1. **Ontario Surtax & Health Premium**
   - Location: `backend/rag/cra_tax/ontario_surtax_health_premium_2025.md`
   - Formulas for V1 (surtax) and V2 (health premium)

2. **BC Tax Reduction**
   - Location: `backend/rag/cra_tax/bc_tax_reduction_2025.md`
   - Formula for Factor S calculation

3. **CRA T4127 Reference**
   - Location: `backend/rag/cra_tax/t4127-jul-25e.pdf`
   - Official source of all tax tables

4. **Phase 1: Data Layer**
   - Location: `docs/planning/payroll/01_phase1_data_layer.md`
   - Will be updated to reference config files

5. **Phase 2: Calculations**
   - Location: `docs/planning/payroll/02_phase2_calculations.md`
   - Will be updated to use `TaxYearConfigLoader`

---

## 🔍 Example: Complete Config-Based Calculation

```python
from backend.app.services.payroll.config_loader import TaxYearConfigLoader
from backend.app.services.payroll.payroll_engine import PayrollEngine
from backend.app.models.payroll import PayrollCalculationRequest, Province, PayPeriodFrequency
from decimal import Decimal
from datetime import date

# Calculate payroll for a specific historical date
pay_period_date = date(2025, 3, 15)  # March 15, 2025

# Determine tax config to use
year = pay_period_date.year
edition = "jan" if pay_period_date.month < 7 else "jul"

# Load configs
federal_config = TaxYearConfigLoader.load_federal_config(year, edition)
provincial_configs = TaxYearConfigLoader.load_provincial_config(year, edition)
cpp_ei_config = TaxYearConfigLoader.load_cpp_ei_config(year, edition)

# Create payroll engine
engine = PayrollEngine(tax_year=year, edition=edition)

# Employee request
request = PayrollCalculationRequest(
    employee_id="emp_001",
    province=Province.ON,
    pay_frequency=PayPeriodFrequency.BIWEEKLY,
    gross_pay=Decimal("2307.69"),
    federal_claim_amount=federal_config["bpaf"],  # Automatic from config
    provincial_claim_amount=provincial_configs["ON"]["basic_personal_amount"],
    rrsp_deduction=Decimal("100.00"),
    ytd_gross=Decimal("4615.38"),
    ytd_cpp=Decimal("200.00"),
    ytd_ei=Decimal("78.46")
)

# Calculate
result = engine.calculate_payroll(request)

print(f"Payroll for {pay_period_date} (using {year}/{edition} tax rates):")
print(f"  Gross: ${result.gross_pay}")
print(f"  CPP: ${result.cpp_employee}")
print(f"  EI: ${result.ei_employee}")
print(f"  Federal Tax: ${result.federal_tax}")
print(f"  Provincial Tax: ${result.provincial_tax}")
print(f"  Net Pay: ${result.net_pay}")
```

---

## 🎯 Success Criteria

Configuration architecture is considered successfully implemented when:

1. ✅ All tax calculations use configuration files (no hardcoded rates)
2. ✅ CRA PDOC validation passes for all 12 provinces
3. ✅ Configuration files exist for at least 2 tax years (e.g., 2024 and 2025)
4. ✅ Time-travel calculations work correctly
5. ✅ New T4127 edition can be added in < 2 hours
6. ✅ Configuration validation catches all structural errors
7. ✅ Performance impact < 5ms per payroll calculation

---

**Next Steps**:
- After approval of this design, proceed to **Phase 0** implementation
- Update Phase 1 and Phase 2 planning documents to reference this architecture
- Begin creating JSON schemas and `TaxYearConfigLoader` class

**Document Version**: 1.1
**Created**: 2025-10-08
**Updated**: 2025-12-17
**Status**: Implemented (with deviations from original design)

---

## 📋 Actual Implementation Notes (December 2025)

The configuration architecture was implemented with some simplifications from the original design. This section documents the actual implementation.

### Implemented Directory Structure

```
backend/
├── config/
│   └── tax_tables/
│       └── 2025/
│           ├── federal.json
│           ├── cpp_ei.json
│           └── provinces.json
```

**Key Differences from Design:**
- Uses flat year directory (`2025/`) instead of edition subdirectories (`2025/jan/`, `2025/jul/`)
- Simplified file naming without year/edition suffix (e.g., `federal.json` instead of `federal_2025_jul.json`)
- Special taxes (Ontario surtax, BC tax reduction) are embedded in `provinces.json` instead of separate file

### Configuration Loader Implementation

**File**: `backend/app/services/payroll/tax_tables.py`

The implementation uses module-level functions with LRU caching instead of the `TaxYearConfigLoader` class:

```python
# Actual API (module functions)
from backend.app.services.payroll.tax_tables import (
    get_federal_config,
    get_cpp_config,
    get_ei_config,
    get_province_config,
    calculate_dynamic_bpa
)

# Usage
federal = get_federal_config(year=2025)
bpaf = Decimal(str(federal["bpaf"]))

cpp = get_cpp_config(year=2025)
ympe = Decimal(str(cpp["ympe"]))

province = get_province_config("ON", year=2025)
bpa = Decimal(str(province["bpa"]))
```

### Field Naming Conventions

| Design Document | Actual Implementation |
|-----------------|----------------------|
| `basic_personal_amount` | `bpa` |
| `bpaf` | `bpaf` (same) |
| `employer_matches_employee: true` | `employer_rate_multiplier: 1.0` |
| `tax_brackets` | `brackets` |

### Features Implemented

- [x] JSON configuration files for federal, CPP/EI, and provincial taxes
- [x] Decimal precision for monetary values
- [x] LRU caching for configuration files
- [x] Dynamic BPA calculation (Manitoba, Nova Scotia, Yukon)
- [x] Tax bracket lookup utilities
- [x] Configuration validation

### Features Deferred

- [ ] Edition subdirectories (jan/jul) - Using single annual config
- [ ] Separate `special_taxes.json` - Embedded in provinces.json
- [ ] Multi-year support (2024 configs) - Only 2025 implemented
- [ ] Automatic edition detection based on date - Hardcoded to 2025
- [ ] `TaxYearConfigLoader` class API - Using simpler module functions

### Why the Simplifications?

1. **Single Annual Config**: CRA T4127 July 2025 edition covers the full year for most values. CPP/EI rates are annual (January). Separating by edition added complexity without immediate benefit.

2. **Module Functions vs Class**: Python module functions with `@lru_cache` provide the same benefits (caching, lazy loading) with simpler API.

3. **Embedded Special Taxes**: Ontario and BC special tax rules are tightly coupled to their province configs. Embedding them reduces file count and simplifies loading.

### Migration Path (if needed)

To add edition support in the future:
1. Create `2025/jul/` subdirectory
2. Move current files into `2025/jul/`
3. Update `_get_config_path()` to accept edition parameter
4. Add `get_current_edition()` helper based on date

The current implementation is sufficient for 2025 payroll processing. Enhanced historical calculation support can be added when multi-year requirements emerge.
