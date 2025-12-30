# Annual Tax Tables Update Checklist

Copy this template for each year's update.

---

## [YEAR] Tax Tables Update

**Update started**: YYYY-MM-DD
**Update completed**: YYYY-MM-DD
**Updated by**: [name]

---

### 1. Data Source Collection

- [ ] Download T4127 PDF (English version)
- [ ] Record edition number: _____ Edition
- [ ] Record effective date: YYYY-MM-DD
- [ ] Save PDF to reference folder

**Source URL**: https://...
**Access Date**: YYYY-MM-DD

---

### 2. CPP Configuration (`cpp_ei.json`)

| Field | Previous | New | Source |
|-------|----------|-----|--------|
| YMPE | $ | $ | T4127 |
| YAMPE | $ | $ | T4127 |
| Basic Exemption | $ | $ | T4127 |
| Base Rate | % | % | T4127 |
| Additional Rate (CPP2) | % | % | T4127 |
| Max Base Contribution | $ | $ | Calculated |
| Max Additional Contribution | $ | $ | Calculated |

- [ ] Values updated in JSON
- [ ] Metadata `_metadata.changes_from_previous` updated
- [ ] Calculation verified: `max_base = (YMPE - exemption) × rate`

---

### 3. EI Configuration (`cpp_ei.json`)

| Field | Previous | New | Source |
|-------|----------|-----|--------|
| MIE | $ | $ | Service Canada |
| Employee Rate | % | % | Service Canada |
| Employer Multiplier | × | × | Service Canada |
| Max Employee Premium | $ | $ | Calculated |
| Max Employer Premium | $ | $ | Calculated |

- [ ] Values updated in JSON
- [ ] Calculation verified: `max_premium = MIE × rate`

---

### 4. Federal Tax Configuration (`federal_jan.json`, `federal_jul.json`)

#### January Edition

| Field | Previous | New | Source |
|-------|----------|-----|--------|
| BPAF | $ | $ | T4127 |
| CEA | $ | $ | T4127 |
| Lowest Rate | % | % | T4127 |

**Tax Brackets**:
| Bracket | Threshold | Rate | Constant |
|---------|-----------|------|----------|
| 1 | $0 | % | $0 |
| 2 | $ | % | $ |
| 3 | $ | % | $ |
| 4 | $ | % | $ |
| 5 | $ | % | $ |

- [ ] January edition file updated
- [ ] July edition file created (if different rates)
- [ ] Bracket constants verified

---

### 5. Provincial Tax Configuration (`provinces_jan.json`, `provinces_jul.json`)

For each province (AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT):

- [ ] **AB** - BPA updated, brackets verified
- [ ] **BC** - BPA updated, brackets verified, tax reduction config checked
- [ ] **MB** - BPA updated, dynamic BPA config verified
- [ ] **NB** - BPA updated, brackets verified
- [ ] **NL** - BPA updated, brackets verified
- [ ] **NS** - BPA updated, dynamic BPA config verified
- [ ] **NT** - BPA updated, brackets verified
- [ ] **NU** - BPA updated, brackets verified
- [ ] **ON** - BPA updated, brackets verified, surtax/health premium configs checked
- [ ] **PE** - BPA updated, brackets verified, surtax config checked
- [ ] **SK** - BPA updated, brackets verified
- [ ] **YT** - BPA updated, dynamic BPA config verified

---

### 6. Validation

#### JSON Schema Validation

```bash
cd backend
uv run python -c "from app.services.payroll.tax_tables import validate_tax_tables; print(validate_tax_tables(YEAR))"
```

- [ ] No schema validation errors

#### PDOC Test Suite

```bash
cd backend
uv run pytest tests/payroll/pdoc/ -v --year=YEAR
```

| Tier | Status | Notes |
|------|--------|-------|
| Tier 1 (Provinces) | ⬜ | |
| Tier 2 (Income) | ⬜ | |
| Tier 3 (CPP/EI) | ⬜ | |
| Tier 4 (Special) | ⬜ | |
| Tier 5 (Rate change) | ⬜ | |

- [ ] All 44+ test cases pass
- [ ] Variance < $0.05 per component

#### Manual PDOC Verification

Test at least 5 scenarios manually against CRA PDOC calculator:

| Scenario | Province | Income | Expected Net | Actual Net | Variance |
|----------|----------|--------|--------------|------------|----------|
| 1 | ON | $60k | $ | $ | $ |
| 2 | BC | $45k | $ | $ | $ |
| 3 | AB | $100k | $ | $ | $ |
| 4 | NS | $35k | $ | $ | $ |
| 5 | MB | $80k | $ | $ | $ |

- [ ] All manual tests pass (variance < $1.00)

---

### 7. Metadata Update

For each updated config file:

- [ ] `_metadata.version` set correctly
- [ ] `_metadata.source.accessed_date` set to today
- [ ] `_metadata.validation.pdoc_validated` set to `true`
- [ ] `_metadata.validation.pdoc_validation_date` set to today
- [ ] `_metadata.validation.test_cases_passed` updated
- [ ] `_metadata.changes_from_previous` lists all changes
- [ ] `_metadata.last_updated` set to today
- [ ] `_metadata.updated_by` set

---

### 8. Documentation

- [ ] Update log created: `docs/tax-tables/YEAR-update-log.md`
- [ ] README.md Key Dates section updated
- [ ] CHANGELOG entry added

---

### 9. Final Review

- [ ] All config files have valid JSON syntax
- [ ] All test suites pass
- [ ] Code review completed
- [ ] Changes committed with descriptive message

**Sign-off**: _____________ Date: _____________
