# BeanFlow Payroll - Test Implementation Plan

**Project**: BeanFlow Payroll
**Version**: 1.0
**Created**: 2025-12-29
**Status**: Draft

---

## Executive Summary

This test plan ensures the accuracy and compliance of BeanFlow Payroll's calculation engine against CRA (Canada Revenue Agency) standards. The primary validation method is comparison against CRA's official PDOC (Payroll Deductions Online Calculator).

### Quality Goals

| Metric | Target |
|--------|--------|
| Test Coverage | > 80% for payroll services |
| PDOC Variance | < $1 per component |
| Province Coverage | 12/12 provinces |
| Critical Bug Count | 0 |

---

## Test Strategy Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Testing Pyramid                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                        ┌─────────┐                                   │
│                        │  PDOC   │  ◄── Manual validation           │
│                        │Validate │      against CRA calculator       │
│                        └────┬────┘                                   │
│                             │                                        │
│                    ┌────────┴────────┐                               │
│                    │   Integration   │  ◄── Full payroll flow        │
│                    │     Tests       │      All 12 provinces         │
│                    └────────┬────────┘                               │
│                             │                                        │
│           ┌─────────────────┴─────────────────┐                      │
│           │          Unit Tests               │  ◄── Individual      │
│           │  CPP | EI | Federal | Provincial  │      calculators     │
│           └───────────────────────────────────┘                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Document | Focus | Duration | Priority |
|-------|----------|-------|----------|----------|
| **Phase 1** | `01_unit_tests.md` | Calculator unit tests | 3-4 days | P0 |
| **Phase 2** | `02_integration_tests.md` | End-to-end payroll flow | 2-3 days | P0 |
| **Phase 3** | `03_pdoc_validation.md` | CRA PDOC comparison | 2-3 days | P0 |
| **Phase 4** | `04_test_matrix.md` | Complete test scenarios | Reference | P1 |

**Total Estimated Duration**: 1.5 - 2 weeks

---

## Test Scope

### In Scope

| Component | Description |
|-----------|-------------|
| CPP Calculator | Base CPP + CPP2 (additional) |
| EI Calculator | Employee + Employer premiums |
| Federal Tax Calculator | T4127 Option 1 formula |
| Provincial Tax Calculator | All 12 provinces/territories |
| Payroll Engine | Full calculation orchestration |
| YTD Tracking | Cumulative limits and maximums |
| Special Rules | Ontario surtax, BC reduction, dynamic BPA |

### Out of Scope (Future)

- Quebec payroll (separate system)
- T4 generation tests
- ROE generation tests
- UI/Frontend tests
- Performance/load tests

---

## Test Data Strategy

### Approach: PDOC as Golden Standard

Since we don't have real employee data, we use **CRA PDOC** as the source of truth:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Test Data Generation Flow                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. Design Test Scenario                                         │
│      ├── Province: Ontario                                        │
│      ├── Gross Pay: $2,307.69                                     │
│      ├── Pay Frequency: Bi-weekly                                 │
│      └── TD1 Claims: Federal $16,129, Provincial $12,747          │
│                          │                                        │
│                          ▼                                        │
│   2. Run in CRA PDOC (screenshot for evidence)                    │
│      └── https://www.canada.ca/.../payroll-deductions-online...   │
│                          │                                        │
│                          ▼                                        │
│   3. Record Expected Values                                       │
│      ├── CPP: $119.23                                             │
│      ├── EI: $37.85                                               │
│      ├── Federal Tax: $220.15                                     │
│      └── Provincial Tax: $89.87                                   │
│                          │                                        │
│                          ▼                                        │
│   4. Write Test Case with Expected Values                         │
│      └── assert result.cpp == Decimal("119.23")                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Test Data Categories

| Category | Description | Count |
|----------|-------------|-------|
| **Standard Cases** | Normal salary scenarios per province | 12 |
| **Boundary Cases** | CPP/EI max, YMPE/YAMPE boundaries | 8 |
| **Edge Cases** | Exemptions, low income, high income | 10 |
| **Special Rules** | ON surtax, BC reduction, dynamic BPA | 6 |
| **Total** | | ~36 core test cases |

---

## Acceptance Criteria

### Pass Criteria

1. **Unit Tests**: All pass, coverage > 80%
2. **Integration Tests**: All 12 provinces pass
3. **PDOC Validation**: Variance < $1 for all components
4. **No Critical Bugs**: Zero blocking issues

### Variance Tolerance

| Component | Acceptable Variance | Reason |
|-----------|---------------------|--------|
| CPP | ± $0.50 | Rounding differences |
| EI | ± $0.50 | Rounding differences |
| Federal Tax | ± $1.00 | Multiple rounding steps |
| Provincial Tax | ± $1.00 | Complex formulas |
| Net Pay | ± $2.00 | Cumulative variance |

---

## Directory Structure

```
backend/tests/
├── conftest.py                     # Shared fixtures
├── payroll/
│   ├── __init__.py
│   ├── test_cpp_calculator.py      # Phase 1
│   ├── test_ei_calculator.py       # Phase 1
│   ├── test_federal_tax.py         # Phase 1
│   ├── test_provincial_tax.py      # Phase 1
│   ├── test_payroll_engine.py      # Phase 2
│   ├── test_all_provinces.py       # Phase 2
│   └── fixtures/
│       ├── pdoc_test_data.json     # PDOC expected values
│       └── boundary_cases.json     # Edge case data
└── pdoc_validation/
    ├── validation_results.md       # Phase 3 results
    └── screenshots/                # PDOC evidence
```

---

## Tools & Commands

### Running Tests

```bash
# Run all payroll tests
cd backend
uv run pytest tests/payroll/ -v

# Run with coverage
uv run pytest tests/payroll/ -v --cov=app/services/payroll --cov-report=html

# Run specific test file
uv run pytest tests/payroll/test_cpp_calculator.py -v

# Run specific test
uv run pytest tests/payroll/test_cpp_calculator.py::TestCPPCalculator::test_base_cpp -v
```

### Quality Checks

```bash
# Type checking
uv run mypy app/services/payroll/

# Linting
uv run ruff check app/services/payroll/

# Full quality check
bash scripts/quality-check-backend.sh
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDOC unavailable | High | Cache screenshots, document values |
| Tax rate changes | Medium | Version-controlled config files |
| Province-specific bugs | Medium | Parametrized tests for all 12 |
| Rounding discrepancies | Low | Document acceptable variance |

---

## Sign-off Checklist

- [ ] Phase 1: Unit tests complete (coverage > 80%)
- [ ] Phase 2: Integration tests pass for all provinces
- [ ] Phase 3: PDOC validation documented (variance < $1)
- [ ] Phase 4: Test matrix reviewed and approved
- [ ] All quality checks pass
- [ ] Test documentation complete

---

## Next Steps

1. **Start with Phase 1**: Unit tests for calculators
2. **Gather PDOC data**: Run scenarios in CRA calculator
3. **Implement tests**: Follow templates in phase documents
4. **Validate results**: Compare against PDOC
5. **Document findings**: Record any discrepancies

---

**Next**: [Phase 1: Unit Tests](./01_unit_tests.md)
