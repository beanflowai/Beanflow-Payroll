# Tax Tables Configuration Management

## Overview

This directory contains documentation for managing Canadian payroll tax tables in the Beanflow-Payroll system.

## Configuration Structure

```
backend/config/tax_tables/
├── 2024/                    # Historical (reference only)
├── 2025/                    # Current production
│   ├── cpp_ei.json         # CPP and EI configuration
│   ├── federal_jan.json    # Federal tax (Jan-Jun, 120th Edition)
│   ├── federal_jul.json    # Federal tax (Jul-Dec, 121st Edition)
│   ├── provinces_jan.json  # Provincial tax (Jan-Jun)
│   └── provinces_jul.json  # Provincial tax (Jul-Dec)
├── 2026/                    # Next year (incomplete)
│   ├── cpp_ei.json
│   ├── federal_jan.json
│   └── provinces_jan.json
└── schemas/                 # JSON Schema files for validation
```

## Configuration Metadata

Each configuration file includes a `_metadata` field for traceability:

```json
{
  "_metadata": {
    "version": "121st Edition",
    "effective_date": "2025-07-01",
    "source": {
      "document": "CRA T4127 Payroll Deductions Formulas",
      "edition": "121st Edition (July 2025)",
      "url": "https://...",
      "accessed_date": "2025-12-29"
    },
    "validation": {
      "pdoc_validated": true,
      "pdoc_validation_date": "2025-12-29",
      "test_cases_passed": 44
    },
    "changes_from_previous": [...],
    "last_updated": "2025-12-30",
    "updated_by": "claude-code"
  }
}
```

## Data Sources

| Config Type | Primary Source | Update Frequency |
|-------------|---------------|------------------|
| CPP/EI | CRA announcements | Annual (January) |
| Federal Tax | T4127 Table 8.1 | Semi-annual (Jan + Jul editions) |
| Provincial Tax | T4127 Provincial sections | Semi-annual (Jan + Jul editions) |

### Official CRA Resources

- **T4127 Payroll Deductions Formulas**: https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html
- **PDOC Calculator**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/payroll-deductions-online-calculator.html
- **CPP/EI Rates**: https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/payroll-deductions-contributions/cpp-contributions.html

## Annual Update Process

### Automated Conversion (Recommended)

Use the **Tax Config Converter** tool to automate PDF to JSON conversion:

```bash
cd backend
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/
```

See [tax-config-converter.md](./tax-config-converter.md) for full documentation.

### Manual Update Steps

1. **Obtain source documents** - Download T4127 PDF when released
2. **Follow checklist** - Use [annual-update-checklist.md](./annual-update-checklist.md)
3. **Add metadata** - Include source URLs and access dates
4. **Validate with PDOC** - Run 44+ test cases against CRA calculator
5. **Update log** - Document changes in yearly update log

## Validation

### PDOC Test Suite

Location: `backend/tests/payroll/pdoc/`

| Tier | Description | Test Cases |
|------|-------------|------------|
| Tier 1 | Province coverage | 12 |
| Tier 2 | Income levels | 12 |
| Tier 3 | CPP/EI boundaries | 8 |
| Tier 4 | Special conditions | 8 |
| Tier 5 | Federal rate change | 4 |

**Total**: 44 test cases with $0.05 tolerance per component

### Running Tests

```bash
cd backend
uv run pytest tests/payroll/pdoc/ -v
```

## Key Dates

| Edition | Effective Date | Notes |
|---------|---------------|-------|
| 120th (Jan 2025) | 2025-01-01 | Federal rate 15% |
| 121st (Jul 2025) | 2025-07-01 | Federal rate 14% |
| 122nd (Jan 2026) | 2026-01-01 | Awaiting PDOC validation |

## Related Documentation

- [Tax Config Converter](./tax-config-converter.md) - Automated PDF to JSON conversion tool
- [Annual Update Checklist](./annual-update-checklist.md) - Manual update procedure
- [Phase 2 Calculations](../02_phase2_calculations.md) - Calculation formulas
- [PDOC Validation Test Plan](../test-plan/03_pdoc_validation.md) - Test methodology
