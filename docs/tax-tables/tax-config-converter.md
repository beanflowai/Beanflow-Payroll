# T4127 PDF to JSON Tax Config Converter

## Overview

CLI tool to convert CRA T4127 PDF documents into JSON tax configuration files using LLM-driven parsing.

- **Source**: `docs/tax-tables/` (T4127 PDFs by year/edition)
- **Target**: `backend/config/tax_tables/` (JSON files per year)
- **Location**: `backend/tools/tax_config_converter/`

---

## Features

- **LLM-driven parsing** - Uses GLM-4.7 with thinking mode for intelligent table extraction
- **Multi-edition support** - Handles January and July editions automatically
- **Schema validation** - Validates output against JSON schemas
- **Dry-run mode** - Preview extraction without writing files
- **Debug extraction** - Extract PDF text for inspection

---

## Why LLM over Regex?

| Aspect | Regex Approach | LLM Approach |
|--------|---------------|--------------|
| Robustness | Brittle, breaks on format changes | Understands context |
| Maintenance | New patterns each year | Prompts work across years |
| Complex data | Struggles with nested tables | Handles naturally |
| Province-specific | Needs custom parsers | Single prompt handles all |
| Development time | Days of pattern tuning | Hours of prompt design |

---

## Installation

### Dependencies

The tool requires optional dependencies. Install with:

```bash
cd backend
uv sync --extra tools
```

This adds:
- `PyMuPDF>=1.24.0` - PDF text extraction
- `zhipuai>=2.1.0` - GLM API client (智谱清言)

### API Key Setup

GLM API key required from [智谱清言](https://open.bigmodel.cn/):

```bash
# Option 1: Environment variable
export GLM_API_KEY="your-api-key"

# Option 2: .env file in backend/
echo 'GLM_API_KEY="your-api-key"' >> backend/.env
```

---

## Usage

### Convert PDF to JSON

```bash
cd backend

# Basic conversion
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/

# With options
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/ \
  --edition jan \
  --model glm-4.7 \
  --verbose

# Dry run (preview without writing)
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output output/ \
  --dry-run -v
```

### Validate Config Files

```bash
cd backend

# Validate a directory
uv run python -m tools.tax_config_converter validate \
  --config config/tax_tables/2025/
```

### Extract PDF Text (Debug)

```bash
cd backend

# List tables found
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf

# Save extracted text
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output extracted_text.txt

# Extract specific table
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --table 8.1 \
  --output table_8.1.txt
```

---

## CLI Options

### `convert` Command

| Option | Description | Default |
|--------|-------------|---------|
| `--pdf`, `-p` | Path to T4127 PDF file | Required |
| `--output`, `-o` | Output directory for JSON files | Required |
| `--edition`, `-e` | Edition type: `jan`, `jul`, `auto` | `auto` |
| `--model`, `-m` | GLM model to use | `glm-4.7` |
| `--no-thinking` | Disable GLM thinking mode | Enabled |
| `--skip-validation` | Skip schema validation | Validate |
| `--dry-run` | Preview without writing files | Write files |
| `-v`, `--verbose` | Enable debug logging | Info level |

### `validate` Command

| Option | Description | Default |
|--------|-------------|---------|
| `--config`, `-c` | Directory with JSON config files | Required |

### `extract` Command

| Option | Description | Default |
|--------|-------------|---------|
| `--pdf`, `-p` | Path to T4127 PDF file | Required |
| `--output`, `-o` | Output file for extracted text | Print summary |
| `--table`, `-t` | Extract specific table (e.g., `8.1`) | Full text |

---

## Architecture

```
backend/tools/tax_config_converter/
├── __init__.py
├── __main__.py           # Entry point
├── cli.py                # CLI interface
├── converter.py          # Main orchestrator
├── extractors/
│   ├── __init__.py
│   ├── pdf_extractor.py  # PDF text extraction (PyMuPDF)
│   └── glm_parser.py     # GLM API client (zhipuai)
├── prompts/
│   ├── __init__.py
│   ├── cpp_ei_prompt.py      # CPP/EI extraction prompt
│   ├── federal_prompt.py     # Federal tax extraction prompt
│   └── provinces_prompt.py   # Provincial tax extraction prompt
├── generators/
│   ├── __init__.py
│   └── json_generator.py     # JSON file generation
└── validators/
    ├── __init__.py
    └── schema_validator.py   # JSON schema validation
```

---

## Conversion Pipeline

```
┌─────────────────┐
│  T4127 PDF      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ PDF Extractor   │────▶│ Table Detection │
│ (PyMuPDF)       │     │ (Table 8.x)     │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ GLM Parser      │◀────│ Extraction      │
│ (zhipuai)       │     │ Prompts         │
└────────┬────────┘     └─────────────────┘
         │
         ├──────────────────────────────┐
         ▼                              ▼
┌─────────────────┐          ┌─────────────────┐
│ CPP/EI Data     │          │ Tax Brackets    │
└────────┬────────┘          └────────┬────────┘
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│ cpp_ei.json     │          │ federal_*.json  │
│                 │          │ provinces_*.json│
└────────┬────────┘          └────────┬────────┘
         │                            │
         └────────────┬───────────────┘
                      ▼
              ┌─────────────────┐
              │ Schema Validator│
              └─────────────────┘
```

---

## Output Files

For each year, the converter generates:

| File | Description | Source Tables |
|------|-------------|---------------|
| `cpp_ei.json` | CPP, CPP2, EI rates and limits | Tables 8.3-8.7 |
| `federal_jan.json` | Federal tax (Jan-Jun edition) | Tables 8.1, 8.2 |
| `federal_jul.json` | Federal tax (Jul-Dec edition) | Tables 8.1, 8.2 |
| `provinces_jan.json` | All 12 provinces (Jan-Jun) | Tables 8.1, 8.2 |
| `provinces_jul.json` | All 12 provinces (Jul-Dec) | Tables 8.1, 8.2 |

---

## Extraction Details

### CPP/EI Data (Tables 8.3-8.7)

Extracts:
- CPP base rate, additional rate (CPP2), YMPE, YAMPE, basic exemption
- QPP equivalents for Quebec
- EI rates and MIE (Maximum Insurable Earnings)

### Federal Tax (Tables 8.1, 8.2)

Extracts:
- Tax brackets (R values), constants (K, A)
- BPAF (Basic Personal Amount Federal)
- CEA (Canada Employment Amount)
- Indexing factor

### Provincial Tax (Tables 8.1, 8.2)

Extracts for all 12 provinces (AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT):
- Tax brackets and constants
- BPA (Basic Personal Amount)
- Province-specific features:
  - **AB**: K5P (age credit)
  - **BC**: Tax reduction (S, phase-out thresholds)
  - **MB/NS**: Dynamic BPA calculation
  - **ON**: Surtax + Health Premium
  - **PE**: Surtax
  - **YT**: K4P (additional deduction)

---

## Validation

### Schema Validation

Generated files are validated against JSON schemas in:
```
backend/config/tax_tables/schemas/
├── cpp_ei.schema.json
├── federal.schema.json
└── provinces.schema.json
```

### Sanity Checks

- Rate bounds: `0 < rate < 1`
- Threshold ordering: ascending
- Required fields present

### PDOC Integration

After conversion, validate against PDOC test suite:

```bash
cd backend
uv run pytest tests/payroll/pdoc/ -v
```

Target: 100% pass rate with $0.05 tolerance per component.

---

## Troubleshooting

### "GLM_API_KEY environment variable is required"

Set your API key:
```bash
export GLM_API_KEY="your-key-from-zhipu"
```

### "zhipuai package is required"

Install tools dependencies:
```bash
cd backend
uv sync --extra tools
```

### "Could not determine year from PDF"

The PDF metadata extraction failed. Try:
1. Check if the PDF is the correct T4127 document
2. Use `--edition jan` or `--edition jul` to specify manually
3. Run `extract` command to inspect PDF structure

### JSON validation errors

1. Review the error messages for specific field issues
2. Check the extracted data with `--dry-run -v`
3. Manually correct the output JSON if needed
4. Re-validate with `validate` command

---

## Related Documentation

- [Tax Tables README](./README.md) - Configuration structure overview
- [Annual Update Checklist](./annual-update-checklist.md) - Update procedure
- [Phase 2 Calculations](../02_phase2_calculations.md) - Calculation formulas
- [PDOC Validation](../test-plan/03_pdoc_validation.md) - Test methodology

---

## Technical Details

### GLM Configuration

```python
GLMParser(
    model="glm-4.7",
    enable_thinking=True,   # Deep reasoning for complex tables
    temperature=0.1,        # Low for deterministic extraction
    max_tokens=16384        # Handle large province outputs
)
```

### Text Truncation Limits

To fit GLM context window:
- CPP/EI: 20,000 chars
- Federal: 30,000 chars
- Provinces: 50,000 chars

### Prompt Design

Each prompt includes:
1. Extracted table text
2. Target JSON schema
3. Example output format
4. Clear extraction instructions

---

*Last updated: 2025-12-30*
