# Remittance UI Design

> **Last Updated**: 2025-12-08
> **Status**: Design Complete

---

## Overview

The Remittance page is a dedicated interface for managing CRA payroll remittances. This is a **core business function** - employers must remit CPP, EI, and income tax deductions to CRA on time to avoid penalties.

### Key User Goals

1. **Know what's due** - See upcoming remittance amount and due date
2. **Track payments** - Record when remittances are paid
3. **View history** - See past remittance records
4. **Generate forms** - Create PD7A vouchers if needed

---

## Navigation

Add "Remittance" to the sidebar navigation:

```
┌─────────────────────┐
│ 📊 Dashboard        │
│ 👥 Employees        │
│ 💰 Run Payroll      │
│ 📜 History          │
│ 🏛️ Remittance      │  ← NEW
│ 📈 Reports          │
│ ⚙️ Settings         │
└─────────────────────┘
```

| Item | Icon | Path |
|------|------|------|
| Remittance | `fa-landmark` | `/remittance` |

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ CRA Remittance                                    [2025 ▼] │
│ Track and manage your payroll deduction remittances         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Remitter Type Badge]  Regular (Monthly) • Due 15th        │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │              UPCOMING REMITTANCE CARD                   ││
│ │  (Highlighted card for next due remittance)             ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Summary Cards Row]                                         │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│ │ YTD Remit │ │ This Year │ │ On Time   │ │ Pending   │   │
│ │ $85,400   │ │ 11 of 12  │ │ 100%      │ │ $8,160    │   │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│                                                             │
│ [Remittance History Table]                                  │
│ ┌──────────┬──────────┬──────────┬──────────┬────────────┐│
│ │ Period   │ Due Date │ Amount   │ Paid     │ Status     ││
│ ├──────────┼──────────┼──────────┼──────────┼────────────┤│
│ │ Dec 2025 │ Jan 15   │ $8,160   │    -     │ ⏳ Pending ││
│ │ Nov 2025 │ Dec 15   │ $7,890   │ Dec 14   │ ✅ Paid    ││
│ │ Oct 2025 │ Nov 15   │ $7,650   │ Nov 12   │ ✅ Paid    ││
│ └──────────┴──────────┴──────────┴──────────┴────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Upcoming Remittance Card

The primary focus element showing the next remittance due.

### States

| State | Color | Icon | Description |
|-------|-------|------|-------------|
| Upcoming | Blue | ⏰ | Due date > 7 days away |
| Due Soon | Yellow | ⚠️ | Due date within 7 days |
| Overdue | Red | 🚨 | Past due date |
| All Paid | Green | ✅ | No pending remittances |

### Layout - Upcoming State

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⏰ NEXT REMITTANCE DUE                              │   │
│  │                                                      │   │
│  │  Period: December 1-31, 2025                        │   │
│  │  Due Date: January 15, 2026                         │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │                                              │   │   │
│  │  │         $8,160.00                           │   │   │
│  │  │         Total Amount Due                    │   │   │
│  │  │                                              │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ CPP        │ │ EI         │ │ Income Tax │       │   │
│  │  │ $3,000.00  │ │ $960.00    │ │ $4,200.00  │       │   │
│  │  │ Emp + Empr │ │ Emp + Empr │ │ Fed + Prov │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘       │   │
│  │                                                      │   │
│  │  ⏰ 38 days until due                               │   │
│  │                                                      │   │
│  │        [Generate PD7A]  [Mark as Paid]              │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Layout - Due Soon State (Yellow)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⚠️ REMITTANCE DUE SOON                    [yellow] │   │
│  │                                                      │   │
│  │  Period: December 1-31, 2025                        │   │
│  │  Due Date: January 15, 2026                         │   │
│  │                                                      │   │
│  │  ...                                                 │   │
│  │                                                      │   │
│  │  ⚠️ Due in 5 days                                   │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Layout - Overdue State (Red)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🚨 REMITTANCE OVERDUE                        [red] │   │
│  │                                                      │   │
│  │  Period: December 1-31, 2025                        │   │
│  │  Due Date: January 15, 2026 (3 days ago)           │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │         $8,160.00 + $244.80 penalty         │   │   │
│  │  │         (3% late fee applied)               │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │  🚨 3 days overdue - Pay immediately to avoid      │   │
│  │     additional penalties                            │   │
│  │                                                      │   │
│  │        [Generate PD7A]  [Mark as Paid]              │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Penalty Display

| Days Late | Penalty Rate | Display |
|-----------|--------------|---------|
| 1-3 days | 3% | "$8,160.00 + $244.80 penalty (3%)" |
| 4-5 days | 5% | "$8,160.00 + $408.00 penalty (5%)" |
| 6-7 days | 7% | "$8,160.00 + $571.20 penalty (7%)" |
| 8+ days | 10% | "$8,160.00 + $816.00 penalty (10%)" |

---

## 2. Summary Cards

Quick stats for the selected year.

```
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ YTD Remitted  │ │ Remittances   │ │ On-Time Rate  │ │ Pending       │
│               │ │               │ │               │ │               │
│   $85,400     │ │   11 of 12    │ │    100%       │ │   $8,160      │
│   ─────────   │ │   ─────────   │ │   ─────────   │ │   ─────────   │
│   Total paid  │ │   Completed   │ │   No late     │ │   1 pending   │
│   this year   │ │   this year   │ │   payments    │ │   remittance  │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

| Card | Value | Subtext | Color |
|------|-------|---------|-------|
| YTD Remitted | Sum of all paid remittances | "Total paid this year" | Primary |
| Remittances | "X of Y" completed | "Completed this year" | Secondary |
| On-Time Rate | Percentage | "No late payments" or "X late" | Green/Red |
| Pending | Amount due | "X pending remittance(s)" | Warning (if overdue) |

---

## 3. Remittance History Table

### Table Columns

| Column | Description | Sortable | Width |
|--------|-------------|----------|-------|
| Period | Month/Quarter name | Yes | 120px |
| Due Date | Remittance due date | Yes | 100px |
| Amount | Total remittance amount | Yes | 120px |
| Paid Date | Date payment was made | Yes | 100px |
| Status | Paid/Pending/Overdue | Yes | 100px |
| Actions | Row actions menu | No | 60px |

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Remittance History                                        [Export] │
├──────────┬──────────┬────────────┬──────────┬───────────┬──────────┤
│ Period   │ Due Date │ Amount     │ Paid     │ Status    │ Actions  │
├──────────┼──────────┼────────────┼──────────┼───────────┼──────────┤
│ Dec 2025 │ Jan 15   │ $8,160.00  │    -     │ ⏳Pending │   [⋯]    │
├──────────┼──────────┼────────────┼──────────┼───────────┼──────────┤
│ Nov 2025 │ Dec 15   │ $7,890.00  │ Dec 14   │ ✅ Paid   │   [⋯]    │
├──────────┼──────────┼────────────┼──────────┼───────────┼──────────┤
│ Oct 2025 │ Nov 15   │ $7,650.00  │ Nov 12   │ ✅ Paid   │   [⋯]    │
├──────────┼──────────┼────────────┼──────────┼───────────┼──────────┤
│ Sep 2025 │ Oct 15   │ $7,500.00  │ Oct 14   │ ✅ Paid   │   [⋯]    │
└──────────┴──────────┴────────────┴──────────┴───────────┴──────────┘
```

### Status Badge

| Status | Icon | Color | Tailwind Classes |
|--------|------|-------|------------------|
| Pending | ⏳ | Gray | `bg-gray-100 text-gray-700` |
| Due Soon | ⚠️ | Yellow | `bg-yellow-100 text-yellow-800` |
| Overdue | 🚨 | Red | `bg-red-100 text-red-800` |
| Paid | ✅ | Green | `bg-green-100 text-green-800` |
| Paid Late | ⚠️✅ | Orange | `bg-orange-100 text-orange-800` |

### Row Actions Menu

```
[⋯] Click to expand:
┌──────────────────────────┐
│ 📄 View Details          │
│ ─────────────────────────│
│ 📥 Download PD7A         │  (if pending)
│ ✅ Mark as Paid          │  (if pending)
│ ─────────────────────────│
│ ✏️ Edit Payment Date     │  (if paid)
└──────────────────────────┘
```

---

## 4. Row Expansion - Remittance Details

Clicking a row expands to show detailed breakdown:

```
┌─────────────────────────────────────────────────────────────────────┐
│ December 2025 Remittance - Detailed Breakdown                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Period: December 1-31, 2025                                         │
│ Due Date: January 15, 2026                                          │
│ Payroll Runs Included: 2 (Dec 15, Dec 31)                          │
│                                                                     │
│ ── Deduction Breakdown ───────────────────────────────────────────  │
│                                                                     │
│ ┌────────────────────────┬────────────────┬────────────────┐       │
│ │ Category               │ Employee       │ Employer       │       │
│ ├────────────────────────┼────────────────┼────────────────┤       │
│ │ CPP Contributions      │    $1,200.00   │    $1,200.00   │       │
│ │ EI Premiums            │      $400.00   │      $560.00   │       │
│ │ Federal Income Tax     │    $3,000.00   │        -       │       │
│ │ Provincial Income Tax  │    $1,200.00   │        -       │       │
│ ├────────────────────────┼────────────────┼────────────────┤       │
│ │ SUBTOTAL               │    $5,800.00   │    $1,760.00   │       │
│ └────────────────────────┴────────────────┴────────────────┘       │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐    │
│ │                    TOTAL: $7,560.00                         │    │
│ └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│ ── Payment Information ───────────────────────────────────────────  │
│                                                                     │
│ Status: ✅ Paid                                                     │
│ Payment Date: December 14, 2025                                     │
│ Payment Method: My Payment (Online)                                 │
│ Confirmation #: PAY-2025-12-001234                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mark as Paid Modal

When user clicks "Mark as Paid":

```
┌─────────────────────────────────────────────────────────────┐
│ Record Remittance Payment                              [X]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ You are recording payment for:                              │
│                                                             │
│   Period: December 2025                                     │
│   Amount: $8,160.00                                         │
│   Due Date: January 15, 2026                               │
│                                                             │
│ ── Payment Details ───────────────────────────────────────  │
│                                                             │
│ Payment Date *                                              │
│ [📅 2025-12-14___________________________________]         │
│                                                             │
│ Payment Method *                                            │
│ [▼ My Payment (CRA Online)_________________________]       │
│                                                             │
│ Confirmation Number (Optional)                              │
│ [PAY-2025-12-001234______________________________]         │
│                                                             │
│ Notes (Optional)                                            │
│ [__________________________________________________]       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                [Cancel]              [Record Payment]       │
└─────────────────────────────────────────────────────────────┘
```

### Payment Method Options

| Method | Value | Description |
|--------|-------|-------------|
| My Payment (CRA Online) | `my_payment` | CRA's online payment portal |
| Pre-Authorized Debit | `pre_authorized_debit` | Automatic bank debit |
| Online Banking | `online_banking` | Through bank's bill payment |
| Wire Transfer | `wire_transfer` | Bank wire transfer |
| Cheque | `cheque` | Physical cheque mailed |

---

## 6. Different Remitter Type Displays

### Quarterly Remitter View

```
┌─────────────────────────────────────────────────────────────────────┐
│ Remittance History                                    [Quarterly]  │
├──────────┬──────────┬────────────┬──────────┬───────────┬──────────┤
│ Quarter  │ Due Date │ Amount     │ Paid     │ Status    │ Actions  │
├──────────┼──────────┼────────────┼──────────┼───────────┼──────────┤
│ Q4 2025  │ Jan 15   │ $2,400.00  │    -     │ ⏳Pending │   [⋯]    │
│ Q3 2025  │ Oct 15   │ $2,200.00  │ Oct 12   │ ✅ Paid   │   [⋯]    │
│ Q2 2025  │ Jul 15   │ $2,100.00  │ Jul 14   │ ✅ Paid   │   [⋯]    │
│ Q1 2025  │ Apr 15   │ $2,000.00  │ Apr 10   │ ✅ Paid   │   [⋯]    │
└──────────┴──────────┴────────────┴──────────┴───────────┴──────────┘
```

### Accelerated Threshold 1 View (Twice Monthly)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Remittance History                          [Accelerated T1]       │
├──────────────┬──────────┬────────────┬──────────┬─────────┬────────┤
│ Period       │ Due Date │ Amount     │ Paid     │ Status  │Actions │
├──────────────┼──────────┼────────────┼──────────┼─────────┼────────┤
│ Dec 16-31    │ Jan 10   │ $12,500    │    -     │⏳Pending│  [⋯]   │
│ Dec 1-15     │ Dec 25   │ $12,300    │ Dec 24   │✅ Paid  │  [⋯]   │
│ Nov 16-30    │ Dec 10   │ $12,100    │ Dec 9    │✅ Paid  │  [⋯]   │
│ Nov 1-15     │ Nov 25   │ $11,900    │ Nov 24   │✅ Paid  │  [⋯]   │
└──────────────┴──────────┴────────────┴──────────┴─────────┴────────┘
```

---

## 7. Empty State

When no remittance data exists:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     🏛️                                      │
│                                                             │
│              No Remittance Data Yet                         │
│                                                             │
│   Run your first payroll to start tracking remittances.    │
│   Remittance amounts are calculated automatically based    │
│   on payroll deductions.                                    │
│                                                             │
│                   [Run Payroll →]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## TypeScript Types

```typescript
// payroll-frontend/src/lib/types/remittance.ts

import type { RemitterType } from './company';

export type RemittanceStatus = 'pending' | 'due_soon' | 'overdue' | 'paid' | 'paid_late';

export type PaymentMethod =
  | 'my_payment'
  | 'pre_authorized_debit'
  | 'online_banking'
  | 'wire_transfer'
  | 'cheque';

export interface RemittancePeriod {
  id: string;
  companyId: string;
  remitterType: RemitterType;

  // Period Information
  periodStart: string;    // ISO date
  periodEnd: string;      // ISO date
  periodLabel: string;    // e.g., "December 2025", "Q4 2025", "Dec 1-15"
  dueDate: string;        // ISO date

  // Amounts
  cppEmployee: number;
  cppEmployer: number;
  eiEmployee: number;
  eiEmployer: number;
  federalTax: number;
  provincialTax: number;
  totalAmount: number;

  // Payment Tracking
  status: RemittanceStatus;
  paidDate: string | null;
  paymentMethod: PaymentMethod | null;
  confirmationNumber: string | null;
  notes: string | null;

  // Penalty (if overdue)
  daysOverdue: number;
  penaltyRate: number;        // 0.03, 0.05, 0.07, 0.10
  penaltyAmount: number;

  // Linked Payroll Runs
  payrollRunIds: string[];

  // Metadata
  createdAt: string;
  updatedAt: string;
}

export interface RemittanceSummary {
  year: number;
  ytdRemitted: number;
  totalRemittances: number;
  completedRemittances: number;
  onTimeRate: number;         // 0.0 to 1.0
  pendingAmount: number;
  pendingCount: number;
}

// Payment method display info
export const PAYMENT_METHOD_INFO: Record<PaymentMethod, {
  label: string;
  description: string;
}> = {
  my_payment: {
    label: 'My Payment (CRA Online)',
    description: "Pay through CRA's online portal"
  },
  pre_authorized_debit: {
    label: 'Pre-Authorized Debit',
    description: 'Automatic bank withdrawal by CRA'
  },
  online_banking: {
    label: 'Online Banking',
    description: 'Pay as a bill through your bank'
  },
  wire_transfer: {
    label: 'Wire Transfer',
    description: 'Direct bank wire transfer'
  },
  cheque: {
    label: 'Cheque',
    description: 'Mail a cheque to CRA'
  }
};

// Penalty rates by days overdue
export function calculatePenaltyRate(daysOverdue: number): number {
  if (daysOverdue <= 0) return 0;
  if (daysOverdue <= 3) return 0.03;
  if (daysOverdue <= 5) return 0.05;
  if (daysOverdue <= 7) return 0.07;
  return 0.10;
}

// Status display info
export const REMITTANCE_STATUS_INFO: Record<RemittanceStatus, {
  label: string;
  icon: string;
  colorClass: string;
}> = {
  pending: {
    label: 'Pending',
    icon: '⏳',
    colorClass: 'bg-gray-100 text-gray-700'
  },
  due_soon: {
    label: 'Due Soon',
    icon: '⚠️',
    colorClass: 'bg-yellow-100 text-yellow-800'
  },
  overdue: {
    label: 'Overdue',
    icon: '🚨',
    colorClass: 'bg-red-100 text-red-800'
  },
  paid: {
    label: 'Paid',
    icon: '✅',
    colorClass: 'bg-green-100 text-green-800'
  },
  paid_late: {
    label: 'Paid Late',
    icon: '⚠️',
    colorClass: 'bg-orange-100 text-orange-800'
  }
};
```

---

## Component Files

### Current Implementation (Phase 0)

```
payroll-frontend/src/routes/(app)/remittance/
└── +page.svelte                    # Main page with inline components

payroll-frontend/src/lib/components/remittance/
└── MarkAsPaidModal.svelte          # ✅ Extracted - Payment recording modal
```

**Note**: In Phase 0, most UI elements are inline within the main page file for rapid prototyping. The `MarkAsPaidModal` has been extracted as a reusable component.

### Planned Refactoring (Post-API Integration)

When API integration is complete, consider extracting:

```
payroll-frontend/src/lib/components/remittance/
├── MarkAsPaidModal.svelte          # ✅ Already extracted
├── (future) UpcomingRemittanceCard.svelte   # Highlighted upcoming/overdue card
├── (future) RemittanceSummaryCards.svelte   # YTD stats row
├── (future) RemittanceHistoryTable.svelte   # History table with expansion
└── (future) index.ts                        # Component exports
```

---

## Page Flow

```
User opens /remittance
    │
    ├─► System loads remittance data for current year
    │
    ├─► Display Upcoming Remittance Card
    │   • Shows next due remittance
    │   • Highlights if due soon or overdue
    │
    ├─► Display Summary Cards
    │   • YTD totals and statistics
    │
    └─► Display History Table
        │
        ├─► User clicks "Mark as Paid"
        │   • Opens MarkAsPaidModal
        │   • Records payment details
        │   • Updates status to "Paid"
        │
        ├─► User clicks "Generate PD7A"
        │   • Downloads PD7A PDF
        │
        └─► User clicks row to expand
            • Shows detailed breakdown
```

---

## Accessibility

- Upcoming card uses appropriate `role="alert"` for overdue status
- Table uses proper `<table>` semantics with `<thead>` and `<tbody>`
- Status badges have `aria-label` for screen readers
- Modal follows focus trap patterns
- Color is not the only indicator (icons accompany colors)
- All interactive elements are keyboard accessible

---

## Responsive Design

### Desktop (≥1024px)
- Full table with all columns visible
- Side-by-side summary cards

### Tablet (768px - 1023px)
- Table scrolls horizontally
- Summary cards in 2x2 grid

### Mobile (<768px)
- Cards stack vertically
- Table converts to card list view
- Each remittance as a card

```
Mobile Card View:
┌─────────────────────────────┐
│ December 2025      ⏳Pending│
│ Due: Jan 15, 2026           │
│ Amount: $8,160.00           │
│                             │
│ [Generate PD7A] [Mark Paid] │
└─────────────────────────────┘
```

---

**Document Version**: 1.0
**Created**: 2025-12-08
