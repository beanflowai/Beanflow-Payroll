# Employees UI Design

> **Last Updated**: 2025-12-09
> **Source**: Consolidated from `binary-enchanting-ritchie.md` (latest design)
> **Updated**: Added Pay Group and Tags support

---

## 0. Key Business Rules

### Province of Employment (POE)

**CRA Requirement**: Payroll taxes are calculated based on the **Province of Employment**, NOT the company's location.

| Scenario | Province of Employment |
|----------|------------------------|
| Employee works at employer's office | Province where the office is located |
| Remote work (with agreement) | Province of the employer's establishment the employee is "attached to" |
| Employee doesn't report to any location | Province where wages are paid from |

**What POE Affects**:
- ✅ **Provincial Tax Rate** - Calculated using POE tax brackets
- ✅ **Holiday Pay Formula** - Ontario uses 1/20 formula, BC uses average day's pay
- ✅ **Statutory Holidays** - Different holidays by province
- ❌ **Vacation Rate** - NOT affected (national standard: 4%/6%)

**Reference**: [CRA - Determine the Province of Employment](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/set-up-new-employee/determine-province-employment.html)

---

### Vacation Rate

| Years of Service | Standard Rate | Notes |
|------------------|---------------|-------|
| 0 - 5 years | 4% | All provinces |
| 5+ years | 6% | All provinces |
| 10+ years (Federal) | 8% | Federal employers only |

**Editability**:
- ✅ **Editable** - Employer can override with a higher rate (e.g., contract agreement)
- 🔄 **Auto-suggested** - System calculates recommended rate from `hireDate`

---

### Vacation Balance

**Editability**:
- ❌ **Read-only** for existing employees (calculated by payroll system)
- ✅ **Adjustable** via "Adjust Balance" button for:
  - Initial balance when importing existing employees
  - Manual corrections (with audit trail)

---

## 1. Employee List Page (`/employees`)

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Header Bar]                                                │
│ Employees                          [+ Add Employee] [Import]│
├─────────────────────────────────────────────────────────────┤
│ [Filter Bar]                                                │
│ Status: [All▼]  Pay Group: [All▼]  Tags: [All▼]  🔍 Search │
├─────────────────────────────────────────────────────────────┤
│ [Summary Cards]                                             │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│ │ Total: 12 │ │ Active: 10│ │ Salaried:8│ │ Hourly: 4 │   │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────┤
│ [Employee Table]                                            │
│ ┌────┬──────────┬──────────┬──────────┬────────┬─────────┐│
│ │ ✓  │ Name     │Pay Group │ Tags     │Salary  │ Status  ││
│ ├────┼──────────┼──────────┼──────────┼────────┼─────────┤│
│ │ □  │ Jane Doe │Bi-wk FT  │🏷️Sales   │ $60,000│ Active  ││
│ │ □  │ John Sm..│Monthly FT│🏷️Exec    │ $42/hr │ Active  ││
│ │ □  │ Bob W... │Bi-wk PT  │🏷️Sales   │ $25/hr │ Active  ││
│ └────┴──────────┴──────────┴──────────┴────────┴─────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Table Columns

The table uses a **Column Group Tab** system to organize fields:

#### All Groups - Fixed Columns
| Column | Description | Editable | Notes |
|--------|-------------|----------|-------|
| ☑️ Checkbox | Batch operations | - | Always visible |
| Name | First + Last Name | ✅ Dbl-click | Always visible |
| Actions | ⋯ menu | - | Always visible |

#### Personal Tab
| Column | Editable | Notes |
|--------|----------|-------|
| SIN | ✅ Dbl-click | Masked by default, click to reveal |
| Email | ✅ Dbl-click | Optional |
| Status | ✅ Dbl-click | Draft/Active/Terminated |

#### Employment Tab
| Column | Editable | Notes |
|--------|----------|-------|
| Pay Group | ✅ Dbl-click | **Required** - Select from company's Pay Groups |
| Province | ✅ Dbl-click | **Province of Employment** (see rules above) |
| Tags | ✅ Dbl-click | Optional - Multi-select tags for custom grouping |
| Hire Date | ✅ Dbl-click | Used for Years of Service calculation |

**Note**: Pay Frequency and Employment Type are now determined by the selected Pay Group.

#### Compensation Tab
| Column | Editable | Notes |
|--------|----------|-------|
| Salary/Rate | ✅ Dbl-click | Toggle between annual salary and hourly rate |
| Per Period | ❌ Read-only | Calculated: `annualSalary / payPeriods` |
| Vacation Rate | ✅ Dbl-click | Dropdown: 4%/6%/8% |
| Vac Balance | ❌ Read-only* | *Editable only for new employees |

#### Tax Tab
| Column | Editable | Notes |
|--------|----------|-------|
| Fed Claim | ✅ Dbl-click | Auto-filled with 2025 BPA ($16,129) |
| Prov Claim | ✅ Dbl-click | Auto-filled based on province |
| CPP Exempt | ✅ Dbl-click | Checkbox |
| EI Exempt | ✅ Dbl-click | Checkbox |

#### Deductions Tab
| Column | Editable | Notes |
|--------|----------|-------|
| RRSP/Period | ✅ Dbl-click | Per-period RRSP contribution |
| Union Dues | ✅ Dbl-click | Per-period union dues |

### Row Actions Menu

- **View Details** → Opens slide-out panel
- **Edit** → Opens edit modal
- **Terminate** → Confirmation dialog, then terminates

### Filter Options

| Filter | Type | Options |
|--------|------|---------|
| Status | Dropdown | All, Active, Terminated |
| Pay Group | Dropdown | All, + list of Pay Groups |
| Tags | Multi-select | All defined tags |
| Search | Text | Searches name, email |

### Filter Logic

| Filter | Logic |
|--------|-------|
| Status: All | No filter |
| Status: Active | `termination_date IS NULL` |
| Status: Terminated | `termination_date IS NOT NULL` |
| Pay Group: [name] | `pay_group_id = selected_id` |
| Tags: [tag] | `tags CONTAINS selected_tag` |

---

## 2. Employee Detail Panel (Slide-out)

Opens when clicking "View Details" or a row. Displays read-only information organized in sections.

### Section 1: Basic Information
- Employee ID
- SIN: `***-***-789` [Click to reveal]
- Province of Employment
- Pay Group (with Pay Frequency and Employment Type)
- Hire Date
- Tags (if any)

### Section 2: Compensation
- Type: `Salaried` | `Hourly`
- Annual Salary: `$60,000.00` (or Hourly Rate: `$42.00/hr`)
- Per-Period Gross: `$2,307.69`

### Section 3: Tax Information (TD1)
- Federal Claim Amount: `$16,129.00`
- Provincial Claim Amount: `$12,747.00`
- CPP Exempt: `No`
- EI Exempt: `No`
- CPP2 Exempt: `No`

### Section 4: Optional Deductions
- RRSP Per Period: `$0.00`
- Union Dues Per Period: `$0.00`

### Section 5: Vacation Configuration

| Field | Value | Editable | Notes |
|-------|-------|----------|-------|
| Payout Method | `Accrual` / `Pay as you go` / `Lump sum` | ✅ Yes | Dropdown select |
| Vacation Rate | `4%` / `6%` / `8%` | ✅ Yes | Dropdown, auto-suggested based on Years of Service |
| Years of Service | `3.5 years` | ❌ No | Calculated from `hireDate` |
| Current Balance | `$1,234.56` [Adjust] | ❌ Read-only | "Adjust" button for manual corrections |

**Vacation Rate Auto-Suggestion Logic**:
```
if (yearsOfService < 5) → suggest 4%
else if (yearsOfService < 10) → suggest 6%
else if (isFederalEmployer) → suggest 8%
else → suggest 6%
```

**Years of Service Calculation**:
```typescript
yearsOfService = (today - hireDate).days / 365.25
```

### Section 6: YTD Summary
- YTD Gross: `$X,XXX.XX`
- YTD CPP: `$X,XXX.XX`
- YTD EI: `$X,XXX.XX`
- YTD Net Pay: `$X,XXX.XX`

### Section 7: Actions
- [Edit Employee Information]
- [View Payment History]

---

## 3. Add/Edit Employee Modal

### Form Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Add New Employee                                      [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ── Personal Information ─────────────────────────────────   │
│ First Name *         Last Name *                           │
│ [_______________]    [_______________]                     │
│                                                             │
│ SIN *                Email                                 │
│ [___-___-___]        [_______________]                     │
│                                                             │
│ ── Employment Details ───────────────────────────────────   │
│ Pay Group *          Province *                            │
│ [▼ Bi-weekly FT_]    [▼ Ontario______]                     │
│                                                             │
│ Hire Date *          Tags                                  │
│ [📅 YYYY-MM-DD]      [+ Add Tag...]                        │
│                                                             │
│ ── Compensation ─────────────────────────────────────────   │
│ (●) Annual Salary    ( ) Hourly Rate                       │
│ $ [___________]      $ [___________] /hr                   │
│                                                             │
│ ── Tax Information (TD1) ────────────────────────────────   │
│ ℹ️ Auto-filled with 2025 Basic Personal Amounts            │
│                                                             │
│ Federal Claim *      Provincial Claim *                    │
│ $ [16,129.00___]     $ [12,747.00___]                      │
│                                                             │
│ ☐ CPP Exempt   ☐ EI Exempt   ☐ CPP2 Exempt                │
│                                                             │
│ ── Optional Deductions ──────────────────────────────────   │
│ RRSP Per Period      Union Dues Per Period                 │
│ $ [0.00________]     $ [0.00________]                      │
│                                                             │
│ ── Vacation Settings ────────────────────────────────────   │
│ Payout Method        Vacation Rate                         │
│ [▼ Accrual_____]     [▼ 4%_________]                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│           [Cancel]                [Add Employee]            │
└─────────────────────────────────────────────────────────────┘
```

### Form Sections

#### Personal Information
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| First Name | text | ✅ | min 1 char |
| Last Name | text | ✅ | min 1 char |
| SIN | masked input | ✅ | Format: XXX-XXX-XXX |
| Email | email | ❌ | Valid email format |

#### Employment Details
| Field | Type | Required | Options |
|-------|------|----------|---------|
| Pay Group | select | ✅ | List of company's Pay Groups |
| Province | select | ✅ | 13 provinces/territories |
| Hire Date | date | ✅ | Calendar picker |
| Tags | multi-select | ❌ | User-defined tags (create on-the-fly) |

**Note**: Pay Frequency and Employment Type are inherited from the selected Pay Group.

#### Compensation
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Salary Type | radio | ✅ | Annual Salary OR Hourly Rate |
| Annual Salary | currency | Conditional | Required if salary type = Annual |
| Hourly Rate | currency | Conditional | Required if salary type = Hourly |

#### Tax Information (TD1)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Federal Claim | currency | ✅ | Auto-filled with BPA, editable |
| Provincial Claim | currency | ✅ | Auto-filled based on province |
| CPP Exempt | checkbox | ❌ | Default: unchecked |
| EI Exempt | checkbox | ❌ | Default: unchecked |
| CPP2 Exempt | checkbox | ❌ | Default: unchecked |

#### Optional Deductions
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| RRSP Per Period | currency | ❌ | Default: $0.00 |
| Union Dues Per Period | currency | ❌ | Default: $0.00 |

#### Vacation Settings
| Field | Type | Required | Options |
|-------|------|----------|---------|
| Payout Method | select | ❌ | Accrual, Pay as you go, Lump sum |
| Vacation Rate | select | ❌ | 4%, 6%, 8% |

### Auto-fill Behavior

When province is selected:
1. Federal Claim → Set to current year's federal BPA ($16,129 for 2025)
2. Provincial Claim → Set to province-specific BPA

---

## 4. SIN Display Component

### Masked State (Default)
```
SIN: ***-***-789 [👁️]
```

### Revealed State (On Click)
```
SIN: 123-456-789 [🙈]
```

### Behavior
- Default: Shows last 3 digits only
- Click eye icon → Reveals full SIN for 10 seconds
- Auto-hides after timeout
- Logs access for audit trail

---

## 5. Data Field → Payroll Calculation Mapping

| Employee Field | Affects Calculation |
|----------------|---------------------|
| `province_of_employment` | Provincial tax rate, holiday list, holiday rules |
| `pay_frequency` | P value (periods/year), per-period gross |
| `annual_salary` / `hourly_rate` | Gross Pay calculation |
| `federal_claim_amount` | Federal tax K1 credit |
| `provincial_claim_amount` | Provincial tax K1P credit |
| `is_cpp_exempt` | Whether to calculate CPP |
| `is_ei_exempt` | Whether to calculate EI |
| `cpp2_exempt` | Whether to calculate CPP2 (over YMPE) |
| `rrsp_per_period` | Reduces taxable income (Factor F) |
| `union_dues_per_period` | Reduces taxable income (Factor U1) |
| `hire_date` | Vacation eligibility (30 days), seniority |
| `vacation_rate` | Vacation pay accumulation rate |

---

## 6. TypeScript Types

```typescript
// payroll-frontend/src/lib/types/employee.ts

export type VacationPayoutMethod = 'accrual' | 'pay_as_you_go' | 'lump_sum';
export type VacationRate = '0.04' | '0.06' | '0.08';
export type EmployeeStatus = 'draft' | 'active' | 'terminated';

// Note: PayFrequency and EmploymentType are now defined in pay-group.ts
// and inherited from the employee's Pay Group

export interface VacationConfig {
  payoutMethod: VacationPayoutMethod;
  vacationRate: VacationRate;
}

export interface Employee {
  id: string;
  companyId: string;

  // Personal Info
  firstName: string;
  lastName: string;
  sin: string;           // For UI (masked or full)
  sinEncrypted: string;  // Encrypted SIN (never sent to frontend)
  email?: string;

  // Employment Details
  payGroupId: string;               // **Required** - Links to PayGroup
  provinceOfEmployment: string;     // e.g., 'ON', 'BC' - determines tax/holiday rules
  tags: string[];                   // User-defined tags for custom grouping
  status: EmployeeStatus;
  hireDate: string;                 // ISO date
  terminationDate?: string;         // ISO date, null if active

  // Computed from Pay Group (read-only)
  // payFrequency and employmentType are derived from payGroupId

  // Compensation
  annualSalary?: number | null;  // in cents (mutually exclusive with hourlyRate)
  hourlyRate?: number | null;    // in cents (mutually exclusive with annualSalary)

  // Tax Information (TD1)
  federalClaimAmount: number;     // in cents
  provincialClaimAmount: number;  // in cents
  isCppExempt: boolean;
  isEiExempt: boolean;
  cpp2Exempt: boolean;

  // Optional Deductions
  rrspPerPeriod: number;      // in cents
  unionDuesPerPeriod: number; // in cents

  // Vacation
  vacationConfig: VacationConfig;
  vacationBalance: number;  // in cents (read-only, updated by payroll)

  // Metadata
  createdAt: string;
  updatedAt: string;
}

// Computed fields (calculated in frontend)
export interface EmployeeComputed {
  yearsOfService: number;        // Calculated from hireDate
  suggestedVacationRate: VacationRate;  // Based on yearsOfService
  perPeriodGross: number;        // annualSalary / payPeriods
  fullName: string;              // firstName + lastName
  isActive: boolean;             // terminationDate === null
}

// Helper function to calculate years of service
export function calculateYearsOfService(hireDate: string): number {
  const hire = new Date(hireDate);
  const today = new Date();
  const diffDays = (today.getTime() - hire.getTime()) / (1000 * 60 * 60 * 24);
  return Math.round((diffDays / 365.25) * 100) / 100; // 2 decimal places
}

// Helper function to suggest vacation rate
export function suggestVacationRate(yearsOfService: number, isFederal = false): VacationRate {
  if (yearsOfService >= 10 && isFederal) return '0.08';
  if (yearsOfService >= 5) return '0.06';
  return '0.04';
}

export interface EmployeeYTD {
  employeeId: string;
  year: number;
  grossPay: number;
  cppContributions: number;
  eiPremiums: number;
  federalTax: number;
  provincialTax: number;
  netPay: number;
}
```

---

## 7. Component Files

```
payroll-frontend/src/lib/components/employees/
├── EmployeeTable.svelte          # Main table with column groups, inline editing
├── EmployeeFilters.svelte        # Status filter tabs + search
├── EmployeeDetailSidebar.svelte  # Right sidebar with full employee details
└── (future) EmployeeFormModal.svelte    # Add/Edit form (not yet implemented)
```

### EmployeeDetailSidebar.svelte (Implemented)

A sticky right sidebar that displays comprehensive employee information when a row is selected.

**Props**:
```typescript
interface Props {
  employee: Employee;
  showSIN: boolean;
  onToggleSIN: () => void;
  onClose: () => void;
}
```

**Sections Displayed**:

| Section | Fields |
|---------|--------|
| **Basic Information** | Name, SIN (with toggle), Email, Status Badge |
| **Employment** | Province, Employment Type, Pay Frequency, Hire Date, Termination Date (if applicable) |
| **Compensation** | Type (Hourly/Salaried), Rate/Salary, Per-Period Gross |
| **Tax Information (TD1)** | Federal Claim, Provincial Claim, CPP/EI/CPP2 Exempt flags |
| **Optional Deductions** | RRSP Per Period, Union Dues Per Period |
| **Vacation** | Payout Method, Vacation Rate, Current Balance |
| **Actions** | Edit Employee, View Pay History buttons |

**Responsive Behavior**:
- Desktop (>1024px): Sticky sidebar, 360px width
- Mobile (≤1024px): Full-screen overlay, 100% width

**Key Features**:
- SIN masking with click-to-reveal toggle
- CPP2 exempt with info tooltip explaining CPT30 form
- Calculated Per-Period Gross based on salary and pay frequency
- Status badges with color coding (Active=green, Draft=yellow)
- Pay Group display with inherited frequency/type
- Tags display with chip-style badges

---

## 8. Employee Tags

Tags allow users to create custom groupings for employees beyond Pay Groups.

### Tag Input Component

```
┌─────────────────────────────────────────────────────────────┐
│ Tags                                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Sales  ✕  │ 🏷️ Toronto  ✕  │ [+ Add Tag...]        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Adding a new tag (dropdown appears):
┌─────────────────────────────────────────────────────────────┐
│ Tags                                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Sales  ✕  │ [Marketing_______________________]      │ │
│ │               ├───────────────────────────────────────┐ │ │
│ │               │ Existing Tags:                        │ │ │
│ │               │   🏷️ Marketing                       │ │ │
│ │               │   🏷️ Engineering                     │ │ │
│ │               │   🏷️ Finance                         │ │ │
│ │               │ ─────────────────────────────────────  │ │
│ │               │ ➕ Create "Marketing" as new tag      │ │ │
│ │               └───────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tag Behavior

| Action | Behavior |
|--------|----------|
| Add existing tag | Select from dropdown of all tags used in company |
| Create new tag | Type new name, click "Create" - adds to company's tag list |
| Remove tag | Click X on tag chip |
| Filter by tag | In employee list, select tag from filter dropdown |

### Tag Storage

Tags are stored as an array of strings on the Employee record:

```typescript
// Employee.tags
tags: ['Sales', 'Toronto', 'Senior']
```

Company maintains a derived list of all unique tags for the dropdown:

```typescript
// Computed from all employees
companyTags: string[]  // ['Sales', 'Marketing', 'Engineering', 'Toronto', 'Senior', ...]
```

---

## 9. Integration with Pay Groups

### Pay Group Dropdown in Employee Form

```
Pay Group *
┌─────────────────────────────────────────────────────────────┐
│ [▼ Bi-weekly Full-time                                    ] │
├─────────────────────────────────────────────────────────────┤
│  📋 Bi-weekly Full-time                                     │
│     Every 2 weeks | Full-time | 12 employees               │
│ ─────────────────────────────────────────────────────────── │
│  📋 Bi-weekly Part-time                                     │
│     Every 2 weeks | Part-time | 5 employees                │
│ ─────────────────────────────────────────────────────────── │
│  📋 Monthly Executives                                      │
│     Monthly | Full-time | 3 employees                      │
└─────────────────────────────────────────────────────────────┘
```

### Validation

| Rule | Error Message |
|------|---------------|
| Pay Group is required | "Please select a Pay Group for this employee" |
| No Pay Groups exist | "Please create a Pay Group first in Company > Pay Groups" |

### Empty State (No Pay Groups)

If company has no Pay Groups when adding employee:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ No Pay Groups Found                                      │
│                                                             │
│ Before adding employees, you need to create at least one   │
│ Pay Group to define pay frequency and employment type.     │
│                                                             │
│ [Go to Company Settings →]                                  │
└─────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 2.0
**Created**: 2025-12-08
**Updated**: 2025-12-09 - Added Pay Group and Tags support
