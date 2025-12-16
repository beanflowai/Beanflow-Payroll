# Payroll UI Design Overview

> **Last Updated**: 2025-12-11
> **Architecture Version**: v3.0 (Standalone Product)
> **Updated**: Renamed Settings to Company, added Pay Groups

---

## Standalone Product Notice

**BeanFlow Payroll** is a standalone product with its own frontend application.

| Aspect | Details |
|--------|---------|
| **Domain** | `payroll.beanflow.com` |
| **Frontend** | Separate SvelteKit app (`payroll-frontend/`) |
| **Layout** | Simplified 2-column (no AI panel) |
| **Auth** | Shared Google OAuth with BeanFlow Bookkeeping |

See `14_standalone_architecture.md` for detailed frontend setup.

---

## Design Philosophy

The Payroll UI follows a **spreadsheet-inspired interface** optimized for professional users:

- **Efficiency**: Minimal clicks, inline editing, batch operations
- **Familiarity**: Excel/Google Sheets-like interaction patterns
- **Accuracy**: Clear data presentation, real-time calculation feedback
- **Professional**: Clean, data-dense layout for desktop/tablet use

### Core Design Principles

1. **Single-Page Management**: All payroll operations on one screen
2. **Inline Editing**: Click-to-edit fields with immediate calculation
3. **Pay Period Navigation**: Easy switching between pay periods
4. **Real-time Sync**: All changes auto-save to Supabase
5. **Optional Bookkeeping Integration**: "Run Payroll" can create journal entries

---

## Routing Structure

**Base Domain**: `payroll.beanflow.com`

### Employer/Admin Routes
```
/                          → Landing page / Login
/dashboard                 → Overview dashboard
/employees                 → Employee list
/employees/new             → Add new employee
/employees/[id]            → Employee detail
/payroll                   → Payroll runs (by Pay Group)
/payroll/run               → Run payroll wizard
/payroll/history           → Past payroll runs
/payroll/history/[id]      → Run detail
/remittance                → CRA remittance tracking
/reports                   → Reports hub
/company                   → Company settings (Profile, Pay Groups, Integration)
```

### Employee Portal Routes (Phase 2)
```
/employee/                 → Employee portal dashboard
/employee/auth             → Magic link login
/employee/auth/verify      → Verify magic link token
/employee/paystubs         → Paystub history
/employee/paystubs/[id]    → Paystub detail
/employee/profile          → Profile management (personal, tax, bank)
/employee/leave            → Leave balances and history
```

---

## Workspace Layout

Payroll uses a **simpler 2-column layout** (no AI Panel):

```
┌─────────────────────────────────────────────────────┐
│  Header (Logo, Company Name, User Menu)             │
├──────────────┬──────────────────────────────────────┤
│   Sidebar    │                                      │
│   (200px)    │          Main Content                │
│              │                                      │
│  • Dashboard │                                      │
│  • Employees │                                      │
│  • Payroll   │  (Pay Group selector + runs)         │
│  • History   │                                      │
│  • Remittance│  (CRA deduction tracking)            │
│  • Reports   │                                      │
│  • Company   │  (Profile, Pay Groups, Integration)  │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

**Responsive Behavior** (Tailwind breakpoints):
- **≥1024px (lg)**: Full layout with sidebar
- **768px - 1024px (md)**: Sidebar collapses to icons only
- **<768px**: Mobile navigation (hamburger menu)

---

## User Scenarios

### Scenario 1: Process Bi-weekly Payroll
1. User navigates to current pay period (Jan 1-14, 2025)
2. Reviews employee list and gross pay amounts
3. Edits gross pay for employees with overtime/bonuses
4. System auto-calculates deductions (CPP, EI, taxes)
5. Reviews Net Pay column
6. Generates paystubs for all employees
7. Confirms payroll → Creates Payable entry (if linked to Bookkeeping)
8. After bank payment → Updates status

### Scenario 2: Add New Employee
1. Clicks "Add Employee" button
2. Fills form: Name, SIN, Province, Pay Frequency, Salary
3. System auto-fills TD1 claim amounts (federal/provincial BPA)
4. User adjusts claim amounts if needed
5. Saves → Employee appears in payroll table

### Scenario 3: View Historical Payroll
1. Uses date navigation to switch to previous pay period
2. Views all historical data from Supabase
3. Can regenerate paystub PDFs for past periods
4. Cannot edit confirmed/paid payrolls

---

## UI Module Index

| Module | File | Description | Phase |
|--------|------|-------------|-------|
| Employees | [01_employees.md](./01_employees.md) | Employee list, detail panel, Pay Group & Tags | MVP |
| Payroll Runs | [02_payroll_runs.md](./02_payroll_runs.md) | Payroll runs by Pay Group, run detail, holiday/leave, one-time adjustments | MVP |
| Shared Components | [03_shared_components.md](./03_shared_components.md) | StatusBadge, MoneyDisplay, SummaryCard | MVP |
| State Management | [04_state_management.md](./04_state_management.md) | Svelte Stores architecture | MVP |
| Responsive & a11y | [05_responsive_a11y.md](./05_responsive_a11y.md) | Responsive design, accessibility | MVP |
| Company | [06_company.md](./06_company.md) | Company Profile, Pay Groups, Integration (Tab layout) | MVP |
| Remittance | [07_remittance.md](./07_remittance.md) | CRA remittance tracking, payment recording | MVP |
| Pay Groups | [08_pay_groups.md](./08_pay_groups.md) | Pay Group management, Leave policy configuration | MVP |
| **Employee Portal** | [09_employee_portal.md](./09_employee_portal.md) | Employee self-service portal (Magic Link auth, paystubs, profile editing) | **Phase 2** |

---

## Component File Structure

```
payroll-frontend/src/lib/
├── components/
│   ├── employees/
│   │   ├── EmployeeTable.svelte
│   │   ├── EmployeeDetailPanel.svelte
│   │   ├── EmployeeFormModal.svelte
│   │   ├── SINDisplay.svelte
│   │   ├── PortalStatusBadge.svelte         # Phase 2: Portal status
│   │   ├── InviteToPortalModal.svelte       # Phase 2: Send portal invite
│   │   └── ProfileChangeReviewModal.svelte  # Phase 2: Review employee changes
│   ├── payroll/
│   │   ├── PayrollRunsTable.svelte
│   │   ├── PayrollRunDetail.svelte
│   │   ├── PayrollRecordRow.svelte
│   │   ├── PayrollRecordExpanded.svelte
│   │   ├── HolidayWorkModal.svelte
│   │   ├── LeaveModal.svelte
│   │   ├── OneTimeAdjustmentModal.svelte    # NEW: Bonus, Retro Pay, etc.
│   │   └── AdjustmentBadge.svelte           # NEW: Adjustment type badge
│   ├── remittance/
│   │   ├── UpcomingRemittanceCard.svelte
│   │   ├── RemittanceSummaryCards.svelte
│   │   ├── RemittanceHistoryTable.svelte
│   │   ├── RemittanceDetailRow.svelte
│   │   ├── RemittanceStatusBadge.svelte
│   │   └── MarkAsPaidModal.svelte
│   ├── company/
│   │   ├── ProfileTab.svelte                # Tab 1: Profile content
│   │   ├── CompanyInfoSection.svelte
│   │   ├── RemittanceSection.svelte
│   │   ├── PreferencesSection.svelte
│   │   ├── PayGroupsTab.svelte              # Tab 2: Pay Groups list
│   │   ├── PayGroupCard.svelte
│   │   ├── PayGroupModal.svelte
│   │   ├── PayGroupDeleteModal.svelte
│   │   ├── IntegrationTab.svelte            # Tab 3: Integration
│   │   └── RemitterTypeSelect.svelte
│   ├── employee-portal/                     # Phase 2: Employee Self-Service
│   │   ├── PortalHeader.svelte
│   │   ├── PortalNav.svelte
│   │   ├── DashboardCard.svelte
│   │   ├── PaystubCard.svelte
│   │   ├── PaystubDetail.svelte
│   │   ├── ProfileSection.svelte
│   │   ├── EditPersonalInfoModal.svelte
│   │   ├── EditTaxInfoModal.svelte
│   │   ├── EditBankInfoModal.svelte
│   │   └── LeaveBalanceCard.svelte
│   └── shared/
│       ├── StatusBadge.svelte
│       ├── MoneyDisplay.svelte
│       └── SummaryCard.svelte
└── types/
    ├── employee.ts                          # Employee with payGroupId and tags
    ├── payroll.ts                           # PayrollRun, OneTimeAdjustment
    ├── company.ts                           # CompanyProfile
    ├── pay-group.ts                         # PayGroup, PayFrequency, EmploymentType
    ├── remittance.ts
    └── employee-portal.ts                   # Phase 2: Portal types
```
