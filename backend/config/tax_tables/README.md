# Tax Tables Configuration

Canadian payroll tax configuration files for CPP, EI, federal tax, and provincial tax calculations.

## Official Data Source

**All tax data must be sourced from the official CRA T4127 Payroll Deductions Formulas:**

https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/t4127-payroll-deductions-formulas-computer-programs.html

### Edition Schedule

| Edition | Effective Date | Notes |
|---------|---------------|-------|
| 121st | January 1, 2025 | Current year start |
| 122nd | January 1, 2026 | Next year |
| 123rd | July 1, 2026 (expected) | Mid-year update |

CRA typically releases two editions per year:
- **January Edition**: Released in late December for January 1 effective date
- **July Edition**: Released in late June for July 1 effective date (if rates change)

## Directory Structure

```
tax_tables/
├── schemas/                    # JSON Schema definitions
│   ├── cpp_ei.schema.json     # CPP/EI configuration schema
│   ├── federal.schema.json    # Federal tax schema
│   └── provinces.schema.json  # Provincial tax schema
├── 2024/                       # Tax year 2024
│   ├── cpp_ei.json            # CPP/EI (single file - rates don't change mid-year)
│   ├── federal_jan.json       # Federal tax (January edition)
│   ├── federal_jul.json       # Federal tax (July edition)
│   ├── provinces_jan.json     # Provincial tax (January edition)
│   └── provinces_jul.json     # Provincial tax (July edition)
├── 2025/                       # Tax year 2025
│   ├── cpp_ei.json            # CPP/EI (single file - rates don't change mid-year)
│   ├── federal_jan.json       # Federal tax (January edition)
│   ├── federal_jul.json       # Federal tax (July edition)
│   ├── provinces_jan.json     # Provincial tax (January edition)
│   └── provinces_jul.json     # Provincial tax (July edition)
├── 2026/                       # Tax year 2026
│   └── ...                    # Same structure
└── README.md                   # This file
```

## Schema Validation

All JSON configuration files must conform to their respective schemas in the `schemas/` directory.

### Validation Requirements

1. **Schema Consistency**: When adding new fields to JSON files, update the corresponding schema first
2. **additionalProperties: false**: Schemas are strict - unknown fields will fail validation
3. **Required Fields**: Check schema for mandatory fields before adding new configurations

### Running Validation

```bash
# Using Python jsonschema
cd backend
uv run python -c "
import json
from jsonschema import validate

with open('config/tax_tables/schemas/provinces.schema.json') as f:
    schema = json.load(f)
with open('config/tax_tables/2026/provinces_jan.json') as f:
    data = json.load(f)
validate(data, schema)
print('Validation passed!')
"
```

## Update Workflow

When CRA releases a new T4127 edition:

### 1. Obtain Official Document

1. Visit the CRA T4127 page (link above)
2. Download the PDF for the new edition
3. Note the edition number and effective date

### 2. Update Configuration Files

1. Create or update the appropriate JSON files
2. Update `_metadata` section with:
   - `version`: T4127 edition number
   - `effective_date`: When rates take effect
   - `source.edition`: Full edition reference
   - `source.accessed_date`: When you accessed the data
   - `last_updated`: Current date
   - `updated_by`: Your identifier

### 3. Update Schema (if needed)

If adding new fields:
1. Update the schema in `schemas/` first
2. Document the new field with description
3. Run validation to ensure existing files still pass

### 4. Validate and Test

1. Run schema validation (see above)
2. Run PDOC tests: `uv run pytest tests/payroll/pdoc/`
3. Verify calculations match CRA PDOC calculator

## Key Configuration Fields

### Provincial Tax (`provinces.schema.json`)

| Field | Description |
|-------|-------------|
| `bpa` | Basic Personal Amount |
| `bpa_is_dynamic` | Whether BPA varies by income |
| `brackets[]` | Tax brackets with threshold, rate, constant |
| `surtax_config` | ON/PE surtax configuration |
| `health_premium_config` | Ontario health premium |
| `tax_reduction_config` | BC tax reduction |
| `k5p_config` | Alberta supplemental tax credit (K5P) |

### K5P Configuration (Alberta Only)

K5P formula: `K5P = ((K1P + K2P) - threshold) × factor`

**2025 format** (factor as fraction):
```json
"k5p_config": {
  "threshold": 3600.00,
  "factor_numerator": 0.04,
  "factor_denominator": 0.06,
  "description": "K5P = ((K1P + K2P) - threshold) × (0.04/0.06)"
}
```

**2026+ format** (factor as decimal):
```json
"k5p_config": {
  "threshold": 4896.00,
  "factor": 0.25,
  "description": "K5P = ((K1P + K2P) - threshold) × 0.25"
}
```

## References

- [CRA T4127 Payroll Deductions Formulas](https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html)
- [CRA PDOC Calculator](https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/payroll-deductions-online-calculator.html)
- [TaxTips.ca](https://www.taxtips.ca/) - Secondary reference for tax rates
