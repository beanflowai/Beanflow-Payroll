"""
Single Province Tax Extraction Prompt for T4127 PDF

Extracts tax configuration for one province at a time.
Used for sequential processing to avoid timeout issues.
"""

import json

# Province-specific information for targeted extraction
PROVINCE_INFO = {
    "AB": {
        "name": "Alberta",
        "features": ["k5p_config"],
        "notes": "Has K5P (employment income exemption). No surtax, no health premium."
    },
    "BC": {
        "name": "British Columbia",
        "features": ["tax_reduction_config"],
        "notes": "Has tax reduction. No surtax, no health premium."
    },
    "MB": {
        "name": "Manitoba",
        "features": ["dynamic_bpa"],
        "notes": "Has dynamic BPA (income-based reduction). No surtax."
    },
    "NB": {
        "name": "New Brunswick",
        "features": [],
        "notes": "Standard province. No special features."
    },
    "NL": {
        "name": "Newfoundland and Labrador",
        "features": [],
        "notes": "Standard province. No special features."
    },
    "NS": {
        "name": "Nova Scotia",
        "features": ["dynamic_bpa"],
        "notes": "Has dynamic BPA (income-based). No surtax."
    },
    "NT": {
        "name": "Northwest Territories",
        "features": [],
        "notes": "Standard territory. No special features."
    },
    "NU": {
        "name": "Nunavut",
        "features": [],
        "notes": "Standard territory. No special features."
    },
    "ON": {
        "name": "Ontario",
        "features": ["surtax_config", "health_premium_config"],
        "notes": "Has two-tier surtax AND health premium. Most complex province."
    },
    "PE": {
        "name": "Prince Edward Island",
        "features": ["surtax_config"],
        "notes": "Has single-tier surtax. No health premium."
    },
    "SK": {
        "name": "Saskatchewan",
        "features": [],
        "notes": "Standard province. No special features."
    },
    "YT": {
        "name": "Yukon",
        "features": ["dynamic_bpa", "k4p"],
        "notes": "BPA follows federal. Has K4P employment credit (CEA)."
    }
}

# Example outputs by province type
EXAMPLE_STANDARD = {
    "name": "New Brunswick",
    "code": "NB",
    "bpa": 13396.00,
    "bpa_is_dynamic": False,
    "indexing_rate": 0.027,
    "has_surtax": False,
    "has_health_premium": False,
    "has_tax_reduction": False,
    "brackets": [
        {"threshold": 0, "rate": 0.094, "constant": 0},
        {"threshold": 49958, "rate": 0.14, "constant": 2298},
        {"threshold": 99916, "rate": 0.16, "constant": 4296},
        {"threshold": 185064, "rate": 0.195, "constant": 10773}
    ]
}

EXAMPLE_WITH_SURTAX_ON = {
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
}

EXAMPLE_WITH_DYNAMIC_BPA = {
    "name": "Manitoba",
    "code": "MB",
    "bpa": 15969.00,
    "bpa_is_dynamic": True,
    "dynamic_bpa_type": "income_based_reduction",
    "dynamic_bpa_config": {
        "base_bpa": 15969.00,
        "reduction_start": 200000.00,
        "reduction_end": 400000.00,
        "min_bpa": 0.00
    },
    "indexing_rate": None,
    "has_surtax": False,
    "has_health_premium": False,
    "has_tax_reduction": False,
    "brackets": [
        {"threshold": 0, "rate": 0.108, "constant": 0},
        {"threshold": 47000, "rate": 0.1275, "constant": 917},
        {"threshold": 100000, "rate": 0.174, "constant": 5562}
    ]
}

EXAMPLE_WITH_K5P = {
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
}


def _get_example_for_province(province_code: str) -> dict:
    """Get the most relevant example for a given province."""
    info = PROVINCE_INFO.get(province_code, {})
    features = info.get("features", [])

    if "health_premium_config" in features:
        return EXAMPLE_WITH_SURTAX_ON
    elif "surtax_config" in features:
        return EXAMPLE_WITH_SURTAX_ON  # PE uses same structure
    elif "dynamic_bpa" in features:
        return EXAMPLE_WITH_DYNAMIC_BPA
    elif "k5p_config" in features:
        return EXAMPLE_WITH_K5P
    else:
        return EXAMPLE_STANDARD


def _get_special_instructions(province_code: str) -> str:
    """Get province-specific extraction instructions."""
    instructions = []

    if province_code == "AB":
        instructions.append("""
**K5P Configuration (Alberta only)**:
- threshold: Employment income threshold (usually $3,600)
- factor_numerator: Usually 0.04
- factor_denominator: Usually 0.06
""")
    elif province_code == "BC":
        instructions.append("""
**Tax Reduction (BC only)**:
- base_reduction: Base reduction amount
- reduction_rate: Rate applied to income over threshold
- phase_out_start: Income where reduction starts phasing out
- phase_out_end: Income where reduction ends
""")
    elif province_code in ["MB", "NS"]:
        instructions.append("""
**Dynamic BPA (income-based)**:
- dynamic_bpa_type: "income_based_reduction"
- base_bpa: Starting BPA for low income
- reduction_start: Income where BPA starts reducing
- reduction_end: Income where BPA reaches minimum
- min_bpa: Minimum BPA value
""")
    elif province_code == "ON":
        instructions.append("""
**Ontario Surtax (two-tier)**:
- first_threshold: Tax amount where 20% surtax starts
- first_rate: 0.20
- second_threshold: Tax amount where additional 36% surtax starts
- second_rate: 0.36

**Ontario Health Premium**:
- Multi-tier brackets based on income
- Include all tiers from 0 to 200,600+
""")
    elif province_code == "PE":
        instructions.append("""
**PEI Surtax (single-tier)**:
- threshold: Tax amount where surtax starts
- rate: Surtax rate (usually 0.10)
""")
    elif province_code == "YT":
        instructions.append("""
**Yukon Special Features**:
- bpa_is_dynamic: true (follows federal)
- dynamic_bpa_type: "follows_federal"
- has_k4p: true
- cea: Canada Employment Amount value
""")

    return "\n".join(instructions) if instructions else "No special configuration needed."


def create_single_province_prompt(
    table_text: str,
    year: int,
    effective_date: str,
    province_code: str
) -> str:
    """
    Create prompt for extracting ONE province's tax data from T4127 Table 8.1.

    This is more efficient than extracting all 12 at once:
    - Smaller prompt = faster response
    - Single province = simpler JSON output
    - Failed provinces can be retried individually

    Args:
        table_text: Text from Table 8.1 (all provincial sections)
        year: Tax year (e.g., 2025)
        effective_date: Effective date (e.g., "2025-01-01")
        province_code: 2-letter province code (e.g., "ON")

    Returns:
        Formatted prompt for GLM
    """
    info = PROVINCE_INFO.get(province_code, {
        "name": province_code,
        "features": [],
        "notes": "Unknown province"
    })

    example = _get_example_for_province(province_code)
    special_instructions = _get_special_instructions(province_code)

    return f"""You are a Canadian payroll tax expert. Extract provincial tax data for {info['name']} ({province_code}) from CRA T4127.

## Task
Parse tax data for: **{info['name']} ({province_code})**

Province notes: {info['notes']}

## Source Text (Table 8.1)
{table_text}

## Example Output Format
```json
{json.dumps(example, indent=2)}
```

## Required Fields
- **name**: "{info['name']}"
- **code**: "{province_code}"
- **bpa**: Basic Personal Amount (provincial)
- **bpa_is_dynamic**: true if BPA varies by income
- **indexing_rate**: Decimal (e.g., 0.027 for 2.7%), null if no indexing
- **has_surtax**: true/false
- **has_health_premium**: true/false
- **has_tax_reduction**: true/false
- **brackets**: Array of tax brackets with threshold, rate, constant

## How to Find Values in Table 8.1
Look for the "{province_code}" section and find:
1. Tax brackets: R (threshold), V (rate), KP (constant)
2. Basic Personal Amount: TCP or BPA value
3. Special parameters based on province type

## Special Instructions for {province_code}
{special_instructions}

## Important Notes
- All rates as decimals (15% = 0.15)
- Dollar amounts without $ symbol
- This is for year {year}, effective {effective_date}

Return ONLY the JSON object for {province_code}, no other text."""
