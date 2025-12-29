# Payroll Runs UI Design

> **Last Updated**: 2025-12-18
> **Source**: Consolidated from `binary-enchanting-ritchie.md` (latest design)
> **Updated**: Added Draft state editing with Recalculate/Finalize workflow

---

## 0. Pay Group Integration

> **Added**: 2025-12-09
> **Key Change**: Payroll runs are now per Pay Group

### Why Pay Groups Matter for Payroll

Each Pay Group must be run **separately** because:
1. **Tax calculations differ by frequency** - Weekly uses 52 periods, bi-weekly uses 26, etc.
2. **Different pay dates** - Each group has its own `nextPeriodEnd` (pay date is calculated based on province regulations)
3. **Leave policies** - Groups can have different leave settings

### Payroll Page Flow

```
User visits /payroll
    │
    ├─► System shows Pay Group selector
    │
    ├─► User selects a Pay Group (e.g., "Bi-weekly Full-time")
    │
    └─► Page shows only employees and runs for that Pay Group
```

---

## 1. Payroll Runs List Page (`/payroll`)

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Header Bar]                                                │
│ Payroll                                    [+ Run Payroll]  │
├─────────────────────────────────────────────────────────────┤
│ Pay Group: [▼ Bi-weekly Full-time           ]              │
├─────────────────────────────────────────────────────────────┤
│ [Year Selector] 2025 ◀ ▶                                   │
├─────────────────────────────────────────────────────────────┤
│ [Status Summary Cards]                                      │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│ │ YTD Gross  │ │ Next Run   │ │ Pending    │              │
│ │ $245,000   │ │ Dec 15     │ │ 1 approval │              │
│ └────────────┘ └────────────┘ └────────────┘              │
├─────────────────────────────────────────────────────────────┤
│ [Payroll Runs Table]                                        │
│ ┌──────────────┬──────────┬──────────┬─────────┬────────┐ │
│ │ Period       │ Pay Date │ Employees│ Net Pay │ Status │ │
│ ├──────────────┼──────────┼──────────┼─────────┼────────┤ │
│ │ Dec 1-15     │ Dec 20   │ 10       │$18,500  │Approved│ │
│ │ Nov 16-30    │ Dec 5    │ 10       │$18,200  │ Paid   │ │
│ └──────────────┴──────────┴──────────┴─────────┴────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Pay Group Selector

```
Pay Group: [▼ Bi-weekly Full-time                           ]
┌─────────────────────────────────────────────────────────────┐
│  📋 Bi-weekly Full-time                           12 emp    │
│     Next pay: Dec 15, 2025                                  │
│ ─────────────────────────────────────────────────────────── │
│  📋 Bi-weekly Part-time                            5 emp    │
│     Next pay: Dec 15, 2025                                  │
│ ─────────────────────────────────────────────────────────── │
│  📋 Monthly Executives                             3 emp    │
│     Next pay: Dec 31, 2025                                  │
└─────────────────────────────────────────────────────────────┘
```

**Behavior**:
- Default to first Pay Group (or last selected)
- Persist selection in localStorage
- Show employee count and next pay date
- Badge for groups with pending payroll

### Table Columns

| Column | Description | Sortable |
|--------|-------------|----------|
| Period | `period_start` - `period_end` | ✅ |
| Pay Date | `pay_date` | ✅ |
| Employees | `total_employees` count | ✅ |
| Gross Pay | `total_gross` | ✅ |
| Deductions | Total deductions | ✅ |
| Net Pay | `total_net_pay` | ✅ |
| Status | draft/pending_approval/approved/paid | ✅ |
| Actions | View / Edit / Approve | - |

### Status Badge Colors

| Status | Color | Tailwind Class |
|--------|-------|----------------|
| Draft | Gray | `bg-gray-100 text-gray-800` |
| Pending Approval | Yellow | `bg-yellow-100 text-yellow-800` |
| Approved | Blue | `bg-blue-100 text-blue-800` |
| Paid | Green | `bg-green-100 text-green-800` |
| Cancelled | Red | `bg-red-100 text-red-800` |

### Table Columns (Updated)

| Column | Description | Sortable |
|--------|-------------|----------|
| Period | `period_start` - `period_end` | Yes |
| Pay Date | `pay_date` | Yes |
| Employees | Count of employees in this run | Yes |
| Gross Pay | `total_gross` | Yes |
| Deductions | Total deductions | Yes |
| Net Pay | `total_net_pay` | Yes |
| Status | draft/pending_approval/approved/paid | Yes |
| Actions | View / Edit / Approve | - |

**Note**: The table only shows runs for the selected Pay Group.

---

## 2. Payroll Run Detail - Slide-over Panel

> **Updated**: 2025-12-08
> **Change**: Changed from full page (`/payroll/runs/:id`) to slide-over panel for better UX

### Design Rationale

- Content is not extensive enough to warrant a full page
- Slide-over panel keeps context (list visible)
- Consistent with Employee Detail Sidebar pattern
- Allows quick switching between different payroll runs

### History Page with Detail Panel (`/payroll/history`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Payroll History                                              [2025 ▼]  │
├────────────────────────────────────────────┬────────────────────────────┤
│ [Payroll Runs Table]                       │ [Detail Panel - 400px]     │
│                                            │                            │
│ Period     | Pay Date | Employees | Status │ Dec 1-15, 2025        [X] │
│ ──────────────────────────────────────────│ Pay Date: Dec 20, 2025     │
│ Dec 1-15 ● | Dec 20   | 4         | Paid   │                            │
│ Nov 16-30  | Dec 5    | 4         | Paid   │ ┌──────────┐ ┌──────────┐ │
│ Nov 1-15   | Nov 20   | 4         | Paid   │ │Total Gross│ │Deductions│ │
│                                            │ │$11,538.46 │ │-$2,756   │ │
│                                            │ └──────────┘ └──────────┘ │
│                                            │ ┌──────────┐ ┌──────────┐ │
│                                            │ │ Net Pay  │ │Employees │ │
│                                            │ │$8,781.89 │ │    4     │ │
│                                            │ └──────────┘ └──────────┘ │
│                                            │                            │
│                                            │ Employer Costs             │
│                                            │ CPP: $560.42  EI: $274.61 │
│                                            │ Total: $835.03            │
│                                            │                            │
│                                            │ ─────────────────────────  │
│                                            │ Employees                  │
│                                            │ ┌─────────┬──────┬──────┐ │
│                                            │ │Name     │Gross │Net   │ │
│                                            │ │Jane Doe │$2,884│$2,195│ │
│                                            │ │John S.  │$2,884│$2,195│ │
│                                            │ │...      │      │      │ │
│                                            │ └─────────┴──────┴──────┘ │
│                                            │                            │
│                                            │ [Download All] [Resend]   │
└────────────────────────────────────────────┴────────────────────────────┘
```

### Detail Panel Sections

1. **Header**: Period, Pay Date, Close button
2. **Summary Cards (2x2 grid)**: Gross, Deductions, Net Pay, Employees
3. **Employer Costs**: CPP, EI, Total (compact row)
4. **Employee List**: Simplified table (Name, Gross, Net)
5. **Actions**: Download All Paystubs, Resend All

### Component: `PayrollRunDetailPanel.svelte`

```typescript
interface Props {
  payrollRun: PayrollRun;
  payrollRecords: PayrollRecord[];
  onClose: () => void;
}
```

---

## 2.1 Payroll Run Detail - Full Page (Optional)

> **Note**: Full page view is still available at `/payroll/runs/:id` for users who prefer a dedicated page view or need to share a direct link.

### Full Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Payroll > Dec 1-15, 2025                       │
│                                                             │
│ [Header Bar]                                                │
│ Pay Period: Dec 1-15, 2025                    [Status: ●]  │
│ Pay Date: December 20, 2025                                 │
│                                    [Approve] [Download CSV] │
├─────────────────────────────────────────────────────────────┤
│ [Holiday Alert - if holidays in period]                     │
│ 🎄 Christmas Day (Dec 25) falls in this period             │
│                                  [Manage Holiday Hours →]   │
├─────────────────────────────────────────────────────────────┤
│ [Summary Cards]                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │ Total Gross  │ │ Total Deduct │ │ Total Net    │        │
│ │ $23,076.90   │ │ $4,500.00    │ │ $18,576.90   │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │ Employer CPP │ │ Employer EI  │ │ Employer Cost│        │
│ │ $1,000.00    │ │ $560.00      │ │ $1,560.00    │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│ [Employee Payroll Table]                                    │
│ ┌───────────┬───────┬────────┬────────┬────────┬────────┐ │
│ │ Employee  │ Gross │ CPP    │ EI     │ Tax    │ Net    │ │
│ ├───────────┼───────┼────────┼────────┼────────┼────────┤ │
│ │ Jane Doe  │$2,307 │ $100.00│ $39.23 │ $290   │$1,878  │ │
│ │   ↳ 🎄    │+$115  │        │        │        │        │ │
│ │ John Smith│$2,000 │ $86.54 │ $34.00 │ $250   │$1,630  │ │
│ └───────────┴───────┴────────┴────────┴────────┴────────┘ │
│                                                             │
│ [Totals Row]                                                │
│ │ TOTAL     │$4,422 │ $186.54│ $73.23 │ $540   │$3,508  │ │
└─────────────────────────────────────────────────────────────┘
```

### Employee Payroll Table Columns

| Column | Description | Editable |
|--------|-------------|----------|
| Employee | Name (click to expand) | No |
| Gross Regular | Regular pay | ✅ |
| Overtime | Overtime pay | ✅ |
| Holiday Pay | Holiday compensation | Auto |
| Holiday Premium | Holiday work premium | ✅ (hours) |
| Vacation Pay | Vacation payout | ✅ |
| CPP (Employee) | CPP deduction | Auto |
| EI (Employee) | EI deduction | Auto |
| Federal Tax | Federal income tax | Auto |
| Provincial Tax | Provincial income tax | Auto |
| Other Deductions | RRSP, union dues, etc. | ✅ |
| Net Pay | Final pay | Calculated |

---

## 3. Employee Payroll Row Expansion

Clicking an employee row expands to show detailed breakdown:

```
┌─────────────────────────────────────────────────────────────┐
│ Jane Doe - Detailed Breakdown                               │
├─────────────────────────────────────────────────────────────┤
│ EARNINGS                          │ DEDUCTIONS              │
│ Regular Pay:        $2,307.69     │ CPP Base:      $100.00 │
│ Overtime (5h):      $  115.38     │ CPP2:          $  0.00 │
│ Holiday Pay (Dec 25): $ 92.31     │ EI:            $ 39.23 │
│ Holiday Premium (8h): $138.46     │ Federal Tax:   $205.00 │
│                                   │ Provincial Tax:$ 85.00 │
│                                   │ RRSP:          $  0.00 │
│                                   │ Union Dues:    $  0.00 │
├───────────────────────────────────┼─────────────────────────┤
│ GROSS TOTAL:        $2,653.84     │ TOTAL DED:     $429.23 │
├─────────────────────────────────────────────────────────────┤
│                           NET PAY: $2,224.61                │
└─────────────────────────────────────────────────────────────┘
│ YTD: Gross $4,615 | CPP $200 | EI $78 | Fed $410 | Prov $170│
└─────────────────────────────────────────────────────────────┘
```

### Earnings Breakdown
- Regular Pay
- Overtime (hours × 1.5 rate)
- Holiday Pay (provincial rules)
- Holiday Premium (hours worked on holiday × 1.5)
- Vacation Pay
- Bonus / Commission

### Deductions Breakdown
- CPP (Base)
- CPP2 (Additional, if applicable)
- EI
- Federal Tax
- Provincial Tax
- RRSP
- Union Dues
- Garnishments

### YTD Summary Row
Shows year-to-date totals for key fields.

---

## 4. Holiday Work Modal

When a pay period contains statutory holidays, this modal allows recording hours worked.

### Modal Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Holiday Hours - Dec 1-15, 2025                        [X]   │
├─────────────────────────────────────────────────────────────┤
│ 🎄 Christmas Day (Dec 25, 2025) - Ontario                   │
│ Regular employees receive holiday pay automatically         │
├─────────────────────────────────────────────────────────────┤
│ Record hours for employees who WORKED on this holiday:      │
│                                                             │
│ ┌──────────────────┬────────────────┬─────────────────────┐│
│ │ Employee         │ Worked         │ Hours Worked        ││
│ ├──────────────────┼────────────────┼─────────────────────┤│
│ │ Jane Doe         │ ☑️             │ [8.0] hours         ││
│ │ John Smith       │ ☐              │ [-.-] hours         ││
│ │ Mary Johnson     │ ☐              │ [-.-] hours         ││
│ └──────────────────┴────────────────┴─────────────────────┘│
│                                                             │
│ ℹ️ Employees who worked will receive:                       │
│    • Regular holiday pay (auto-calculated)                  │
│    • Premium pay at 1.5x regular rate for hours worked     │
├─────────────────────────────────────────────────────────────┤
│           [Cancel]                      [Save Hours]        │
└─────────────────────────────────────────────────────────────┘
```

### Behavior
1. Lists all active employees for the pay period
2. Checkbox enables hours input for that employee
3. Hours input accepts decimals (e.g., 4.5 hours)
4. Save updates payroll calculations automatically

---

## 5. Payroll Calculation Flow

```
                    ┌─────────────────┐
                    │  Employee Data  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐        ┌───────────┐        ┌──────────┐
   │ Gross   │        │ TD1 Claims│        │ Exemptions│
   │ Earnings│        │ F/P BPA   │        │ CPP/EI   │
   └────┬────┘        └─────┬─────┘        └────┬─────┘
        │                   │                   │
        ▼                   ▼                   ▼
   ┌────────────────────────────────────────────────┐
   │              Payroll Calculator                │
   │  • CPP (T4127 Ch.6)                           │
   │  • EI (T4127 Ch.7)                            │
   │  • Federal Tax (T4127 Ch.4)                   │
   │  • Provincial Tax (T4127 Ch.4)                │
   └────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Payroll Record  │
                    │ (Net Pay = G-D) │
                    └─────────────────┘
```

---

## 6. TypeScript Types

```typescript
// payroll-frontend/src/lib/types/payroll.ts

export type PayrollRunStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'paid'
  | 'cancelled';

export interface PayrollRun {
  id: string;
  companyId: string;
  payGroupId: string;   // **Required** - Links to PayGroup
  payGroupName: string; // Denormalized for display
  periodStart: string;  // ISO date
  periodEnd: string;    // ISO date
  payDate: string;      // ISO date
  status: PayrollRunStatus;

  // Aggregates
  totalEmployees: number;
  totalGross: number;      // in cents
  totalDeductions: number; // in cents
  totalNetPay: number;     // in cents

  // Employer costs
  employerCpp: number;     // in cents
  employerEi: number;      // in cents

  // Metadata
  createdAt: string;
  updatedAt: string;
  approvedAt?: string;
  approvedBy?: string;
  paidAt?: string;
}

export interface PayrollRecord {
  id: string;
  payrollRunId: string;
  employeeId: string;

  // Employee snapshot (denormalized for history)
  employeeName: string;
  employeeProvince: string;

  // Earnings
  grossRegular: number;
  grossOvertime: number;
  holidayPay: number;
  holidayPremiumPay: number;
  vacationPayPaid: number;
  bonus: number;
  commission: number;

  // Deductions
  cppEmployee: number;
  cppAdditional: number;  // CPP2
  eiEmployee: number;
  federalTax: number;
  provincialTax: number;
  rrsp: number;
  unionDues: number;
  garnishments: number;

  // Employer contributions
  cppEmployer: number;
  eiEmployer: number;

  // Calculated
  grossTotal: number;
  totalDeductions: number;
  netPay: number;

  // YTD (snapshot at time of payroll)
  ytdGross: number;
  ytdCpp: number;
  ytdEi: number;
  ytdFederalTax: number;
  ytdProvincialTax: number;
}

export interface HolidayWorkEntry {
  payrollRunId: string;
  employeeId: string;
  holidayDate: string;
  holidayName: string;
  hoursWorked: number;
}

export interface PayrollSummary {
  totalGross: number;
  totalDeductions: number;
  totalNetPay: number;
  employerCpp: number;
  employerEi: number;
  totalEmployerCost: number;
}
```

---

## 7. Component Files

```
payroll-frontend/src/lib/components/payroll/
├── PayrollRunsTable.svelte           # List of payroll runs
├── PayrollRunDetail.svelte           # Single run detail view
├── PayrollRecordRow.svelte           # Employee row in run
├── PayrollRecordExpanded.svelte      # Expanded breakdown
├── HolidayWorkModal.svelte           # Holiday hours entry
├── PayrollSummaryCards.svelte        # Summary statistics
├── PayrollStatusBadge.svelte         # Status indicator
├── DraftPayrollView.svelte           # Draft state main view with Recalculate/Finalize
├── DraftPayGroupSection.svelte       # Editable pay group section for Draft state
├── BeforeRunPayGroupSection.svelte   # Before Run pay group with input fields
├── BeforeRunEmployeeRow.svelte       # Before Run employee row (editable)
└── BeforeRunEmployeeExpandedRow.svelte # Before Run expanded row details
```

---

## 8. Run Payroll Workflow

> **Updated**: 2025-12-18
> **Major Change**: Added Draft state editing with Recalculate/Finalize workflow
> **Design Principle**: All data affecting payroll calculations should be entered BEFORE starting the run, but can be edited in Draft state

### Overview

The payroll run page (`/payroll/run/[periodEnd]`) supports multiple states:

| State | Data Input | Calculation | Next Action |
|-------|-----------|-------------|-------------|
| **Before Run** | Hours, Overtime, Leave, Holiday Work, Adjustments | Frontend estimation (Est.) | Start Payroll Run |
| **Draft** | Same as above, can modify | Backend precise calculation | Recalculate → Finalize |
| **Pending Approval** | Read-only | Locked | Approve & Send |
| **Approved** | Read-only | Locked | Mark as Paid |
| **Paid** | Read-only | Locked | - |

**Key Workflow Change (2025-12-18)**:
- Start Payroll Run now creates a `draft` status (not `pending_approval`)
- Draft state allows editing with Recalculate/Finalize workflow
- Finalize transitions draft → pending_approval (read-only)

### 8.1 Before Run State (No payroll_runs record)

When user navigates to `/payroll/run/2025-12-20` and no payroll run exists:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ← Back to Payroll                                                       │
│                                                                         │
│ Pay Date: Friday, December 20, 2025                    [Not Started]    │
│ 2 Pay Groups · 8 Employees                      [Start Payroll Run]     │
├─────────────────────────────────────────────────────────────────────────┤
│ 🎄 Holidays in this period: Christmas Day (Dec 25)    [Manage Hours →] │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│ │Est. Gross  │ │ Deductions │ │ Net Pay    │ │ Employees  │            │
│ │ $18,500    │ │     --     │ │     --     │ │     8      │            │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘            │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─ Bi-weekly Full-time ─────────────────────────────────────────────┐  │
│ │ Bi-weekly · Full-time · Dec 1 - Dec 14    6 Emp  $12k  --  [Add]  │  │
│ ├───────────────────────────────────────────────────────────────────┤  │
│ │ Employee       │Type  │Rate/Salary│Hours│OT │Leave│Est.Gross│ ▶  │  │
│ ├───────────────────────────────────────────────────────────────────┤  │
│ │ Sarah Johnson  │Salary│$60,000/yr │  -  │ 0 │  0  │ $2,307  │ ▶  │  │
│ │ Michael Chen   │Hourly│$25.00/hr  │[80] │[5]│ 8h  │ $2,187  │ ▶  │  │
│ │ Lisa Wong      │Hourly│$22.50/hr  │[64] │ 0 │  0  │ $1,440  │ ▶  │  │
│ └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│ ℹ️ Click "Start Payroll Run" to calculate deductions and net pay       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Table Columns**:

| Column | Description | Editable |
|--------|-------------|----------|
| Employee | Name (click to expand) | No |
| Type | "Salary" or "Hourly" badge | No |
| Rate/Salary | `$XX,XXX/yr` or `$XX.XX/hr` | No |
| Hours | Regular hours (hourly only) | Yes |
| OT | Overtime hours | Yes |
| Leave | Total leave hours (VAC + SIC) | Yes (click to open modal) |
| Est. Gross | Frontend calculated estimate | No (auto-calculated) |
| ▶ | Expand/collapse row | - |

**Key Features**:
- **Complete data input**: All payroll-affecting data can be entered before starting
- **Real-time estimation**: Est. Gross updates as user enters data
- **Expandable rows**: Click ▶ to see detailed breakdown and edit more fields
- Summary cards show estimated totals (Deductions and Net Pay show `--` until Start)

### 8.2 Expanded Row Design (Before Run)

Click the ▶ button to expand an employee row:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Michael Chen                                                       [▼]  │
├─────────────────────┬─────────────────────┬─────────────────────────────┤
│     EARNINGS        │    DEDUCTIONS       │          LEAVE              │
│  (double-click edit)│   (after Start)     │        (editable)           │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│ Regular Pay  $2,000 │ CPP         --      │ 🏖️ Vacation                 │
│ Overtime(5h)  $187  │ EI          --      │    Hours: [8]               │
│ Holiday Pay    --   │ Federal Tax --      │    Balance: 72h ($1,800)    │
│ Vacation(8h) $200   │ Provincial  --      │                             │
│                     │ RRSP        --      │ 🏥 Sick                     │
│─────────────────────│─────────────────────│    Hours: [0]               │
│ Est. Gross  $2,387  │ Total       --      │    Balance: 40h             │
└─────────────────────┴─────────────────────┴─────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│ ONE-TIME ADJUSTMENTS                                        [+ Add]     │
├─────────────────────────────────────────────────────────────────────────┤
│ 💰 Bonus: Q4 Performance                                    +$500.00    │
│ 🎁 Taxable Benefit: Holiday gift card                       +$100.00    │
│ 💵 Reimbursement: Mileage (non-taxable)                      +$75.00    │
│ ➖ Deduction: Extra RRSP contribution                        -$100.00   │
└─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                         EST. NET PAY: --                                │
│               (Start Payroll Run to calculate CPP/EI/Tax)               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Expanded Row Sections**:

1. **EARNINGS Column** (Left)
   - Shows all earnings items with amounts
   - **Double-click to inline edit**: Regular Pay, Overtime hours, etc.
   - Est. Gross = sum of all earnings

2. **DEDUCTIONS Column** (Middle)
   - Shows `--` placeholder before Start
   - After Start, shows calculated CPP, EI, Tax, etc.

3. **LEAVE Column** (Right)
   - Editable input fields for Vacation and Sick hours
   - Shows current balance (hours and dollars)
   - Updates Est. Gross when leave hours change

4. **ONE-TIME ADJUSTMENTS Section** (Bottom)
   - `[+ Add]` button to add new adjustment
   - Types: Bonus, Taxable Benefit, Reimbursement, Deduction
   - Each item shows icon, description, and amount
   - Can delete items with X button

**Inline Edit Behavior**:
- Normal state: Display value
- Hover state: Show edit icon
- Click/double-click: Show input field
- Enter or blur: Save value
- Escape: Cancel edit

### 8.3 Data Input Rules (Before Run)

**Hours Input** (Hourly employees only):
1. Default value pre-filled based on pay period (e.g., 80 for bi-weekly)
2. Input allows decimals (e.g., 37.5 hours)
3. Validation: Must be > 0 for hourly employees

**Overtime Input**:
1. Available for all employee types
2. Calculated at 1.5x regular rate
3. Default: 0

**Leave Input**:
1. Vacation: Deducted from balance, paid at regular rate
2. Sick: Tracked separately, provincial rules apply
3. Balance shown in real-time

**One-Time Adjustments**:
| Type | Icon | Taxable | CPP | EI |
|------|------|---------|-----|-----|
| Bonus | 💰 | Yes | Yes | Yes |
| Retroactive Pay | ⏪ | Yes | Yes | Yes |
| Taxable Benefit | 🎁 | Yes | No | Configurable |
| Reimbursement | 💵 | No | No | No |
| Deduction | ➖ | Pre-tax | Reduces taxable | - |

### 8.4 Estimated Gross Calculation (Frontend)

Before Start, the frontend calculates Est. Gross in real-time:

```
Est. Gross = Regular Pay + Overtime Pay + Leave Pay + Adjustments

Where:
- Salaried: Regular Pay = annual_salary / pay_periods_per_year
- Hourly: Regular Pay = regular_hours × hourly_rate
- Overtime Pay = overtime_hours × hourly_rate × 1.5
- Leave Pay = leave_hours × hourly_rate (or derived from salary)
- Adjustments = sum of all positive adjustments - deductions
```

**Note**: Deductions (CPP, EI, Tax) are NOT calculated until Start is clicked.

### 8.5 Start Payroll Run

When user clicks "Start Payroll Run":

1. **Validation**:
   - Check all hourly employees have hours entered (> 0)
   - If validation fails, show error and prevent start

2. **Send Data to Backend**:
   All input data is sent to the backend for precise calculation:
   ```typescript
   interface StartPayrollRunRequest {
     payDate: string;
     employeeInputs: Array<{
       employeeId: string;
       regularHours?: number;
       overtimeHours?: number;
       leaveEntries?: LeaveEntry[];
       holidayWorkEntries?: HolidayWorkEntry[];
       adjustments?: Adjustment[];
       overrides?: {
         regularPay?: number;
         overtimePay?: number;
       };
     }>;
   }
   ```

3. **Backend Calculation**:
   - Create `payroll_runs` record with status = `draft`
   - For each employee:
     - Calculate gross earnings (using input data)
     - Calculate CPP (5.95% employee, 5.95% employer)
     - Calculate EI (1.66% employee, 1.4× employer)
     - Calculate Federal Tax
     - Calculate Provincial Tax
   - Create `payroll_records` for each employee
   - Store original input data in `input_data` JSONB column for each record

4. **Update UI**:
   - Status badge changes to "Draft" (editable state)
   - Summary cards show calculated totals (including Deductions and Net Pay)
   - Employee table shows all calculated amounts
   - Header shows "Recalculate" and "Finalize" buttons
   - All input fields remain editable in Draft state

### 8.6 Review & Edit (Draft State)

After Start, the UI transitions to "Draft" state where all data remains editable:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [Draft Badge]                                                           │
│ Pay Date: Friday, December 20, 2025                                     │
│                                          [Recalculate] [Finalize]       │
├─────────────────────────────────────────────────────────────────────────┤
│ ⚠️ Unsaved Changes: You have modified employee data. Click              │
│    Recalculate to update CPP, EI, and tax calculations.                │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│ │ Employees  │ │Total Gross │ │ Deductions │ │ Net Pay    │            │
│ │     8      │ │ $18,615    │ │  $4,289    │ │ $14,326    │            │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘            │
├─────────────────────────────────────────────────────────────────────────┤
│ Deduction Breakdown                                                     │
│ ┌──────────────┬──────────────┬──────────────┐                         │
│ │CPP Employee  │CPP Employer  │EI Employee   │                         │
│ │  $856.24     │  $856.24     │  $238.40     │                         │
│ ├──────────────┼──────────────┼──────────────┤                         │
│ │EI Employer   │Federal Tax   │Provincial Tax│                         │
│ │  $333.76     │  $1,892.36   │  $1,302.00   │                         │
│ └──────────────┴──────────────┴──────────────┘                         │
│                          Total Employer Cost: $1,190.00                 │
├─────────────────────────────────────────────────────────────────────────┤
│ [Pay Group Sections with editable employee data]                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Draft State Features**:
- **Status Badge**: Yellow "Draft" badge indicates editable state
- **Editable Fields**: Hours, Overtime, Leave, Adjustments can all be modified
- **Warning Banner**: Appears when any record is modified, prompts user to Recalculate
- **Recalculate Button**: Disabled when no changes; enabled when records modified
- **Finalize Button**: Disabled when records are modified (must Recalculate first)

**Editable Items in Draft State**:
| Field | Description | Location |
|-------|-------------|----------|
| Regular Hours | Hourly employee regular hours | Inline in row |
| Overtime Hours | OT hours for all employees | Inline in row |
| Leave Hours | Vacation/Sick hours taken | Leave column or modal |
| Adjustments | Bonus, Retro Pay, Benefits, etc. | Expanded row |
| Salaried Override | Override salary calculation | Expanded row |

**Key Differences from Before Run**:
- Deductions column shows actual calculated values (CPP, EI, Tax)
- Net Pay shows calculated values
- Deduction Breakdown section shows employer/employee contributions
- Changes set `is_modified` flag on affected records
- Warning banner appears until Recalculate is clicked

### 8.7 Recalculate

When user modifies any data after Start:

1. **Visual Feedback**:
   - Yellow warning banner appears: "Data has been modified. Click Recalculate to update deductions."
   - Modified fields are highlighted
   - "Recalculate" button appears (or becomes enabled)

2. **Recalculate Action**:
   - User clicks "Recalculate"
   - All input data is sent to backend
   - Backend recalculates CPP, EI, Tax for all employees
   - UI updates with new values
   - Warning banner disappears

3. **Why Recalculate is Needed**:
   - CPP/EI have annual maximums that depend on YTD amounts
   - Tax brackets depend on total taxable income
   - Changing any earnings item affects all deductions
   - Frontend cannot accurately calculate these

### 8.8 Finalize (Draft → Pending Approval)

The "Finalize" action transitions the payroll run from Draft (editable) to Pending Approval (read-only):

1. **Pre-conditions**:
   - Status must be `draft`
   - No modified records (`hasModifiedRecords === false`)
   - If records are modified, user must click "Recalculate" first

2. **Finalize Action**:
   - User clicks "Finalize" button
   - System validates no pending modifications
   - Status changes from `draft` to `pending_approval`
   - **All fields become read-only**

3. **Post-Finalize UI**:
   - Status badge changes to "Pending Approval"
   - Edit capabilities are disabled
   - "Approve & Send Paystubs" button appears

**Button States**:
| State | Recalculate | Finalize |
|-------|-------------|----------|
| Draft, no changes | Disabled | Enabled |
| Draft, has changes | Enabled | Disabled |
| Pending Approval | Hidden | Hidden |

### 8.8.1 Revert to Draft (Pending Approval → Draft)

> **Added**: 2025-12-23

When a payroll run is in `pending_approval` status, the user can click "Revert to Draft" to return to the editable `draft` state for further modifications.

**Pre-conditions**:
- Status must be `pending_approval`

**Revert Action**:
1. User clicks "Revert to Draft" button
2. System changes status from `pending_approval` to `draft`
3. All fields become editable again

**Post-Revert UI**:
- Status badge changes to "Draft"
- Edit capabilities are re-enabled
- "Recalculate" and "Finalize" buttons reappear

**Button Location**: Header actions area, next to "Approve & Send" button

**Use Cases**:
- User discovers an error after finalizing but before approval
- Need to add a last-minute adjustment or bonus
- Correction of hours or leave entries

### 8.9 Approve

After Finalize, the payroll run can be approved:

1. User reviews totals in read-only mode
2. Clicks "Approve & Send Paystubs" → Opens confirmation modal (see Section 10)
3. System generates paystubs for all employees
4. System sends paystubs via email (PDF attachment)
5. Status changes to "Approved"

### 8.10 Mark as Paid

1. After bank transfer complete
2. User clicks "Mark as Paid"
3. Status changes to "Paid"
4. Locked from further edits

### 8.11 Route Structure

```
/payroll                    → Payroll Dashboard (upcoming pay periods)
/payroll/run/[periodEnd]    → Payroll Run Page (before/after run)
/payroll/history            → Past payroll runs
```

### 8.12 State Machine Summary

```
                    ┌─────────────┐
                    │ Before Run  │
                    │ (no record) │
                    └──────┬──────┘
                           │ Start Payroll Run
                           ▼
                    ┌─────────────┐
              ┌────►│    Draft    │◄────┐
              │     │ (editable)  │     │
              │     └──────┬──────┘     │
              │            │            │
         Recalculate       │       Edit Data
              │            │            │
              └────────────┴────────────┘
                           │ Finalize
                           ▼
                    ┌─────────────┐
              ┌────►│  Pending    │
              │     │  Approval   │
   Revert to  │     │ (read-only) │
     Draft    │     └──────┬──────┘
              │            │ Approve & Send
              └────────────┤
                           ▼
                    ┌─────────────┐
                    │  Approved   │
                    └──────┬──────┘
                           │ Mark as Paid
                           ▼
                    ┌─────────────┐
                    │    Paid     │
                    └─────────────┘
```

**State Descriptions**:
| State | Editable | Actions Available |
|-------|----------|-------------------|
| Before Run | Yes | Start Payroll Run |
| Draft | Yes | Edit, Recalculate, Finalize |
| Pending Approval | No | Approve & Send Paystubs, Revert to Draft |
| Approved | No | Mark as Paid, Download/Resend Paystubs |
| Paid | No | Download/Resend Paystubs |

---

## 9. Paystub Management

> **Added**: 2025-12-08
> **Trigger**: Approve payroll → auto-generate and send paystubs

### 9.1 Header Actions (Status-Based)

**Before Approval** (status = draft | pending_approval):
```
┌─────────────────────────────────────────────────────────────┐
│ Pay Period: Dec 1-15, 2025                [Pending Approval]│
│ Pay Date: December 20, 2025                                 │
│                                    [Export CSV] [Approve]   │
└─────────────────────────────────────────────────────────────┘
```

**After Approval** (status = approved | paid):
```
┌─────────────────────────────────────────────────────────────┐
│ Pay Period: Dec 1-15, 2025                    [Approved ✓]  │
│ Pay Date: December 20, 2025                                 │
│            [Export CSV] [Download All Paystubs] [Resend All]│
└─────────────────────────────────────────────────────────────┘
```

**New Buttons**:
| Button | Visibility | Function |
|--------|------------|----------|
| Download All Paystubs | status = approved/paid | Download all paystubs as ZIP |
| Resend All | status = approved/paid | Resend email to all employees |

### 9.2 Employee Table - Paystub Column

Add "Paystub" column to show send status:

```
┌───────────┬───────┬────────┬────────┬─────────────┬─────────┐
│ Employee  │ Gross │ Deduct │ Net    │ Paystub     │ Actions │
├───────────┼───────┼────────┼────────┼─────────────┼─────────┤
│ Jane Doe  │$2,307 │ $429   │$1,878  │ ✅ Sent     │ [⋯]     │
│           │       │        │        │ Dec 20 2:30p│         │
├───────────┼───────┼────────┼────────┼─────────────┼─────────┤
│ John Smith│$2,000 │ $370   │$1,630  │ ⚠️ Failed   │ [⋯]     │
│           │       │        │        │ Click retry │         │
├───────────┼───────┼────────┼────────┼─────────────┼─────────┤
│ Mary Doe  │$1,800 │ $320   │$1,480  │ ⏳ Sending  │ [⋯]     │
└───────────┴───────┴────────┴────────┴─────────────┴─────────┘
```

**Paystub Status Badge**:
| Status | Icon | Color | Tailwind Class | Subtext |
|--------|------|-------|----------------|---------|
| Pending | ⏳ | Gray | `bg-gray-100 text-gray-600` | "Not generated" |
| Sending | ⏳ | Blue | `bg-blue-100 text-blue-600` | "Sending..." |
| Sent | ✅ | Green | `bg-green-100 text-green-700` | Timestamp |
| Failed | ⚠️ | Red | `bg-red-100 text-red-700` | "Click to retry" |

### 9.3 Row Actions Menu

Extend the existing actions menu:

```
[⋯] Click to expand:
┌──────────────────────────┐
│ 📄 View Breakdown        │  ← existing
│ ─────────────────────────│
│ ⬇️ Download Paystub      │  ← NEW
│ 📧 Resend Paystub        │  ← NEW
└──────────────────────────┘
```

| Action | Availability | Description |
|--------|--------------|-------------|
| View Breakdown | Always | Expand row to show earnings/deductions |
| Download Paystub | status = approved/paid | Download individual PDF |
| Resend Paystub | status = approved/paid | Resend email to this employee |

---

## 10. Approve Confirmation Modal

When user clicks "Approve" button, show confirmation modal:

```
┌─────────────────────────────────────────────────────────────┐
│ Approve Payroll Run                                    [X]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ You are about to approve the payroll for:                   │
│                                                             │
│   Pay Period: Dec 1-15, 2025                               │
│   Employees: 4                                              │
│   Total Net Pay: $8,781.89                                 │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ✓ Generate paystubs for all employees                  ││
│ │ ✓ Email paystubs automatically (PDF attachment)        ││
│ │ ✓ Lock payroll from further edits                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ⚠️ This action cannot be undone.                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                [Cancel]              [Approve & Send]       │
└─────────────────────────────────────────────────────────────┘
```

### Modal Behavior
1. Display summary of what will happen
2. "Approve & Send" triggers:
   - Status change to "Approved"
   - Paystub PDF generation
   - Email sending to all employees
3. Show progress indicator (Section 11)

---

## 11. Send Progress Indicator

After clicking "Approve & Send", show progress overlay:

### During Sending
```
┌─────────────────────────────────────────────────────────────┐
│ 📧 Sending Paystubs                                         │
│                                                             │
│ ████████████░░░░░░░░  3/4 employees                        │
│                                                             │
│ ✅ Jane Doe - Sent                                         │
│ ✅ John Smith - Sent                                       │
│ ✅ Mary Doe - Sent                                         │
│ ⏳ James Wilson - Sending...                               │
└─────────────────────────────────────────────────────────────┘
```

### Success State
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Payroll Approved                                         │
│                                                             │
│ 4 paystubs sent successfully.                              │
│                                           [View Details]    │
└─────────────────────────────────────────────────────────────┘
```

### Partial Failure State
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Payroll Approved with Issues                            │
│                                                             │
│ 3 paystubs sent, 1 failed.                                 │
│                              [View Details] [Retry Failed]  │
└─────────────────────────────────────────────────────────────┘
```

### Behavior
- Progress bar updates in real-time
- Each employee row updates as email is sent
- "Retry Failed" button attempts to resend only failed emails
- User can dismiss and continue working; status shown in table

---

## 12. Leave Management

> **Added**: 2025-12-08
> **Scope**: Vacation + Sick Leave (Statutory Leave deferred to Phase 2)

### 12.1 Leave Alert Banner

When employees have leave recorded for the pay period, show an alert similar to Holiday Alert:

```
┌─────────────────────────────────────────────────────────────┐
│ 🏖️ 2 employees have leave recorded                         │
│    Jane Doe (8h vacation), John Smith (4h sick)             │
│                                      [Manage Leave Hours →] │
└─────────────────────────────────────────────────────────────┘
```

**Behavior**:
- Appears below Holiday Alert (if both exist)
- Shows summary of employees with leave
- Click button opens LeaveModal

### 12.2 Leave Modal

Modal for recording leave taken during the pay period:

```
┌─────────────────────────────────────────────────────────────┐
│ Leave Hours - Dec 1-15, 2025                           [X]  │
├─────────────────────────────────────────────────────────────┤
│ Record leave taken during this pay period:                  │
│                                                             │
│ ┌─────────────┬──────────────┬─────────┬─────────────────┐ │
│ │ Employee    │ Leave Type   │ Hours   │ Balance         │ │
│ ├─────────────┼──────────────┼─────────┼─────────────────┤ │
│ │ Jane Doe ▼  │ Vacation ▼   │ [8.0]   │ 74h ($1,850)    │ │
│ │ John Smith▼ │ Sick     ▼   │ [4.0]   │ 36h remaining   │ │
│ │ [+ Add Row] │              │         │                 │ │
│ └─────────────┴──────────────┴─────────┴─────────────────┘ │
│                                                             │
│ ℹ️ Leave Types:                                            │
│    • Vacation: Paid from accrued balance                   │
│    • Sick: Paid per provincial requirements                │
├─────────────────────────────────────────────────────────────┤
│                [Cancel]                    [Save Leave]     │
└─────────────────────────────────────────────────────────────┘
```

**Modal Columns**:

| Column | Type | Description |
|--------|------|-------------|
| Employee | Combobox | Select from active employees (exclude already added) |
| Leave Type | Dropdown | Vacation / Sick |
| Hours | Number input | Decimal hours (0.5 - 80) |
| Balance | Read-only | Shows remaining balance after this leave |

**Leave Types Supported**:

| Type | Icon | Color | Calculation |
|------|------|-------|-------------|
| Vacation | 🏖️ | Blue (`bg-blue-100`) | Hours × Hourly Rate, deducted from balance |
| Sick | 🏥 | Orange (`bg-orange-100`) | Hours × Hourly Rate, within provincial limits |

### 12.3 Employee Table - Leave Column

Add "Leave" column to PayrollRecordTable (after Gross, before Deductions):

```
┌───────────┬───────┬────────┬────────┬────────┬─────────┐
│ Employee  │ Gross │ Leave  │ Deduct │ Net Pay│ Actions │
├───────────┼───────┼────────┼────────┼────────┼─────────┤
│ Jane Doe  │$2,307 │ 8h VAC │ $429   │ $1,878 │ [⋯]     │
│ John Smith│$2,000 │ 4h SIC │ $370   │ $1,630 │ [⋯]     │
│ Mary Doe  │$1,800 │   -    │ $320   │ $1,480 │ [⋯]     │
└───────────┴───────┴────────┴────────┴────────┴─────────┘
```

**Leave Column Display**:
- Format: `{hours}h {TYPE}` (e.g., "8h VAC", "4h SIC")
- Multiple types: Show first type + "+1 more"
- No leave: Show "-"
- Clickable: Opens LeaveModal for editing

### 12.4 Expanded Row - Leave Details

In PayrollRecordExpandedRow, add leave breakdown:

```
┌─────────────────────────────────────────────────────────────┐
│ Jane Doe - Detailed Breakdown                               │
├─────────────────────────────────────────────────────────────┤
│ EARNINGS                          │ DEDUCTIONS              │
│ Regular Pay:        $1,800.00     │ CPP Base:      $100.00 │
│ Overtime (0h):      $    0.00     │ EI:            $ 39.23 │
│ Vacation Pay:       $  200.00     │ Federal Tax:   $205.00 │
│   └── 8h × $25.00/h               │ Provincial Tax:$ 85.00 │
│   └── Balance: 74h ($1,850)       │                        │
│ Sick Pay:           $    0.00     │                        │
│ Holiday Pay:        $    0.00     │                        │
├───────────────────────────────────┼─────────────────────────┤
│ GROSS TOTAL:        $2,000.00     │ TOTAL DED:     $429.23 │
├─────────────────────────────────────────────────────────────┤
│                           NET PAY: $1,570.77                │
└─────────────────────────────────────────────────────────────┘
```

**Leave Details Show**:
- Hours taken × Hourly rate
- Updated balance (hours and dollar amount)
- Color-coded by leave type

### 12.5 Leave Type Badge Component

Reusable badge for leave type display:

```typescript
// LeaveTypeBadge.svelte
interface Props {
  type: 'vacation' | 'sick';
  hours: number;
  compact?: boolean;  // true = "8h VAC", false = "8 hours Vacation"
}
```

| Type | Compact | Full | Tailwind Classes |
|------|---------|------|------------------|
| Vacation | 8h VAC | 8 hours Vacation | `bg-blue-100 text-blue-700` |
| Sick | 4h SIC | 4 hours Sick | `bg-orange-100 text-orange-700` |

### 12.6 TypeScript Types

```typescript
// Add to payroll-frontend/src/lib/types/payroll.ts

export type LeaveType = 'vacation' | 'sick';

export interface LeaveEntry {
  id: string;
  employeeId: string;
  employeeName: string;
  leaveType: LeaveType;
  hours: number;
  payRate: number;       // hourly rate at time of leave
  leavePay: number;      // calculated: hours × payRate
}

// Extend PayrollRecord
export interface PayrollRecord {
  // ... existing fields ...

  // Leave tracking
  leaveEntries: LeaveEntry[];
  vacationHoursTaken: number;
  vacationPayPaid: number;      // existing field
  sickHoursTaken: number;
  sickPayPaid: number;

  // Balance snapshot (after this period)
  vacationBalanceHours: number;
  vacationBalanceDollars: number;
  sickBalanceHours: number;
}

// Leave type labels
export const LEAVE_TYPE_LABELS: Record<LeaveType, { short: string; full: string; icon: string }> = {
  vacation: { short: 'VAC', full: 'Vacation', icon: '🏖️' },
  sick: { short: 'SIC', full: 'Sick', icon: '🏥' }
};
```

### 12.7 Calculation Flow

```
User adds leave entry in LeaveModal
  │
  ├─► Frontend calculates preview:
  │   • leavePay = hours × payRate
  │   • newBalance = currentBalance - leavePay
  │
  ├─► User clicks "Save Leave"
  │   POST /api/payroll/leave
  │   with entries[]
  │
  ├─► Backend validates:
  │   • Employee exists and active
  │   • Hours within reasonable limits
  │   • Vacation: sufficient balance
  │   • Sick: within provincial limits
  │
  └─► Payroll recalculates:
      • Regular hours reduced by leave hours
      • Leave pay added to earnings
      • Vacation balance updated
      • Deductions recalculated on new gross
```

### 12.8 Provincial Sick Leave Rules

| Province | Paid Days/Year | Notes |
|----------|----------------|-------|
| BC | 5 days | After 90 days employment |
| Ontario | 3 days | Unpaid; IDEL days separate |
| Alberta | 0 days | No statutory paid sick leave |
| Quebec | 2 days | After 3 months employment |
| Federal | 10 days | After 30 days employment |

**Implementation Note**: Sick leave limits should be configurable per province and tracked per calendar year.

### 12.9 Component Files

```
payroll-frontend/src/lib/components/payroll/
├── ... existing files ...
├── LeaveModal.svelte         # NEW: Leave hours entry modal
├── LeaveAlert.svelte         # NEW: Alert banner for leave
└── LeaveTypeBadge.svelte     # NEW: Leave type badge
```

### 12.10 Run Payroll Workflow (Updated)

```
Step 1: Create New Run
  └─► Click "+ Run Payroll" → Auto-detect next pay period → Create draft

Step 2: Review & Edit
  └─► System pre-fills all employees → User edits overtime/bonuses

Step 3: Holiday Check
  └─► If holidays exist → Show alert banner → User clicks "Manage Holiday Hours"

Step 4: Leave Check (NEW)
  └─► User clicks "Manage Leave Hours" → Record vacation/sick leave taken
  └─► System recalculates: reduces regular hours, adds leave pay, updates balances

Step 5: Vacation Payout (Optional, NEW)
  └─► For accrual employees: Click row menu → "Vacation Payout"
  └─► Select payout type (scheduled/cashout/termination) and amount
  └─► Payout added to gross earnings, balance deducted

Step 6: Approve
  └─► User reviews totals → Click "Approve" → Generate paystubs → Email PDFs

Step 7: Mark as Paid
  └─► After bank transfer → Click "Mark as Paid" → Status = "Paid"
```

---

## 13. Vacation Payout

### 13.1 Overview

Vacation payout allows employees using the **accrual** method to cash out their vacation balance at any time (not just year-end). This feature integrates with the payroll run workflow.

**Key Constraints**:
- Only available for employees with `vacationConfig.payoutMethod === 'accrual'`
- Employees using `pay_as_you_go` receive vacation pay each paycheck (no balance to cash out)
- Supports partial payouts (employee can cash out part of balance)

### 13.2 Entry Points

| Entry Point | Action | When to Use |
|-------------|--------|-------------|
| PayrollRecordTable row menu | "Vacation Payout" option | During payroll processing |
| Employee Detail sidebar | "Cash Out Vacation" button | Quick access from employee view |

### 13.3 VacationPayoutModal Component

**Pattern**: Follow `LeaveModal.svelte` design patterns.

#### Modal Layout

```
+-------------------------------------------------------------+
| Vacation Payout                                         [X]  |
+-------------------------------------------------------------+
| +-----------------------------------------------------------+
| | [Avatar] Jane Doe                                         |
| | Current Balance: 80h ($2,000.00)                          |
| +-----------------------------------------------------------+
|                                                             |
| ----------------------------------------------------------- |
|                                                             |
| Payout Type                                                 |
| +---------------+ +---------------+ +---------------+       |
| | [📅]          | | [💵]          | | [🚪]          |       |
| | Scheduled     | | Cashout       | | Termination   |       |
| | (selected)    | | Request       | |               |       |
| +---------------+ +---------------+ +---------------+       |
|                                                             |
| Payout Amount                                               |
| ( ) Full Balance (80h = $2,000.00)                          |
| (*) Partial Payout                                          |
|     Hours: [40______] = $1,000.00                           |
|                                                             |
| ----------------------------------------------------------- |
|                                                             |
| After Payout                                                |
| +-----------------------------------------------------------+
| | Remaining Balance: 40h ($1,000.00)                        |
| +-----------------------------------------------------------+
|                                                             |
| [ℹ] This payout will be added to the current pay period    |
|     and included in the employee's gross earnings.          |
|                                                             |
+-------------------------------------------------------------+
|                [Cancel]              [Add to Payroll]       |
+-------------------------------------------------------------+
```

#### Component Interface

```typescript
interface VacationPayoutModalProps {
  employee: Employee;
  payrollRecord?: PayrollRecord; // If adding to existing run
  onClose: () => void;
  onSave: (payout: VacationPayoutEntry) => void;
}
```

#### State Management

```typescript
// Local state within modal
let payoutType: VacationPayoutReason = 'scheduled';
let isFullPayout = true;
let partialHours = 0;

// Computed values
$: payRate = employee.regularPayRate ?? 0;
$: payoutAmount = isFullPayout
  ? employee.vacationBalance
  : partialHours * payRate;
$: remainingBalance = employee.vacationBalance - payoutAmount;
```

### 13.4 Payout Types

| Type | Icon | Code | Use Case |
|------|------|------|----------|
| Scheduled | 📅 | `scheduled` | Planned year-end or anniversary payout |
| Cashout Request | 💵 | `cashout_request` | Employee requests mid-year cashout |
| Termination | 🚪 | `termination` | Full balance on employment end |

### 13.5 Integration with PayrollRecordTable

Add vacation payout option to row action menu (only for accrual employees):

```svelte
<!-- In PayrollRecordTable.svelte row menu -->
{#if record.employee.vacationConfig?.payoutMethod === 'accrual'}
  <DropdownItem on:click={() => openVacationPayoutModal(record)}>
    <DollarSign class="mr-2 h-4 w-4" />
    Vacation Payout
  </DropdownItem>
{/if}
```

### 13.6 Integration with PayrollRecordExpandedRow

Show vacation payout in the Earnings breakdown section:

```
+-------------------------------------------------------------+
| EARNINGS                                                    |
+-------------------------------------------------------------+
| Regular Pay                                      $2,000.00  |
| Overtime                                           $200.00  |
| Vacation Payout                                    $500.00  |
|   └─ 20h × $25.00/h (Cashout Request)                       |
+-------------------------------------------------------------+
| Total Earnings                                   $2,700.00  |
+-------------------------------------------------------------+
```

### 13.7 TypeScript Types

```typescript
// Add to payroll-frontend/src/lib/types/payroll.ts

export type VacationPayoutReason = 'scheduled' | 'cashout_request' | 'termination';

export const VACATION_PAYOUT_LABELS: Record<VacationPayoutReason, { label: string; icon: string }> = {
  scheduled: { label: 'Scheduled Payout', icon: '📅' },
  cashout_request: { label: 'Cashout Request', icon: '💵' },
  termination: { label: 'Termination', icon: '🚪' }
};

export interface VacationPayoutEntry {
  id: string;
  employeeId: string;
  employeeName: string;
  payoutReason: VacationPayoutReason;
  hours: number;
  payRate: number;         // Hourly rate at time of payout
  payoutAmount: number;    // hours × payRate
  notes?: string;
}

// Extend PayrollRecord interface
export interface PayrollRecord {
  // ... existing fields ...

  // Vacation payout tracking
  vacationPayoutEntries?: VacationPayoutEntry[];
  totalVacationPayout?: number;
}
```

### 13.8 Validation Rules

| Rule | Description | Error Message |
|------|-------------|---------------|
| Balance check | Payout hours ≤ available balance | "Insufficient vacation balance" |
| Minimum hours | Payout hours > 0 | "Payout hours must be greater than 0" |
| Accrual only | Only for accrual method employees | Hidden from UI for non-accrual employees |

### 13.9 Component Files

```
payroll-frontend/src/lib/components/payroll/
├── ... existing files ...
├── VacationPayoutModal.svelte     # NEW: Vacation payout entry modal
└── VacationPayoutBadge.svelte     # NEW: Badge for payout reason (optional)
```

### 13.10 Data Flow

```
1. User clicks "Vacation Payout" in row menu
   └─► Open VacationPayoutModal with employee data

2. User selects payout type and amount
   └─► Real-time preview of remaining balance

3. User clicks "Add to Payroll"
   └─► Validate: hours ≤ balance
   └─► Create VacationPayoutEntry

4. Modal closes, PayrollRecord updated
   └─► vacationPayoutEntries.push(entry)
   └─► totalVacationPayout += entry.payoutAmount

5. PayrollRecordExpandedRow re-renders
   └─► Show payout in Earnings section

6. On payroll approval
   └─► Payout included in gross earnings
   └─► CPP/EI/Tax calculated on total
   └─► Employee vacation balance deducted
```

---

## 14. One-Time Pay Adjustments (Ad-hoc Inputs)

> **Added**: 2025-12-11
> **Reference**: CRA PDOC calculator fields analysis
> **Purpose**: Support temporary/one-time pay items during Payroll Run

### 14.1 Overview

While **Pay Group** defines recurring deductions and benefits, **Payroll Run** supports one-time/ad-hoc pay adjustments that vary each pay period. This aligns with CRA PDOC calculator capabilities.

### 14.2 Supported One-Time Items

| Category | Item | Tax Treatment | CPP/EI Treatment | Entry Location |
|----------|------|---------------|------------------|----------------|
| **Additional Earnings** | Bonus | Taxable income | CPP: Yes, EI: Yes | Row menu → "Add Bonus" |
| | Retroactive Pay | Taxable income | CPP: Yes, EI: Yes | Row menu → "Add Retro Pay" |
| | Taxable Benefit (one-time) | Taxable income | See note below | Row menu → "Add Taxable Benefit" |
| | Reimbursement (non-taxable) | Not taxable | No CPP/EI | Row menu → "Add Reimbursement" |
| **Additional Deductions** | One-time RRSP | Pre-tax deduction | Reduces taxable income | Row menu → "Add Deduction" |
| | One-time RPP/PRPP | Pre-tax deduction | Reduces taxable income | Row menu → "Add Deduction" |

### 14.3 Taxable Benefits - EI Treatment Note

Per CRA guidelines, taxable benefits must be classified for EI purposes:

| Type | Description | EI Insurable? | Example |
|------|-------------|---------------|---------|
| Cash benefit | Monetary allowance | Yes | Car allowance, phone stipend |
| Non-cash, insurable | Benefit with cash equivalent | Yes | Gift cards, employer-paid parking |
| Non-cash, not insurable | Benefit without cash equivalent | No | Use of company car, group insurance premiums |

**MVP Approach**: For simplicity, default to "Non-cash, insurable for EI" for most taxable benefits. Advanced users can override if needed.

### 14.4 One-Time Adjustment Modal

**Entry Point**: PayrollRecordTable row menu → "Add Adjustment"

```
┌─────────────────────────────────────────────────────────────┐
│ Add One-Time Adjustment                                 [X]  │
├─────────────────────────────────────────────────────────────┤
│ Employee: Jane Doe                                          │
│                                                             │
│ Adjustment Type:                                            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 💰 Bonus    │ │ ⏪ Retro    │ │ 🎁 Taxable  │            │
│ │ (selected)  │ │    Pay      │ │   Benefit   │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│ ┌─────────────┐ ┌─────────────┐                            │
│ │ 💵 Reimburse│ │ ➖ Deduction│                            │
│ │   (non-tax) │ │   (one-time)│                            │
│ └─────────────┘ └─────────────┘                            │
│                                                             │
│ Amount:                                                     │
│ CA$ [500.00_______]                                        │
│                                                             │
│ Description (optional):                                     │
│ [Q4 Performance Bonus________________________]              │
│                                                             │
│ ℹ️ This bonus will be added to gross earnings and          │
│    subject to CPP, EI, and income tax deductions.          │
├─────────────────────────────────────────────────────────────┤
│                [Cancel]              [Add to Payroll]       │
└─────────────────────────────────────────────────────────────┘
```

### 14.5 TypeScript Types

```typescript
// Add to payroll-frontend/src/lib/types/payroll.ts

export type OneTimeAdjustmentType =
  | 'bonus'
  | 'retroactive_pay'
  | 'taxable_benefit'
  | 'reimbursement'
  | 'one_time_deduction';

export type TaxableBenefitEiType =
  | 'cash_insurable'
  | 'non_cash_insurable'
  | 'non_cash_not_insurable';

export const ONE_TIME_ADJUSTMENT_CONFIG: Record<OneTimeAdjustmentType, {
  label: string;
  icon: string;
  isTaxable: boolean;
  affectsCpp: boolean;
  affectsEi: boolean;
  isDeduction: boolean;
  description: string;
}> = {
  bonus: {
    label: 'Bonus',
    icon: '💰',
    isTaxable: true,
    affectsCpp: true,
    affectsEi: true,
    isDeduction: false,
    description: 'One-time bonus payment (performance, holiday, signing, etc.)'
  },
  retroactive_pay: {
    label: 'Retroactive Pay',
    icon: '⏪',
    isTaxable: true,
    affectsCpp: true,
    affectsEi: true,
    isDeduction: false,
    description: 'Back pay for salary increase or missed wages'
  },
  taxable_benefit: {
    label: 'Taxable Benefit',
    icon: '🎁',
    isTaxable: true,
    affectsCpp: false,  // Benefits don't affect CPP
    affectsEi: true,    // Default: insurable (can override)
    isDeduction: false,
    description: 'One-time taxable benefit (gift, training, parking, etc.)'
  },
  reimbursement: {
    label: 'Reimbursement',
    icon: '💵',
    isTaxable: false,
    affectsCpp: false,
    affectsEi: false,
    isDeduction: false,
    description: 'Non-taxable expense reimbursement (mileage, supplies, etc.)'
  },
  one_time_deduction: {
    label: 'One-Time Deduction',
    icon: '➖',
    isTaxable: false,  // Pre-tax deduction
    affectsCpp: false,
    affectsEi: false,
    isDeduction: true,
    description: 'One-time pre-tax deduction (extra RRSP, RPP, loan repayment)'
  }
};

export interface OneTimeAdjustment {
  id: string;
  employeeId: string;
  type: OneTimeAdjustmentType;
  amount: number;         // in cents
  description?: string;

  // For taxable benefits only
  eiTreatment?: TaxableBenefitEiType;
}

// Extend PayrollRecord interface
export interface PayrollRecord {
  // ... existing fields ...

  // One-time adjustments
  oneTimeAdjustments: OneTimeAdjustment[];
  totalBonus: number;
  totalRetroactivePay: number;
  totalTaxableBenefits: number;
  totalReimbursements: number;
  totalOneTimeDeductions: number;
}
```

### 14.6 PayrollRecordExpandedRow Display

Update earnings/deductions breakdown to show one-time items:

```
┌─────────────────────────────────────────────────────────────┐
│ Jane Doe - Detailed Breakdown                               │
├─────────────────────────────────────────────────────────────┤
│ EARNINGS                          │ DEDUCTIONS              │
│ Regular Pay:        $2,307.69     │ CPP Base:      $115.00 │
│ Overtime (5h):      $  115.38     │ CPP2:          $  0.00 │
│ ────────────────────────────────  │ EI:            $ 48.23 │
│ 💰 Bonus:           $  500.00     │ Federal Tax:   $320.00 │
│    └── Q4 Performance             │ Provincial Tax:$145.00 │
│ 🎁 Taxable Benefit: $  100.00     │ RRSP:          $ 50.00 │
│    └── Holiday gift card          │ ➖ One-time:   $100.00 │
│ 💵 Reimbursement:   $   75.00     │    └── Extra RRSP      │
│    └── Mileage (non-taxable)      │                        │
├───────────────────────────────────┼─────────────────────────┤
│ GROSS TOTAL:        $3,098.07     │ TOTAL DED:     $778.23 │
│ (Taxable: $3,023.07)              │                        │
├─────────────────────────────────────────────────────────────┤
│                           NET PAY: $2,319.84                │
└─────────────────────────────────────────────────────────────┘
```

### 14.7 Row Actions Menu (Updated)

```
[⋯] Click to expand:
┌──────────────────────────────┐
│ 📄 View Breakdown            │ ← existing
│ ─────────────────────────────│
│ ➕ Add Adjustment            │ ← NEW (opens modal)
│    ├── 💰 Bonus              │
│    ├── ⏪ Retroactive Pay    │
│    ├── 🎁 Taxable Benefit    │
│    ├── 💵 Reimbursement      │
│    └── ➖ One-Time Deduction │
│ ─────────────────────────────│
│ 🏖️ Vacation Payout           │ ← existing (accrual only)
│ ─────────────────────────────│
│ ⬇️ Download Paystub          │ ← existing (post-approval)
│ 📧 Resend Paystub            │ ← existing (post-approval)
└──────────────────────────────┘
```

### 14.8 Calculation Flow

```
1. User clicks "Add Adjustment" → Select type → Enter amount
   └─► Creates OneTimeAdjustment entry

2. PayrollRecord recalculates:
   └─► Earnings:
       • grossRegular (unchanged)
       • + bonus
       • + retroactivePay
       • + taxableBenefits
       • = Taxable earnings (for tax calculation)
       • + reimbursements (non-taxable, added to net)

   └─► Deductions:
       • CPP recalculated on taxable earnings
       • EI recalculated (with EI treatment for benefits)
       • Federal/Provincial tax recalculated
       • + oneTimeDeductions (pre-tax)

3. Net Pay = Taxable Earnings - Deductions + Reimbursements
```

### 14.9 CRA PDOC Fields Mapping

| CRA PDOC Field | Our Implementation | Notes |
|----------------|-------------------|-------|
| Bonus payment | `bonus` adjustment | ✅ Fully supported |
| Retroactive payment | `retroactive_pay` adjustment | ✅ Fully supported |
| Taxable benefits (cash/non-cash) | `taxable_benefit` + `eiTreatment` | ✅ Supported with EI options |
| Employer RRSP contributions | Pay Group → `CustomDeduction` | ✅ Recurring config |
| Employee RRSP contributions | Employee → `rrspPerPeriod` | ✅ Recurring config |
| Employee RPP/PRPP contributions | `one_time_deduction` or Pay Group | ✅ One-time or recurring |
| Union dues | Employee → `unionDuesPerPeriod` | ✅ Recurring config |
| Alimony/maintenance payments | Garnishments module | ✅ See `12_garnishments_deductions.md` |
| Living in prescribed zone | ❌ Not supported (MVP) | Low priority - regional |
| Tax-exempt reserve income | ❌ Not supported (MVP) | Low priority - specific |
| Other annual deductions | ❌ Not supported (MVP) | Requires TSO approval |

### 14.10 Component Files

```
payroll-frontend/src/lib/components/payroll/
├── ... existing files ...
├── OneTimeAdjustmentModal.svelte   # NEW: One-time adjustment entry
└── AdjustmentBadge.svelte          # NEW: Badge for adjustment type
```

---

## 15. Pay Group 配置对 Before Run UI 的影响

Before Run 界面根据 Pay Group 的配置动态显示不同的内容。本节说明各配置字段如何驱动 UI 渲染。

### 15.1 配置字段概览

Pay Group 配置直接影响 Before Run 展开行的显示：

| 配置字段 | 类型 | UI 影响 |
|---------|------|--------|
| `leaveEnabled` | `boolean` | 控制 Leave 列的显示/隐藏 |
| `overtimePolicy.bankTimeEnabled` | `boolean` | 控制 Bank Time 选项的显示 |
| `groupBenefits` | `GroupBenefits` | Deductions 列显示 Group Benefits 预览 |
| `customDeductions` | `CustomDeduction[]` | Deductions 列显示默认启用的自定义扣款 |
| `statutoryDefaults.cppExemptByDefault` | `boolean` | 显示 "CPP Exempt" 徽章 |
| `statutoryDefaults.eiExemptByDefault` | `boolean` | 显示 "EI Exempt" 徽章 |

### 15.2 leaveEnabled 条件渲染

**配置**: `payGroup.leaveEnabled: boolean`

**影响范围**:
- 表头 Leave 列 (`<th>`)
- 员工行 Leave 列 (`<td>`)
- 展开行 Leave 区块

**渲染逻辑**:
```svelte
<!-- 表头 -->
{#if payGroup.leaveEnabled}
  <th>Leave</th>
{/if}

<!-- 员工行 -->
{#if leaveEnabled}
  <td><!-- Leave 输入 --></td>
{/if}

<!-- 展开行网格 -->
<div class={leaveEnabled ? 'grid-cols-3' : 'grid-cols-2'}>
  <div>Earnings</div>
  {#if leaveEnabled}
    <div>Leave</div>
  {/if}
  <div>Deductions</div>
</div>
```

**colspan 调整**:
- `leaveEnabled: true` → 展开行 `colspan=8`
- `leaveEnabled: false` → 展开行 `colspan=7`

### 15.3 Bank Time 支持

**配置**: `payGroup.overtimePolicy.bankTimeEnabled: boolean`

**显示条件**:
- `overtimePolicy.bankTimeEnabled === true`
- `input.overtimeHours > 0`

**UI 组件**:
```
┌─────────────────────────────────────┐
│ How would you like to handle OT?   │
│                                     │
│ (●) Pay Out: $187.50 (1.5×)        │
│ ( ) Bank Time: 7.5 hours           │
└─────────────────────────────────────┘
```

**数据字段**: `EmployeePayrollInput.overtimeChoice: 'pay_out' | 'bank_time'`

**计算逻辑**:
- Pay Out 金额: `overtimeHours × hourlyRate × 1.5`
- Bank Time 小时: `overtimeHours × 1.5` (按 1.5 倍计入时间银行)

### 15.4 Deductions 预览

**配置**:
- `payGroup.groupBenefits: GroupBenefits`
- `payGroup.customDeductions: CustomDeduction[]`

**显示内容**:

1. **Group Benefits** (仅显示启用的):
   ```
   Health:    $50.00/period
   Dental:    $25.00/period
   Vision:    $10.00/period
   ```
   - 读取 `groupBenefits.{type}.enabled` 判断是否显示
   - 显示 `groupBenefits.{type}.employeeDeduction` 金额

2. **Custom Deductions** (仅显示 `isDefaultEnabled: true`):
   ```
   RRSP Match:   $100.00  (fixed)
   Union Dues:   2.5%     (percentage)
   ```
   - `calculationType: 'fixed'` → 显示固定金额
   - `calculationType: 'percentage'` → 显示百分比值

3. **Est. Total**:
   ```
   Est. Deductions: $185.00
   ```
   - 计算公式: `Σ(Group Benefits) + Σ(Custom Deductions)`
   - Percentage 类型根据 `estimatedGross` 计算: `grossPay × percentage / 100`

**注意**: Before Run 阶段的 Deductions 为预估值，实际扣款在 Calculate 后确定。

### 15.5 Statutory Defaults 显示

**配置**:
- `payGroup.statutoryDefaults.cppExemptByDefault: boolean`
- `payGroup.statutoryDefaults.eiExemptByDefault: boolean`

**显示位置**: Deductions 列标题旁

**UI 样式**:
```svelte
<div class="flex items-center gap-2">
  <h4>Deductions (Est.)</h4>
  {#if statutoryDefaults.cppExemptByDefault}
    <span class="px-2 py-0.5 text-xs font-medium bg-warning-100
                 text-warning-700 rounded-full border border-warning-200">
      CPP Exempt
    </span>
  {/if}
  {#if statutoryDefaults.eiExemptByDefault}
    <span class="px-2 py-0.5 text-xs font-medium bg-warning-100
                 text-warning-700 rounded-full border border-warning-200">
      EI Exempt
    </span>
  {/if}
</div>
```

**用途**: 提醒用户该 Pay Group 的员工默认豁免 CPP/EI，避免意外扣款。

### 15.6 组件 Props 传递链

配置数据从 Pay Group 向下传递：

```
BeforeRunPayGroupSection
├─ payGroup.leaveEnabled ──────────────┐
├─ payGroup.overtimePolicy ────────────┤
├─ payGroup.groupBenefits ─────────────┤
├─ payGroup.customDeductions ──────────┤
├─ payGroup.statutoryDefaults ─────────┤
│                                      │
└─► BeforeRunEmployeeRow               │
    ├─ leaveEnabled ◄──────────────────┤
    ├─ overtimePolicy ◄────────────────┤
    ├─ groupBenefits ◄─────────────────┤
    ├─ customDeductions ◄──────────────┤
    ├─ statutoryDefaults ◄─────────────┤
    │                                  │
    └─► BeforeRunEmployeeExpandedRow   │
        ├─ leaveEnabled ◄──────────────┤
        ├─ overtimePolicy ◄────────────┤
        ├─ groupBenefits ◄─────────────┤
        ├─ customDeductions ◄──────────┤
        └─ statutoryDefaults ◄─────────┘
```

### 15.7 数据类型定义

```typescript
// Pay Group 配置类型 (来自 pay-group.ts)
interface OvertimePolicy {
  multiplier: number;        // 1.5
  bankTimeEnabled: boolean;  // 是否允许 Bank Time
}

interface GroupBenefits {
  health: BenefitConfig;
  dental: BenefitConfig;
  vision: BenefitConfig;
  life: BenefitConfig;
  disability: BenefitConfig;
  other: BenefitConfig;
}

interface BenefitConfig {
  enabled: boolean;
  employerContribution: number;
  employeeDeduction: number;
}

interface CustomDeduction {
  id: string;
  name: string;
  calculationType: 'fixed' | 'percentage';
  amount: number;
  isDefaultEnabled: boolean;
}

interface StatutoryDefaults {
  cppExemptByDefault: boolean;
  eiExemptByDefault: boolean;
}

// Payroll Input 类型 (来自 payroll.ts)
type OvertimeChoice = 'pay_out' | 'bank_time';

interface EmployeePayrollInput {
  // ... 其他字段 ...
  overtimeChoice?: OvertimeChoice;  // 默认 'pay_out'
}
```

### 15.8 配置与 UI 状态对照表

| Pay Group 配置 | Before Run UI 状态 |
|---------------|-------------------|
| `leaveEnabled: false` | Leave 列隐藏，grid 为 2 列 |
| `leaveEnabled: true` | Leave 列显示，grid 为 3 列 |
| `overtimePolicy.bankTimeEnabled: false` | 无 Bank Time 选项 |
| `overtimePolicy.bankTimeEnabled: true` | OT > 0 时显示选择 UI |
| `groupBenefits.health.enabled: true` | Deductions 显示 Health 行 |
| `customDeductions[].isDefaultEnabled: true` | Deductions 显示该扣款 |
| `statutoryDefaults.cppExemptByDefault: true` | 显示 "CPP Exempt" 徽章 |
| `statutoryDefaults.eiExemptByDefault: true` | 显示 "EI Exempt" 徽章 |
