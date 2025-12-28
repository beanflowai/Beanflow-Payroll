# Paystub Design Improvement Plan

## Objective
Improve the paystub PDF layout to align with Canadian industry standards while maintaining compliance with Saskatchewan pay statement requirements.

---

## Scope Summary (Based on User Input)
- **Logo**: Add company logo support (requires DB + frontend + paystub changes)
- **Employee ID**: Skip (not needed)
- **Bank Info**: Skip (no sensitive financial data)

---

## Current State Analysis

### What's Working Well
- Pay Period and Cheque Date displayed
- Earnings with Current and YTD columns
- Complete tax deductions (CPP, EI, Federal Tax, Provincial Tax)
- Net Pay with YTD totals
- Vacation Pay balance tracking

### Gaps Identified (vs Industry Standard)

| Gap | Impact |
|-----|--------|
| No company logo | Less professional appearance |
| Empty Occupation field | Incomplete employee info |
| Qty/Rate columns empty | Salary employees should show "Salary" |
| No Total Deductions label | Less clarity |
| Footer lacks structure | Employer info not prominent |

---

## Proposed Improvements

### Phase 1: Company Logo Infrastructure

**1.1 Database Schema Update**
- Add `logo_url` column to `companies` table
- Migration file to add nullable text field

**1.2 Backend API Update**
- Update Company model to include `logoUrl` field
- Add endpoint for logo upload (store in DigitalOcean Spaces)
- Update company CRUD operations

**1.3 Frontend Company Settings**
- Add logo upload component to company profile page
- Image preview and upload functionality
- Store URL in database after upload

**Files to modify:**
- `backend/supabase/migrations/` (new migration)
- `backend/app/models/company.py`
- `backend/app/api/v1/company.py`
- `frontend/src/lib/components/company/ProfileTab.svelte`

---

### Phase 2: Paystub Header Enhancement

**2.1 Add Logo Rendering to Paystub**
- Add `logoUrl: str | None` field to `PaystubData`
- Download logo image at generation time
- Modify `_build_memo_section` to render logo at top-left
- Logo size: max 1.5 inch width, maintain aspect ratio
- Fallback: display company name in bold if no logo

**Files to modify:**
- `backend/app/models/paystub.py`
- `backend/app/services/payroll/paystub_generator.py`
- `backend/app/services/payroll/paystub_data_builder.py`

---

### Phase 3: Earnings Section Improvement

**3.1 Handle Salary vs Hourly Display**
- For salaried employees: show "Salary" in Qty column, leave Rate blank
- For hourly employees: show actual hours and rate
- Update data builder to detect pay type from employee/pay group

**3.2 Add Gross Pay Total Row**
- Add explicit "Gross Pay" label row at end of earnings section
- Format: `Gross Pay | | | $X,XXX.XX | $XX,XXX.XX`

**Files to modify:**
- `backend/app/services/payroll/paystub_data_builder.py`
- `backend/app/services/payroll/paystub_generator.py`

---

### Phase 4: Deductions Section Clarity

**4.1 Add "Total Deductions" Label**
- Change blank total row to "Total Deductions" label
- Applies to Taxes section and Adjustments section

**4.2 Visual Separation**
- Add subtle background color or box around Net Pay row
- Make Net Pay more prominent (larger font, bold)

**Files to modify:**
- `backend/app/services/payroll/paystub_generator.py`

---

### Phase 5: Professional Footer

**5.1 Restructure Footer Section**
- Company name and address more prominently displayed
- Add horizontal separator line above footer
- Optionally add "This is your official pay statement" text

**Files to modify:**
- `backend/app/services/payroll/paystub_generator.py`

---

## Implementation Order

### Part A: Company Logo Infrastructure (4 steps)

| Step | Task | Details |
|------|------|---------|
| A1 | Database migration | Add `logo_url TEXT` column to `companies` table |
| A2 | Frontend types | Add `logoUrl?: string \| null` to `CompanyProfile`, `CompanySettings`, `DbCompany` |
| A3 | Frontend service | Add `logo_url` to `dbCompanyToUi()` and `CompanyUpdateInput` |
| A4 | Frontend UI | Add logo upload section to `ProfileTab.svelte` using Supabase Storage |

### Part B: Paystub PDF Improvements (7 steps)

| Step | Task | Details |
|------|------|---------|
| B1 | Add `logoUrl` to PaystubData | `backend/app/models/paystub.py` |
| B2 | Pass logo URL in data builder | `paystub_data_builder.py` - get from company record |
| B3 | Render logo in PDF header | `paystub_generator.py` - download image, resize, position |
| B4 | Improve earnings section | Show "Salary" for salaried employees, add "Gross Pay" row |
| B5 | Add "Total Deductions" label | Replace blank row with label in taxes section |
| B6 | Enhance Net Pay styling | Light gray background box, larger font |
| B7 | Improve footer | Add separator line, "This is your official pay statement" text |

---

## Critical Files

```
# Database
backend/supabase/migrations/YYYYMMDD_add_company_logo.sql (new)

# Frontend (company logo infrastructure)
frontend/src/lib/types/company.ts              # Add logoUrl field to interfaces
frontend/src/lib/services/companyService.ts    # Add logo_url to DbCompany, update converters
frontend/src/lib/components/company/ProfileTab.svelte  # Add logo upload UI

# Backend (paystub rendering)
backend/app/models/paystub.py
backend/app/services/payroll/paystub_generator.py
backend/app/services/payroll/paystub_data_builder.py
```

---

## Expected Result

```
┌─────────────────────────────────────────────────────────┐
│ [LOGO]              WOOHELPS INTERNATIONAL TECHNOLOGY   │
│                     Saskatchewan                        │
├─────────────────────────────────────────────────────────┤
│ Employee: Haifeng Sun                                   │
│ Saskatchewan                   SIN: ***-***-XXX         │
│                                                         │
│ Job Title: Software Developer                           │
├─────────────────────────────────────────────────────────┤
│ Pay Period: 02/01/2025 - 02/28/2025                     │
│ Pay Date: 03/31/2025                                    │
├─────────────────────────────────────────────────────────┤
│ EARNINGS           Qty      Rate      Current    YTD    │
│ Regular Pay        Salary             2,000.00  6,000.00│
│ ───────────────────────────────────────────────────────│
│ Gross Pay                             2,000.00  6,000.00│
├─────────────────────────────────────────────────────────┤
│ DEDUCTIONS                            Current    YTD    │
│ CPP                                   -102.27   -306.81 │
│ EI                                    -32.80    -98.40  │
│ Federal Tax                           -61.30    -183.90 │
│ Provincial Tax                        -30.74    -92.22  │
│ ───────────────────────────────────────────────────────│
│ Total Deductions                      -227.11   -681.33 │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ NET PAY                             1,642.50  4,927.50│ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ LEAVE BALANCES     Earned    Used     Available         │
│ Vacation ($)       115.40    0.00     692.40            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Woohelps International Technology                       │
│ Saskatchewan                                            │
│ This is your official pay statement                     │
└─────────────────────────────────────────────────────────┘
```
