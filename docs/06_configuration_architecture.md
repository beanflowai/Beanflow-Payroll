# Phase 6: Configuration Architecture & Parameterization

**Status**: ✅ Implemented
**Complexity**: Medium
**Prerequisites**: Phase 1-5 completed

> **Last Updated**: 2025-12-31
> **Implementation**: Completed December 2025

---

## Objectives

Design a configuration-driven architecture that externalizes all tax rates, thresholds, and formulas to JSON files, enabling zero-code updates when CRA publishes new T4127 editions.

### Problem Solved

| Challenge | Solution |
|-----------|----------|
| CRA publishes T4127 twice per year | JSON config files updated without code changes |
| 12 provinces × multiple tax brackets | Centralized `provinces.json` with all provinces |
| Risk of transcription errors | Schema validation + PDOC test suite |
| Historical calculation needs | Version-controlled configs by year |

---

## Architecture Overview

### Directory Structure

```
backend/config/tax_tables/
├── schemas/                    # JSON Schema definitions
│   ├── cpp_ei.schema.json
│   ├── federal.schema.json
│   └── provinces.schema.json
├── 2024/                       # Tax year 2024
│   ├── cpp_ei.json
│   ├── federal_jan.json
│   ├── federal_jul.json
│   ├── provinces_jan.json
│   └── provinces_jul.json
├── 2025/                       # Tax year 2025
│   └── [same structure]
├── 2026/                       # Tax year 2026
│   └── [same structure]
└── README.md
```

### Configuration Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `federal_*.json` | Federal tax brackets, BPA, CEA | Every T4127 edition |
| `provinces_*.json` | 12 provincial tax tables, special features | Every T4127 edition |
| `cpp_ei.json` | CPP/EI rates, maximums, exemptions | Annually (January) |

**Note**: Special taxes (Ontario surtax/health premium, BC tax reduction) are embedded in `provinces_*.json`.

---

## Configuration Loader API

### File Location

`backend/app/services/payroll/tax_tables.py`

### Key Functions

| Function | Description |
|----------|-------------|
| `get_federal_config(year, pay_date)` | Load federal tax config with auto edition selection |
| `get_cpp_config(year)` | Load CPP rates and limits |
| `get_ei_config(year)` | Load EI rates and limits |
| `get_province_config(code, year, pay_date)` | Load provincial tax config |
| `find_tax_bracket(income, brackets)` | Find applicable tax rate for income |
| `calculate_dynamic_bpa(...)` | Calculate dynamic BPA (MB, NS, YT) |
| `validate_tax_tables(year)` | Validate all config files for a year |

### Usage

```python
from app.services.payroll.tax_tables import (
    get_federal_config, get_cpp_config, get_province_config
)
from decimal import Decimal

# Load configs
federal = get_federal_config(year=2025, pay_date=date(2025, 3, 15))
cpp = get_cpp_config(year=2025)
ontario = get_province_config("ON", year=2025, pay_date=date(2025, 3, 15))

# Access values
bpaf = Decimal(str(federal["bpaf"]))      # $16,129
ympe = Decimal(str(cpp["ympe"]))          # $71,300
on_bpa = Decimal(str(ontario["bpa"]))     # $12,747
```

### Features

- **Automatic edition selection**: Detects Jan/Jul based on `pay_date`
- **LRU caching**: Frequently accessed configs are cached
- **Schema validation**: Validates bracket ordering, required fields
- **Decimal precision**: All monetary values maintain precision

---

## Pay Group Tax Configuration

Pay Groups can specify which CRA-approved tax calculation method to use:

| Value | Method | Status |
|-------|--------|--------|
| `annualization` | Option 1 - Annual Tax Method | ✅ Implemented |
| `cumulative_averaging` | Option 2 - Cumulative Averaging | 🔜 Future |

**Database**: `pay_groups.tax_calculation_method`
**TypeScript**: `TaxCalculationMethod = 'annualization' | 'cumulative_averaging'`

---

## Special Provincial Features

### Dynamic BPA

Some provinces have income-dependent Basic Personal Amount:

| Province | Behavior |
|----------|----------|
| Manitoba | BPA reduces above $200,000 income |
| Nova Scotia | BPA increases for $25,000-$75,000 income |
| Yukon | Follows federal BPA formula |

### Province-Specific Tax Features

| Province | Feature | Config Location |
|----------|---------|-----------------|
| Ontario | Surtax (V1) | `provinces.json` → `ON.surtax` |
| Ontario | Health Premium (V2) | `provinces.json` → `ON.health_premium` |
| British Columbia | Tax Reduction (S) | `provinces.json` → `BC.tax_reduction` |
| Alberta | K5P Credit | `provinces.json` → `AB.k5p` |

---

## CRA T4127 Update Workflow

When CRA publishes a new T4127 edition:

### Step 1: Download PDF
Download from [CRA T4127 page](https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html)

### Step 2: Run Converter Tool

```bash
cd backend
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2026/01/t4127-01-26e.pdf \
  --output config/tax_tables/2026/
```

### Step 3: Validate Against PDOC

```bash
uv run pytest tests/payroll/pdoc/ -v
```

### Step 4: Deploy
- No code changes needed
- Deploy configuration files to production

**Time Required**: ~2 hours (mostly validation)

---

## T4127 PDF Converter Tool

### Location

`backend/tools/tax_config_converter/`

### Components

| Component | Purpose |
|-----------|---------|
| `PDFExtractor` | Extract text/tables from T4127 PDF |
| `GLMParser` / `GeminiParser` | LLM-based data extraction |
| `JSONGenerator` | Generate final config JSON |
| `SchemaValidator` | Validate against schemas |

### Conversion Steps

```bash
# Step-by-step (resumable)
--step extract      # Extract PDF text (~1 sec)
--step cpp-ei       # Parse CPP/EI (~40 sec)
--step federal      # Parse federal tax (~1.5 min)
--step provinces    # Parse all provinces (~4 min)
--step generate     # Generate final files

# Full conversion
uv run python -m tools.tax_config_converter convert --pdf <path> --output <dir>
```

---

## Implementation Status

| Requirement | Status |
|-------------|--------|
| JSON configuration files (2024-2026) | ✅ Complete |
| Tax config loader with caching | ✅ Complete |
| Federal tax calculator integration | ✅ Complete |
| Provincial tax calculator integration | ✅ Complete |
| Dynamic BPA (MB, NS, YT) | ✅ Complete |
| Special features (surtax, health premium, K5P) | ✅ Complete |
| T4127 PDF converter tool | ✅ Complete |
| Schema validation | ✅ Complete |
| PDOC validation test suite | ✅ Complete |

---

## Related Files

### Configuration

| File | Description |
|------|-------------|
| `backend/config/tax_tables/` | All tax configuration JSON files |
| `backend/config/tax_tables/schemas/` | JSON Schema definitions |
| `backend/config/tax_tables/README.md` | Configuration update guide |

### Implementation

| File | Description |
|------|-------------|
| `backend/app/services/payroll/tax_tables.py` | Configuration loader |
| `backend/app/services/payroll/federal_tax_calculator.py` | Federal tax calculation |
| `backend/app/services/payroll/provincial_tax_calculator.py` | Provincial tax calculation |
| `backend/tools/tax_config_converter/` | PDF to JSON converter |

### Tests

| File | Description |
|------|-------------|
| `backend/tests/payroll/pdoc/` | PDOC validation test suite |
| `backend/tests/payroll/test_tax_tables.py` | Config loader tests |

---

## Benefits

1. **Zero-code updates**: CRA T4127 → JSON files → Deploy
2. **Historical calculations**: Time-travel payroll using versioned configs
3. **Easy auditing**: Human-readable JSON, version controlled
4. **Reduced errors**: Schema validation + PDOC test suite
5. **Multi-year support**: Run 2024/2025/2026 calculations simultaneously

---

**Next**: [Phase 7: Remittance Reporting](./10_remittance_reporting.md)
