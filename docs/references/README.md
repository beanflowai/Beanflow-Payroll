# Official Policy References

This directory contains official policy documentation from Canadian provincial/territorial government sources.

## Purpose

1. **Traceability** - Every config in `backend/config/` can be traced to an official source
2. **Auditability** - Easy to compare implementation vs official policy
3. **Maintenance** - Track when policies were last verified and need updates

## Directory Structure

```
docs/references/
├── README.md                 # This file
├── holiday_pay/              # Holiday Pay official policies
│   ├── _TEMPLATE.md          # Template for new provinces
│   ├── AB.md                 # Alberta
│   ├── BC.md                 # British Columbia
│   ├── ON.md                 # Ontario
│   └── ...
├── vacation_pay/             # Vacation Pay policies
├── sick_leave/               # Sick Leave policies
├── wcb/                      # Workers' Compensation Board reference
│   └── README.md             # WCB policy overview & provincial links
└── tax_tables/               # Tax table sources
```

## Verification Status

| Province | Holiday Pay | Vacation Pay | Sick Leave | Last Verified |
|----------|-------------|--------------|------------|---------------|
| AB | ✅ | ✅ | ✅ | 2025-12-31 |
| BC | ✅ | ✅ | ✅ | 2025-12-31 |
| MB | ✅ | ✅ | ✅ | 2025-12-31 |
| NB | ✅ | ✅ | ✅ | 2025-12-31 |
| NL | ✅ | ✅ | ✅ | 2025-12-31 |
| NS | ✅ | ✅ | ✅ | 2025-12-31 |
| NT | ✅ | ✅ | ✅ | 2025-12-31 |
| NU | ✅ | ✅ | ✅ | 2025-12-31 |
| ON | ✅ | ✅ | ✅ | 2025-12-31 |
| PE | ✅ | ✅ | ✅ | 2025-12-31 |
| QC | ✅ | ✅ | ✅ | 2025-12-31 |
| SK | ✅ | ✅ | ✅ | 2025-12-31 |
| YT | ✅ | ✅ | ✅ | 2025-12-31 |
| Federal | ✅ | ✅ | ✅ | 2025-12-31 |

**Legend**: ⬜ Not Verified | ✅ Verified | ⚠️ Needs Update

### Other References (Not Config-Driven)

| Topic | Status | Notes |
|-------|--------|-------|
| WCB | 📚 Reference | Employer-only cost, rates vary by company. See `wcb/README.md` |

## How to Verify a Province

1. Copy `holiday_pay/_TEMPLATE.md` to `holiday_pay/{PROVINCE_CODE}.md`
2. Search official government website for employment standards
3. Fill in all sections with official data
4. Compare with `backend/config/holiday_pay/2025/provinces_jan.json`
5. Document any differences
6. Update config if needed
7. Update status in this README

## Official Government URLs

| Province | Employment Standards URL |
|----------|-------------------------|
| AB | https://www.alberta.ca/employment-standards |
| BC | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice |
| MB | https://www.gov.mb.ca/labour/standards/ |
| NB | https://www.gnb.ca/en/topic/jobs-workplaces/labour-market-workforce/employment-standards.html |
| NL | https://www.gov.nl.ca/ecc/labour/lsaissues/ |
| NS | https://novascotia.ca/lae/employmentrights/ |
| NT | https://www.ece.gov.nt.ca/en/services/employment-standards |
| NU | https://nu-lsco.ca/faq-s (Labour Standards Compliance Office) |
| ON | https://www.ontario.ca/document/your-guide-employment-standards-act-0 |
| PE | https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/employment-standards-act |
| SK | https://www.saskatchewan.ca/business/employment-standards |
| YT | https://yukon.ca/en/employment-standards |
| Federal | https://www.canada.ca/en/employment-social-development/services/labour-standards.html |

## Workers' Compensation Board URLs

See `wcb/README.md` for complete list. Key links:

| Province | WCB Organization | URL |
|----------|-----------------|-----|
| AB | WCB Alberta | https://www.wcb.ab.ca |
| BC | WorkSafeBC | https://www.worksafebc.com |
| ON | WSIB | https://www.wsib.on.ca |
| QC | CNESST | https://www.cnesst.gouv.qc.ca |
| National | AWCBC | https://awcbc.org |
