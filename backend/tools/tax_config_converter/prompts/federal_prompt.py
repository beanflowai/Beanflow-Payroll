"""
Federal Tax Extraction Prompt for T4127 PDF

Extracts federal tax brackets and credits from Table 8.1.
"""

import json

FEDERAL_EXAMPLE = {
    "bpaf": 16129.00,
    "cea": 1471.00,
    "indexing_rate": 0.027,
    "brackets": [
        {"threshold": 0, "rate": 0.15, "constant": 0},
        {"threshold": 57375, "rate": 0.205, "constant": 3156},
        {"threshold": 114750, "rate": 0.26, "constant": 9467},
        {"threshold": 177882, "rate": 0.29, "constant": 14803},
        {"threshold": 253414, "rate": 0.33, "constant": 24940}
    ],
    "k1_rate": 0.15,
    "k2_cpp_ei_rate": 0.15,
    "k4_canada_employment_rate": 0.15
}


def create_federal_prompt(table_text: str, year: int, effective_date: str) -> str:
    """
    Create prompt for extracting federal tax data from T4127 Table 8.1.

    Args:
        table_text: Text from Table 8.1 (federal section)
        year: Tax year (e.g., 2025)
        effective_date: Effective date (e.g., "2025-01-01")

    Returns:
        Formatted prompt for GLM
    """
    return f"""You are a Canadian payroll tax expert. Extract FEDERAL income tax data from the CRA T4127 Table 8.1.

## Task
Parse the federal tax brackets, credits, and rates from Table 8.1 and return a JSON object.

## Source Text (Table 8.1 - Federal Section)
{table_text}

## Expected Output Format
```json
{json.dumps(FEDERAL_EXAMPLE, indent=2)}
```

## Field Definitions

### Main Fields:
- **bpaf**: Basic Personal Amount Federal - the federal basic personal amount credit
- **cea**: Canada Employment Amount - the employment credit amount
- **indexing_rate**: Annual indexing rate as decimal (e.g., 2.7% = 0.027)

### Tax Brackets:
Each bracket has:
- **threshold**: Income threshold (R value) where this bracket starts
- **rate**: Marginal tax rate as decimal (e.g., 15% = 0.15)
- **constant**: Tax constant (K value) for this bracket

### Credit Rates:
- **k1_rate**: Rate for calculating K1 (personal credits) - typically 0.15
- **k2_cpp_ei_rate**: Rate for calculating K2 (CPP/EI credits) - typically 0.15
- **k4_canada_employment_rate**: Rate for K4 (employment credit) - typically 0.15

## How to Find Values in T4127

### Tax Brackets (Table 8.1):
Look for the federal section showing R (threshold), V (rate), and K (constant):
- R values are income thresholds (0, 57375, 114750, etc.)
- V values are tax rates shown as percentages (15%, 20.5%, 26%, etc.)
- K values are the constants (0, 3156, 9467, etc.)

### Basic Personal Amount (BPAF):
Look for "TC" or "Basic personal amount" in the federal section

### Canada Employment Amount (CEA):
Look for "Canada employment amount" or employment credit value

### Indexing Rate:
Look for "indexation" or "indexing factor" (typically around 2-3%)

## Instructions
1. Find the federal tax bracket table with R, V, K columns
2. Extract all bracket thresholds (R), rates (V), and constants (K)
3. Find BPAF and CEA values
4. Find the indexing rate if available (set to null if not found)
5. The K1, K2, K4 rates are typically all 0.15 (lowest federal rate)
6. Return ONLY valid JSON

## Important Notes
- All rates must be decimals (15% = 0.15, NOT 15)
- All dollar amounts as numbers without $ symbol
- Constants (K values) should match exactly from the table
- This is for year {year}, effective {effective_date}
- There are typically 5 federal tax brackets

Return ONLY the JSON object, no other text."""
