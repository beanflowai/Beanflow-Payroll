"""
Provincial Tax Extraction Prompt for T4127 PDF

Extracts all 12 provincial/territorial tax configurations from Table 8.1.
"""

import json


PROVINCE_EXAMPLE = {
    "AB": {
        "name": "Alberta",
        "code": "AB",
        "bpa": 22323.00,
        "bpa_is_dynamic": False,
        "indexing_rate": 0.02,
        "has_surtax": False,
        "has_health_premium": False,
        "has_tax_reduction": False,
        "k5p_config": {
            "threshold": 3600.00,
            "factor_numerator": 0.04,
            "factor_denominator": 0.06
        },
        "brackets": [
            {"threshold": 0, "rate": 0.10, "constant": 0},
            {"threshold": 151234, "rate": 0.12, "constant": 3025},
            {"threshold": 181481, "rate": 0.13, "constant": 4839},
            {"threshold": 241974, "rate": 0.14, "constant": 7259},
            {"threshold": 362961, "rate": 0.15, "constant": 10889}
        ]
    },
    "ON": {
        "name": "Ontario",
        "code": "ON",
        "bpa": 12747.00,
        "bpa_is_dynamic": False,
        "indexing_rate": 0.027,
        "has_surtax": True,
        "has_health_premium": True,
        "has_tax_reduction": False,
        "surtax_config": {
            "first_threshold": 5710.00,
            "first_rate": 0.20,
            "second_threshold": 7307.00,
            "second_rate": 0.36
        },
        "health_premium_config": {
            "brackets": [
                {"threshold": 0, "premium": 0},
                {"threshold": 20000, "premium": 0, "rate": 0.06, "base": 0},
                {"threshold": 25000, "premium": 300},
                {"threshold": 36000, "premium": 300, "rate": 0.06, "base": 300},
                {"threshold": 38500, "premium": 450},
                {"threshold": 48000, "premium": 450, "rate": 0.25, "base": 450},
                {"threshold": 48600, "premium": 600},
                {"threshold": 72000, "premium": 600, "rate": 0.25, "base": 600},
                {"threshold": 72600, "premium": 750},
                {"threshold": 200000, "premium": 750, "rate": 0.25, "base": 750},
                {"threshold": 200600, "premium": 900}
            ]
        },
        "brackets": [
            {"threshold": 0, "rate": 0.0505, "constant": 0},
            {"threshold": 52886, "rate": 0.0915, "constant": 2168},
            {"threshold": 105775, "rate": 0.1116, "constant": 4294},
            {"threshold": 150000, "rate": 0.1216, "constant": 5794},
            {"threshold": 220000, "rate": 0.1316, "constant": 7994}
        ]
    },
    "BC": {
        "name": "British Columbia",
        "code": "BC",
        "bpa": 12932.00,
        "bpa_is_dynamic": False,
        "indexing_rate": 0.027,
        "has_surtax": False,
        "has_health_premium": False,
        "has_tax_reduction": True,
        "tax_reduction_config": {
            "base_reduction": 562.00,
            "reduction_rate": 0.0356,
            "phase_out_start": 25020.00,
            "phase_out_end": 40807.00
        },
        "brackets": [
            {"threshold": 0, "rate": 0.0506, "constant": 0}
        ]
    }
}


# Note: Quebec (QC) is excluded because it has its own independent tax system
# administered by Revenu Québec, not covered by CRA T4127.
# Quebec employers must use TP-1015.F-V instead.
PROVINCE_CODES = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]

PROVINCE_NAMES = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "SK": "Saskatchewan",
    "YT": "Yukon"
}


def create_provinces_prompt(table_text: str, year: int, effective_date: str) -> str:
    """
    Create prompt for extracting all provincial tax data from T4127 Table 8.1.

    Args:
        table_text: Text from Table 8.1 (all provincial sections)
        year: Tax year (e.g., 2025)
        effective_date: Effective date (e.g., "2025-01-01")

    Returns:
        Formatted prompt for GLM
    """
    return f"""You are a Canadian payroll tax expert. Extract ALL provincial/territorial income tax data from CRA T4127.

## Task
Parse tax data for all 12 provinces/territories: {', '.join(PROVINCE_CODES)}

## Source Text
{table_text}

## Example Output Format (showing 3 provinces)
```json
{json.dumps(PROVINCE_EXAMPLE, indent=2)}
```

## Province/Territory Names
{json.dumps(PROVINCE_NAMES, indent=2)}

## Field Definitions

### Required Fields for ALL Provinces:
- **name**: Full province name
- **code**: 2-letter code (AB, BC, etc.)
- **bpa**: Basic Personal Amount (provincial)
- **bpa_is_dynamic**: Boolean - true if BPA varies by income
- **brackets**: Array of tax brackets with threshold, rate, constant

### Conditional Fields:
- **indexing_rate**: If province uses indexing (decimal, e.g., 0.027 for 2.7%), null if no indexing
- **has_surtax**: true for ON, PE (provinces with surtax)
- **has_health_premium**: true for ON only
- **has_tax_reduction**: true for BC only
- **has_k4p**: true for YT only (employment credit)
- **cea**: Employment amount for YT

### Special Configurations (if applicable):

**Dynamic BPA (MB, NS, YT)**:
```json
"dynamic_bpa_type": "income_based_reduction" | "income_based_increase" | "follows_federal",
"dynamic_bpa_config": {{
    "base_bpa": 15969.00,
    "reduction_start": 200000.00,
    "reduction_end": 400000.00,
    "min_bpa": 0.00
}}
```

**Surtax (ON - two tier)**:
```json
"surtax_config": {{
    "first_threshold": 5710.00,
    "first_rate": 0.20,
    "second_threshold": 7307.00,
    "second_rate": 0.36
}}
```

**Surtax (PE - single threshold)**:
```json
"surtax_config": {{
    "threshold": 13500.00,
    "rate": 0.10
}}
```

**Health Premium (ON only)**:
```json
"health_premium_config": {{
    "brackets": [
        {{"threshold": 0, "premium": 0}},
        {{"threshold": 20000, "premium": 0, "rate": 0.06, "base": 0}},
        ...
    ]
}}
```

**Tax Reduction (BC only)**:
```json
"tax_reduction_config": {{
    "base_reduction": 562.00,
    "reduction_rate": 0.0356,
    "phase_out_start": 25020.00,
    "phase_out_end": 40807.00
}}
```

**K5P Config (AB only)**:
```json
"k5p_config": {{
    "threshold": 3600.00,
    "factor_numerator": 0.04,
    "factor_denominator": 0.06
}}
```

## How to Find Values in T4127 Table 8.1

For each province, look for:
1. Tax brackets: R (threshold), V (rate), KP (constant)
2. Basic Personal Amount: TCP or BPA value
3. Special features based on province abbreviation

## Instructions
1. Extract data for ALL 12 provinces/territories
2. Set boolean flags correctly:
   - MB, NS have dynamic BPA (income-based)
   - YT BPA follows federal
   - ON has surtax AND health premium
   - PE has surtax only
   - BC has tax reduction
   - AB has K5P
   - YT has K4P (employment credit)
3. Include special configs only for provinces that have them
4. Return ONLY valid JSON

## Important Notes
- All rates as decimals (15% = 0.15)
- Dollar amounts without $ symbol
- Include all 12 provinces
- This is for year {year}, effective {effective_date}

Return ONLY the JSON object with all 12 provinces, no other text."""
