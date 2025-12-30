"""
PDOC Validation Tests - Modular Structure

This package contains tests that validate BeanFlow Payroll calculations
against CRA's Payroll Deductions Online Calculator (PDOC).

Structure:
- tier1: Core province coverage (12 provinces × $60k bi-weekly)
- tier2: Income level coverage (low/high income scenarios)
- tier3: CPP/EI boundary tests (contribution maximums)
- tier4: Special conditions (RRSP, union dues, exemptions)
- tier5: Federal tax rate change (pre/post July 2025)

Reference: CRA T4127 Payroll Deductions Formulas
PDOC URL: https://www.canada.ca/en/revenue-agency/services/e-services/
         digital-services-businesses/payroll-deductions-online-calculator.html
"""
