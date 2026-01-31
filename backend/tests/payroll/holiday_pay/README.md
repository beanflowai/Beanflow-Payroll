# Holiday Pay Test Guidelines

This document establishes testing standards for holiday pay calculations to ensure tests are **trustworthy** and **maintainable**.

## Test Organization

```
tests/payroll/holiday_pay/
├── conftest.py                  # Shared fixtures, helpers, data classes
├── test_tier1_major_provinces.py # Integration tests (SK, ON, BC, AB)
├── test_holiday_pay_formulas.py  # Formula method tests with DB mocks
├── test_formula_pure.py          # Pure math validation (no mocks)
├── fixtures/
│   └── 2025/
│       └── tier1_major_provinces.json  # Verified test cases
└── README.md                     # This file
```

## Test Categories

### 1. Integration Tests (`test_tier1_major_provinces.py`)

Tests that call **actual implementation methods** with mocked database responses.

**Purpose**: Verify the calculator produces correct results given historical data.

```python
# ✅ GOOD: Calls actual implementation
def test_sk_full_time_standard(self, mock_supabase, sk_calculator):
    setup_sk_payroll_mock(mock_supabase, case.input)

    result = sk_calculator.formula_calculators.apply_5_percent_28_days(
        employee_id="test_emp",
        holiday_date=date(2025, 1, 1),
        ...
    )

    expected = Decimal(case.expected["regular_holiday_pay"])
    assert result == expected
```

### 2. Formula Method Tests (`test_holiday_pay_formulas.py`)

Tests for individual formula methods with controlled mock data.

**Purpose**: Verify formula methods handle various scenarios correctly.

### 3. Pure Math Tests (`test_formula_pure.py`)

Tests that verify **mathematical correctness** without any mocks.

**Purpose**: Document expected formula outcomes and catch basic math errors.

```python
# ✅ GOOD: Pure math validation
@pytest.mark.parametrize("base,expected", [
    (Decimal("2800.00"), Decimal("140.00")),  # $2800 × 5% = $140
    (Decimal("60.00"), Decimal("3.00")),       # $60 × 5% = $3
])
def test_5_percent_formula_math(self, base, expected):
    result = base * Decimal("0.05")
    assert result == expected
```

---

## Good Test Patterns

### ✅ Always Call Actual Implementation

```python
# ✅ CORRECT: Test calls the real calculator method
def test_sk_calculation(self, mock_supabase, calculator):
    setup_mock_data(mock_supabase, wages=Decimal("2800"))

    result = calculator.formula_calculators.apply_5_percent_28_days(
        employee_id="emp-001",
        ...
    )

    assert result == Decimal("140.00")  # Verified against official calculator
```

### ✅ Mock External Dependencies, Not Logic

```python
# ✅ CORRECT: Mock database, call real logic
mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
    {"gross_regular": 2800, "vacation_pay_paid": 0}
]

result = calculator.calculate_holiday_pay(employee, holiday_date)
```

### ✅ Document Expected Calculations

```python
def test_ontario_4_week_average(self, ...):
    """Test ON 4-week average calculation.

    Case: ON_STANDARD_4WEEK
    Formula: (wages + vacation_pay) / 20
    Calculation: ($2000 + $80) / 20 = $104.00
    Reference: Ontario ESA s.24
    """
    ...
```

### ✅ Use Fixture Data with Verification Sources

```json
{
  "id": "SK_FULL_TIME_BIWEEKLY",
  "expected": {
    "regular_holiday_pay": "140.00"
  },
  "verification": {
    "method": "manual_calculation",
    "formula_applied": "2800.00 × 0.05 = 140.00",
    "verified_date": "2025-01-24",
    "official_reference": "Saskatchewan Employment Act s.42",
    "calculator_url": "https://apps.saskatchewan.ca/lrws/calculator/holidaypay/"
  }
}
```

---

## Bad Test Patterns

### ❌ Never Re-implement Formulas in Tests

```python
# ❌ BAD: This tests nothing! It re-implements the formula.
def test_sk_calculation(self, mock_calculator):
    base = Decimal("2800")
    calculated = base * Decimal("0.05")  # Re-implementing the formula!

    expected = Decimal("140.00")
    assert calculated == expected  # This will always pass even if implementation is wrong!
```

**Why this is bad**: The test doesn't call any implementation code. If the actual
calculator has a bug, this test will still pass.

### ❌ Never Ignore Injected Fixtures

```python
# ❌ BAD: mock_calculator is injected but never used
def test_something(self, mock_calculator):
    result = Decimal("2800") * Decimal("0.05")  # Where's mock_calculator?
    assert result == Decimal("140.00")
```

### ❌ Never Hardcode Formula Logic

```python
# ❌ BAD: Hardcoded formula logic
def test_holiday_pay(self, case):
    wages = case.input["wages_past_28_days"]
    vacation = case.input.get("vacation_pay_past_28_days", 0)

    # This just duplicates the implementation - not a real test!
    calculated = (wages + vacation) * Decimal("0.05")
    assert calculated == case.expected["regular_holiday_pay"]
```

### ❌ Never Use Future Verification Dates

```json
{
  "verification_date": "2025-12-31"  // ❌ Future date = not actually verified
}
```

---

## Verification Standards

### Fixture Verification Requirements

Each test case in fixture files should have:

1. **Verification method**: How was the expected value calculated?
2. **Formula applied**: The actual calculation performed
3. **Verification date**: When was it verified (must be past/present)
4. **Official reference**: Legislation section or official calculator URL

### Official Calculator URLs

| Province | Calculator | Status |
|----------|------------|--------|
| SK | https://apps.saskatchewan.ca/lrws/calculator/holidaypay/ | Available |
| ON | https://apps.labour.gov.on.ca/tools/wages/ | Available |
| QC | https://services.cnt.gouv.qc.ca/calculateurs/ | Available |
| BC | Manual (PDF guide only) | Manual verification |
| AB | Manual (PDF guide only) | Manual verification |

---

## Running Tests

```bash
# Run all holiday pay tests
cd payroll/backend
uv run pytest tests/payroll/holiday_pay/ -v

# Run only pure formula tests (fast, no mocks)
uv run pytest tests/payroll/holiday_pay/test_formula_pure.py -v

# Run integration tests for a specific province
uv run pytest tests/payroll/holiday_pay/test_tier1_major_provinces.py::TestSaskatchewanHolidayPay -v

# Check test coverage
uv run pytest tests/payroll/holiday_pay/ \
    --cov=app.services.payroll_run.holiday_pay \
    --cov-report=term-missing
```

---

## Adding New Tests

### When Adding a New Province Test

1. Add test case to appropriate fixture file with **verification source**
2. Create integration test that **calls actual implementation**
3. Add pure math test to `test_formula_pure.py` for formula validation
4. Verify against official calculator (if available) and document

### When Adding a New Formula Type

1. Add formula to `FormulaCalculators` class
2. Create tests in `test_holiday_pay_formulas.py` with mocked data
3. Add pure math tests to `test_formula_pure.py`
4. Add integration tests to tier test file

---

## Common Mistakes to Avoid

| Mistake | Why It's Bad | What To Do Instead |
|---------|--------------|-------------------|
| Re-implementing formula in test | Test always passes, even with bugs | Call actual implementation |
| Using future verification dates | Indicates not actually verified | Use actual verification date |
| No official source reference | Can't validate correctness | Document calculator URL or legislation |
| Skipping edge cases | Misses bugs in boundary conditions | Test zero wages, new employees, etc. |
| Ignoring mock fixtures | Test doesn't test anything | Always use injected fixtures |

---

## Contact

For questions about test standards, see the `#payroll-dev` channel or the
[testing-strategy skill](/.claude/skills/testing-strategy/SKILL.md).
