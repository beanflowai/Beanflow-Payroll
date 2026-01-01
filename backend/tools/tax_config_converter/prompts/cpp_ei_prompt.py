"""
CPP/EI Extraction Prompt for T4127 PDF

Extracts CPP, CPP2, and EI data from Tables 8.3-8.7.
"""

import json

CPP_EI_EXAMPLE = {
    "cpp": {
        "ympe": 71300.00,
        "yampe": 81200.00,
        "basic_exemption": 3500.00,
        "base_rate": 0.0595,
        "additional_rate": 0.04,
        "max_base_contribution": 4034.10,
        "max_additional_contribution": 396.00,
        "max_total_contribution": 4430.10,
        "employer_rate_multiplier": 1.0
    },
    "ei": {
        "mie": 65700.00,
        "employee_rate": 0.0164,
        "employer_rate_multiplier": 1.4,
        "max_employee_premium": 1077.48,
        "max_employer_premium": 1508.47
    }
}


def create_cpp_ei_prompt(table_text: str, year: int, effective_date: str) -> str:
    """
    Create prompt for extracting CPP/EI data from T4127 tables.

    Args:
        table_text: Combined text from Tables 8.3-8.7
        year: Tax year (e.g., 2025)
        effective_date: Effective date (e.g., "2025-01-01")

    Returns:
        Formatted prompt for GLM
    """
    return f"""You are a Canadian payroll tax expert. Extract CPP and EI contribution data from the CRA T4127 document text below.

## Task
Parse the CPP (Canada Pension Plan) and EI (Employment Insurance) data and return a JSON object.

## Source Text (Tables 8.3-8.7)
{table_text}

## Expected Output Format
```json
{json.dumps(CPP_EI_EXAMPLE, indent=2)}
```

## Field Definitions

### CPP Fields:
- **ympe**: Year's Maximum Pensionable Earnings (YMPE) - the ceiling for base CPP contributions
- **yampe**: Year's Additional Maximum Pensionable Earnings (YAMPE) - ceiling for CPP2/second earnings ceiling
- **basic_exemption**: Basic exemption amount (typically $3,500)
- **base_rate**: Base CPP contribution rate as decimal (e.g., 5.95% = 0.0595)
- **additional_rate**: CPP2 additional rate as decimal (e.g., 4% = 0.04)
- **max_base_contribution**: Maximum annual base CPP contribution (employee portion)
- **max_additional_contribution**: Maximum annual CPP2 contribution (employee portion)
- **max_total_contribution**: Total maximum = base + additional
- **employer_rate_multiplier**: Always 1.0 for CPP (employer matches employee)

### EI Fields:
- **mie**: Maximum Insurable Earnings
- **employee_rate**: Employee EI premium rate as decimal (e.g., 1.64% = 0.0164)
- **employer_rate_multiplier**: Employer pays 1.4x the employee rate
- **max_employee_premium**: Maximum annual employee premium
- **max_employer_premium**: Maximum annual employer premium

## Instructions
1. Find the YMPE, YAMPE values (look for "Year's Maximum Pensionable Earnings")
2. Find the CPP contribution rates (look for "contribution rate", "5.95%", "4%")
3. Find the EI premium rate and maximum insurable earnings (look for "EI premium rate", "maximum insurable earnings")
4. Calculate max contributions if not explicitly stated:
   - max_base_contribution = (YMPE - basic_exemption) × base_rate
   - max_additional_contribution = (YAMPE - YMPE) × additional_rate
   - max_employee_premium = MIE × employee_rate
   - max_employer_premium = max_employee_premium × 1.4
5. Return ONLY valid JSON with no explanation text

## Important Notes
- All rates must be decimals (15% = 0.15, NOT 15)
- All dollar amounts as numbers without $ symbol
- Round monetary values to 2 decimal places
- This is for year {year}, effective {effective_date}

Return ONLY the JSON object, no other text."""
